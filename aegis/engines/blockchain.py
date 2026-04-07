"""
Blockchain forensics engine.

Recursive transaction tracing, mixer/tumbler detection, DeFi-protocol
classification, cross-chain bridge identification, and MEV analysis.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

from aegis.api.manager import APIIntegrationManager
from aegis.config import UnifiedConfiguration
from aegis.constants import BlockchainLayer, PrivacyProtocol, TransactionType
from aegis.models.core import (
    APIResponse,
    BlockchainAddress,
    PrecisionDecimal,
    Timestamp,
    Transaction,
)
from aegis.utils import get_logger, validate_blockchain_address


# ---------------------------------------------------------------------------
# Supported networks registry
# ---------------------------------------------------------------------------

BLOCKCHAIN_NETWORKS = {
    "ethereum": {"chain_id": 1, "layer": BlockchainLayer.L1, "native": "ETH", "block_time": 12},
    "bitcoin": {"chain_id": 0, "layer": BlockchainLayer.L1, "native": "BTC", "block_time": 600},
    "solana": {"chain_id": 0, "layer": BlockchainLayer.L1, "native": "SOL", "block_time": 0.4},
    "polygon": {"chain_id": 137, "layer": BlockchainLayer.L2, "native": "MATIC", "block_time": 2},
    "arbitrum": {"chain_id": 42161, "layer": BlockchainLayer.L2, "native": "ETH", "block_time": 0.25},
    "optimism": {"chain_id": 10, "layer": BlockchainLayer.L2, "native": "ETH", "block_time": 2},
    "base": {"chain_id": 8453, "layer": BlockchainLayer.L2, "native": "ETH", "block_time": 2},
    "avalanche": {"chain_id": 43114, "layer": BlockchainLayer.L1, "native": "AVAX", "block_time": 2},
    "binance": {"chain_id": 56, "layer": BlockchainLayer.L1, "native": "BNB", "block_time": 3},
    "monero": {"chain_id": 0, "layer": BlockchainLayer.L1, "native": "XMR", "block_time": 120, "privacy": True},
    "zcash": {"chain_id": 0, "layer": BlockchainLayer.L1, "native": "ZEC", "block_time": 75, "privacy": True},
}


# ---------------------------------------------------------------------------
# Transaction tracer (recursive, depth-unlimited)
# ---------------------------------------------------------------------------


class TransactionTracer:
    """Recursively traces every outbound transaction until the configured
    depth or transaction cap is reached."""

    def __init__(self, api_mgr: APIIntegrationManager) -> None:
        self._api = api_mgr
        self._log = get_logger("Blockchain.Tracer")
        self._visited: Set[str] = set()

    async def trace_address(
        self,
        address: str,
        network: str,
        max_depth: int = 10,
        max_txns: int = 10_000,
    ) -> List[Transaction]:
        self._visited.clear()
        txns: List[Transaction] = []
        await self._recurse(address, network, 0, max_depth, max_txns, txns)
        self._log.info("Traced %d transactions for %s", len(txns), address)
        return txns

    async def _recurse(
        self,
        address: str,
        network: str,
        depth: int,
        max_depth: int,
        max_txns: int,
        acc: List[Transaction],
    ) -> None:
        if depth >= max_depth or len(acc) >= max_txns:
            return
        key = f"{network}:{address}"
        if key in self._visited:
            return
        self._visited.add(key)

        etherscan = self._api.get_client("etherscan")
        if not etherscan:
            return
        resp = await etherscan.get_transactions(address)
        if not resp.success or not resp.data:
            return
        for raw in resp.data.get("result", [])[:200]:
            tx = self._parse(raw, network)
            if tx:
                acc.append(tx)
                if tx.to_address and len(acc) < max_txns:
                    await self._recurse(
                        tx.to_address.address, network, depth + 1, max_depth, max_txns, acc
                    )

    @staticmethod
    def _parse(raw: Dict[str, Any], network: str) -> Optional[Transaction]:
        try:
            return Transaction(
                tx_hash=raw.get("hash", ""),
                network=network,
                block_number=int(raw.get("blockNumber", 0)),
                timestamp=Timestamp(int(raw.get("timeStamp", 0)) * 1_000_000_000),
                from_address=BlockchainAddress(address=raw.get("from", ""), network=network),
                to_address=(
                    BlockchainAddress(address=raw["to"], network=network)
                    if raw.get("to")
                    else None
                ),
                value=PrecisionDecimal(Decimal(raw.get("value", "0")) / Decimal("1e18")),
                gas_price=PrecisionDecimal(Decimal(raw.get("gasPrice", "0")) / Decimal("1e9")),
                gas_used=int(raw.get("gasUsed", 0)),
                nonce=int(raw.get("nonce", 0)),
                input_data=raw.get("input", ""),
                status="confirmed" if raw.get("txreceipt_status") == "1" else "pending",
            )
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Mixer / tumbler detector
# ---------------------------------------------------------------------------

_KNOWN_MIXERS: Dict[str, List[str]] = {
    "ethereum": [
        "0x722122df12d4e14e13ac3b6895a86e84145b6967",
        "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",
        "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",
        "0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3",
    ],
}


class MixerDetector:
    """Identifies known mixer contracts and mixer-like behavioural patterns."""

    def __init__(self) -> None:
        self._log = get_logger("Blockchain.MixerDetector")

    def detect(self, transactions: List[Transaction]) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "mixer_detected": False,
            "confidence": 0.0,
            "mixer_type": None,
            "indicators": [],
            "related_addresses": set(),
        }
        for tx in transactions:
            for mixer in _KNOWN_MIXERS.get(tx.network, []):
                if (tx.to_address and tx.to_address.address.lower() == mixer) or tx.from_address.address.lower() == mixer:
                    result["mixer_detected"] = True
                    result["confidence"] = max(result["confidence"], 0.95)
                    result["mixer_type"] = "known_mixer"
                    result["indicators"].append(f"Known mixer: {mixer}")
                    result["related_addresses"].add(tx.from_address.address)
                    if tx.to_address:
                        result["related_addresses"].add(tx.to_address.address)
            if self._behavioural_match(tx):
                result["mixer_detected"] = True
                result["confidence"] = max(result["confidence"], 0.70)
                result["indicators"].append("Behavioural mixer pattern")
        result["related_addresses"] = list(result["related_addresses"])
        return result

    @staticmethod
    def _behavioural_match(tx: Transaction) -> bool:
        v = float(tx.value.value)
        return v > 0 and v in (0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 100.0)

    @staticmethod
    def privacy_protocol(address: str, network: str) -> PrivacyProtocol:
        if network.lower() in ("monero", "xmr"):
            return PrivacyProtocol.MONERO
        if network.lower() in ("zcash", "zec"):
            return PrivacyProtocol.ZCASH_SHIELDED
        tc = [
            "0x722122df12d4e14e13ac3b6895a86e84145b6967",
            "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",
        ]
        if address.lower() in tc:
            return PrivacyProtocol.TORNADO_CASH
        return PrivacyProtocol.NONE


# ---------------------------------------------------------------------------
# DeFi protocol analyser
# ---------------------------------------------------------------------------

_DEFI_ROUTERS: Dict[str, Dict[str, str]] = {
    "uniswap_v2": {"router": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"},
    "uniswap_v3": {"router": "0xe592427a0aece92de3edee1f18e0157c05861564"},
    "aave_v3": {"pool": "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"},
    "compound_v2": {"comptroller": "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b"},
}

_UNISWAP_SIGS: Dict[str, str] = {
    "0x38ed1739": "swapExactTokensForTokens",
    "0x8803dbee": "swapTokensForExactTokens",
    "0x7ff36ab5": "swapExactETHForTokens",
    "0x18cbafe5": "swapExactTokensForETH",
    "0x04e45aaf": "exactInputSingle",
    "0xb858183f": "exactOutputSingle",
    "0x5ae401dc": "multicall",
}

_AAVE_SIGS: Dict[str, str] = {
    "0x617ba037": "supply",
    "0xe8eda9df": "withdraw",
    "0xa415bcad": "borrow",
    "0x573ade81": "repay",
    "0xab9c4b5d": "flashLoanSimple",
}


class DeFiAnalyzer:
    def analyze(self, tx: Transaction) -> Dict[str, Any]:
        out: Dict[str, Any] = {"is_defi": False, "protocol": None, "action": None}
        if not tx.to_address:
            return out
        to = tx.to_address.address.lower()
        for proto, addrs in _DEFI_ROUTERS.items():
            for _, addr in addrs.items():
                if to == addr:
                    out["is_defi"] = True
                    out["protocol"] = proto
                    out["action"] = self._decode(tx.input_data, proto)
                    return out
        return out

    @staticmethod
    def _decode(data: str, proto: str) -> str:
        if len(data) < 10:
            return "unknown"
        sig = data[:10].lower()
        if "uniswap" in proto:
            return _UNISWAP_SIGS.get(sig, "unknown")
        if "aave" in proto:
            return _AAVE_SIGS.get(sig, "unknown")
        return "unknown"


# ---------------------------------------------------------------------------
# Cross-chain bridge detector
# ---------------------------------------------------------------------------

_BRIDGES: Dict[str, Dict[str, str]] = {
    "ethereum": {
        "polygon_bridge": "0xa0c68c638235ee32657e8f720a23cec1bfc77c77",
        "arbitrum_bridge": "0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a",
        "optimism_bridge": "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1",
        "base_bridge": "0x49048044d57e1c92a77f79988d21fa8faf74e97e",
        "zksync_bridge": "0x32400084c286cf3e17e7b677ea9583e60a000324",
        "wormhole": "0x3ee18b2214aff97000d974cf647e7c347e8fa585",
        "layerzero": "0x66a71dcef29a0ffbdbe3c6a460a3b5bc225cd675",
    },
}

_BRIDGE_DEST: Dict[str, str] = {
    "polygon_bridge": "polygon",
    "arbitrum_bridge": "arbitrum",
    "optimism_bridge": "optimism",
    "base_bridge": "base",
    "zksync_bridge": "zksync",
}


class BridgeDetector:
    def detect(self, tx: Transaction) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "is_bridge": False, "bridge_type": None,
            "source_chain": tx.network, "destination_chain": None, "confidence": 0.0,
        }
        if not tx.to_address:
            return out
        to = tx.to_address.address.lower()
        for bname, baddr in _BRIDGES.get(tx.network, {}).items():
            if to == baddr:
                out.update(
                    is_bridge=True,
                    bridge_type=bname,
                    confidence=0.95,
                    destination_chain=_BRIDGE_DEST.get(bname),
                )
                break
        return out


# ---------------------------------------------------------------------------
# MEV analyser (sandwich-attack detector)
# ---------------------------------------------------------------------------


class MEVAnalyzer:
    def detect_sandwich(
        self, block_txns: List[Transaction], target: Transaction
    ) -> Dict[str, Any]:
        ordered = sorted(block_txns, key=lambda t: t.nonce or 0)
        idx = next((i for i, t in enumerate(ordered) if t.tx_hash == target.tx_hash), None)
        if idx is None or idx == 0 or idx >= len(ordered) - 1:
            return {"sandwich_detected": False}
        prev, nxt = ordered[idx - 1], ordered[idx + 1]
        detected = (
            prev.from_address.address == nxt.from_address.address
            and prev.from_address.address != target.from_address.address
        )
        return {
            "sandwich_detected": detected,
            "attacker": prev.from_address.address if detected else None,
            "victim": target.from_address.address if detected else None,
            "confidence": 0.8 if detected else 0.0,
        }


# ---------------------------------------------------------------------------
# Composite engine
# ---------------------------------------------------------------------------


class BlockchainForensicsEngine:
    """Coordinates all blockchain-level analysis for a given address."""

    def __init__(self, api_mgr: APIIntegrationManager, config: UnifiedConfiguration) -> None:
        self._api = api_mgr
        self._cfg = config
        self.tracer = TransactionTracer(api_mgr)
        self.mixer = MixerDetector()
        self.defi = DeFiAnalyzer()
        self.bridge = BridgeDetector()
        self.mev = MEVAnalyzer()
        self._log = get_logger("Blockchain.Engine")

    async def analyze_address(
        self, address: str, network: str, max_depth: int = 10
    ) -> Dict[str, Any]:
        if not validate_blockchain_address(address, network):
            return {"error": "Invalid address format"}

        txns = await self.tracer.trace_address(address, network, max_depth)
        mixer_res = self.mixer.detect(txns)

        defi_hits = [self.defi.analyze(t) for t in txns[:200] if self.defi.analyze(t)["is_defi"]]
        bridge_hits = [self.bridge.detect(t) for t in txns[:200] if self.bridge.detect(t)["is_bridge"]]
        risk = await self._risk(address, network)

        return {
            "address": address,
            "network": network,
            "transaction_count": len(txns),
            "total_value": str(sum(float(t.value.value) for t in txns)),
            "mixer_analysis": mixer_res,
            "defi_interactions": defi_hits,
            "bridge_transactions": bridge_hits,
            "risk_score": risk,
            "transactions": [t.to_dict() for t in txns[:50]],
        }

    async def _risk(self, addr: str, net: str) -> float:
        for name in ("chainalysis", "elliptic"):
            cli = self._api.get_client(name)
            if not cli:
                continue
            if name == "chainalysis":
                r = await cli.get_address_risk(addr, net)
            else:
                r = await cli.get_address_analysis(addr)
            if r.success and isinstance(r.data, dict):
                return r.data.get("risk", r.data.get("risk_score", 0.0))
        return 0.0
