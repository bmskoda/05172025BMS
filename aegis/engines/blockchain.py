"""
Blockchain forensics engine.

Recursive transaction tracing (unlimited depth, bidirectional, with token-
transfer following), mixer/tumbler detection, DeFi-protocol classification,
cross-chain bridge identification, MEV analysis, and inline OFAC/risk
scoring via the unified known-address databases.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

from aegis.api.manager import APIIntegrationManager
from aegis.config import UnifiedConfiguration
from aegis.constants import BlockchainLayer, PrivacyProtocol, RiskLevel, TransactionType
from aegis.engines.known_addresses import (
    BLOCKCHAIN_NETWORKS,
    BRIDGE_DESTINATION,
    KNOWN_BRIDGES,
    KNOWN_DEFI,
    KNOWN_MIXERS,
    METHOD_SIGNATURES,
    NFT_MARKETPLACES,
    OFAC_SANCTIONED,
)
from aegis.models.core import (
    BlockchainAddress,
    PrecisionDecimal,
    Timestamp,
    Transaction,
)
from aegis.utils import get_logger, validate_blockchain_address


# ---------------------------------------------------------------------------
# Transaction tracer (recursive, bidirectional, token-transfer following)
# ---------------------------------------------------------------------------


class TransactionTracer:
    """Recursively traces every transaction until the configured depth or
    transaction cap is reached.  Supports bidirectional tracing and follows
    ERC-20/721 token transfers to secondary addresses."""

    def __init__(self, api_mgr: APIIntegrationManager) -> None:
        self._api = api_mgr
        self._log = get_logger("Blockchain.Tracer")
        self._visited: Set[str] = set()
        self._visited_addrs: Set[str] = set()

    async def trace_address(
        self,
        address: str,
        network: str,
        max_depth: int = 10,
        max_txns: int = 10_000,
        direction: str = "both",
    ) -> List[Transaction]:
        self._visited.clear()
        self._visited_addrs.clear()
        txns: List[Transaction] = []
        await self._recurse(address, network, 0, max_depth, max_txns, txns, direction)
        self._log.info(
            "Traced %d transactions, %d unique addresses for %s (depth %d)",
            len(txns), len(self._visited_addrs), address, max_depth,
        )
        return txns

    async def _recurse(
        self, address: str, network: str, depth: int,
        max_depth: int, max_txns: int, acc: List[Transaction],
        direction: str,
    ) -> None:
        if depth >= max_depth or len(acc) >= max_txns:
            return
        addr_key = f"{network}:{address.lower()}"
        if addr_key in self._visited_addrs:
            return
        self._visited_addrs.add(addr_key)

        etherscan = self._api.get_client("etherscan")
        if not etherscan:
            return
        resp = await etherscan.get_transactions(address)
        if not resp.success or not resp.data:
            return

        for raw in resp.data.get("result", [])[:500]:
            tx = self._parse(raw, network, depth)
            if not tx or tx.tx_hash in self._visited:
                continue
            self._visited.add(tx.tx_hash)

            tx = self._enrich_inline(tx)
            acc.append(tx)
            if len(acc) >= max_txns:
                return

            outbound = tx.from_address.address.lower() == address.lower()
            inbound = tx.to_address and tx.to_address.address.lower() == address.lower()

            if direction in ("outgoing", "both") and outbound and tx.to_address:
                await self._recurse(tx.to_address.address, network, depth + 1, max_depth, max_txns, acc, direction)
            if direction in ("incoming", "both") and inbound:
                await self._recurse(tx.from_address.address, network, depth + 1, max_depth, max_txns, acc, direction)

            for tt in tx.token_transfers:
                for key in ("from", "to"):
                    peer = tt.get(key, "")
                    if peer and f"{network}:{peer.lower()}" not in self._visited_addrs:
                        await self._recurse(peer, network, depth + 1, max_depth, max_txns, acc, direction)

    @staticmethod
    def _parse(raw: Dict[str, Any], network: str, depth: int) -> Optional[Transaction]:
        try:
            gas_used = int(raw.get("gasUsed", 0))
            gas_price_wei = int(raw.get("gasPrice", 0))
            return Transaction(
                tx_hash=raw.get("hash", ""),
                network=network,
                block_number=int(raw.get("blockNumber", 0)),
                timestamp=Timestamp(int(raw.get("timeStamp", 0)) * 1_000_000_000),
                from_address=BlockchainAddress(address=raw.get("from", ""), network=network),
                to_address=(
                    BlockchainAddress(address=raw["to"], network=network)
                    if raw.get("to") else None
                ),
                value=PrecisionDecimal(Decimal(raw.get("value", "0")) / Decimal("1e18")),
                gas_price=PrecisionDecimal(Decimal(gas_price_wei) / Decimal("1e9")),
                gas_used=gas_used,
                fee=PrecisionDecimal(Decimal(gas_used * gas_price_wei) / Decimal("1e18")) if gas_used and gas_price_wei else None,
                nonce=int(raw.get("nonce", 0)),
                input_data=raw.get("input", ""),
                status="confirmed" if raw.get("txreceipt_status") == "1" else "pending",
                confirmations=int(raw.get("confirmations", 0)),
                trace_depth=depth,
                transaction_type=TransactionType.CONTRACT_CREATION if not raw.get("to") else TransactionType.STANDARD,
            )
        except Exception:
            return None

    @staticmethod
    def _enrich_inline(tx: Transaction) -> Transaction:
        """Attach OFAC/mixer/bridge/DeFi flags using known-address DBs."""
        net = tx.network.lower()
        to = tx.to_address.address.lower() if tx.to_address else ""
        frm = tx.from_address.address.lower()

        sanctioned = OFAC_SANCTIONED.get(net, set())
        is_sanctioned = frm in sanctioned or to in sanctioned

        mixers = KNOWN_MIXERS.get(net, set())
        is_mixer = to in mixers or frm in mixers
        priv = PrivacyProtocol.TORNADO_CASH if is_mixer else tx.privacy_protocol

        bridges_flat = set()
        bridge_info = tx.bridge_info
        for bname, baddr in KNOWN_BRIDGES.get(net, {}).items():
            if to == baddr:
                bridges_flat.add(to)
                bridge_info = {"bridge": bname, "destination": BRIDGE_DESTINATION.get(bname)}
        is_bridge = to in bridges_flat

        defi_addrs: Set[str] = set()
        defi_info = tx.defi_info
        for _proto, chains in KNOWN_DEFI.items():
            for addr in chains.get(net, {}).values():
                defi_addrs.add(addr)
        is_defi = to in defi_addrs
        if is_defi:
            for proto, chains in KNOWN_DEFI.items():
                if to in chains.get(net, {}).values():
                    defi_info = {"protocol": proto}
                    break

        method = None
        tx_type = tx.transaction_type
        if tx.input_data and len(tx.input_data) >= 10:
            method = METHOD_SIGNATURES.get(tx.input_data[:10].lower())
            if method and "swap" in method.lower():
                tx_type = TransactionType.DEFI_SWAP
            elif method and "flash" in method.lower():
                tx_type = TransactionType.FLASH_LOAN

        nft_addrs = set()
        for addrs in NFT_MARKETPLACES.get(net, {}).values():
            nft_addrs.add(addrs)
        is_nft = to in nft_addrs or tx.is_nft

        risk = 0.0
        if is_sanctioned:
            risk = 1.0
        elif is_mixer:
            risk = max(risk, 0.9)
        elif is_bridge:
            risk = max(risk, 0.5)

        level = RiskLevel.CRITICAL if risk >= 0.9 else RiskLevel.HIGH if risk >= 0.7 else RiskLevel.MEDIUM if risk >= 0.5 else tx.risk_level

        return Transaction(
            tx_hash=tx.tx_hash, network=tx.network, block_number=tx.block_number,
            timestamp=tx.timestamp, from_address=tx.from_address, to_address=tx.to_address,
            value=tx.value, gas_price=tx.gas_price, gas_used=tx.gas_used,
            nonce=tx.nonce, input_data=tx.input_data, transaction_type=tx_type,
            status=tx.status, confirmations=tx.confirmations, fee=tx.fee,
            token_transfers=tx.token_transfers, privacy_protocol=priv,
            risk_score=risk, risk_level=level, trace_depth=tx.trace_depth,
            parent_tx=tx.parent_tx, child_txs=tx.child_txs,
            is_sanctioned=is_sanctioned, is_mixer=is_mixer,
            is_bridge=is_bridge, is_defi=is_defi, is_nft=is_nft,
            bridge_info=bridge_info, mixer_info=tx.mixer_info,
            defi_info=defi_info, nft_metadata=tx.nft_metadata, metadata=tx.metadata,
        )


# ---------------------------------------------------------------------------
# Mixer / tumbler detector
# ---------------------------------------------------------------------------


class MixerDetector:
    """Identifies known mixer contracts and mixer-like behavioural patterns."""

    def __init__(self) -> None:
        self._log = get_logger("Blockchain.MixerDetector")

    def detect(self, transactions: List[Transaction]) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "mixer_detected": False, "confidence": 0.0,
            "mixer_type": None, "indicators": [], "related_addresses": set(),
        }
        for tx in transactions:
            for mixer in KNOWN_MIXERS.get(tx.network, set()):
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
        net = network.lower()
        if net in ("monero", "xmr"):
            return PrivacyProtocol.MONERO
        if net in ("zcash", "zec"):
            return PrivacyProtocol.ZCASH_SHIELDED
        if address.lower() in KNOWN_MIXERS.get(net, set()):
            return PrivacyProtocol.TORNADO_CASH
        return PrivacyProtocol.NONE


# ---------------------------------------------------------------------------
# DeFi protocol analyser
# ---------------------------------------------------------------------------


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
    "0x617ba037": "supply", "0xe8eda9df": "withdraw",
    "0xa415bcad": "borrow", "0x573ade81": "repay",
    "0xab9c4b5d": "flashLoanSimple",
}


class DeFiAnalyzer:
    def analyze(self, tx: Transaction) -> Dict[str, Any]:
        out: Dict[str, Any] = {"is_defi": False, "protocol": None, "action": None}
        if not tx.to_address:
            return out
        to = tx.to_address.address.lower()
        for proto, chains in KNOWN_DEFI.items():
            for net, addrs in chains.items():
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
        return METHOD_SIGNATURES.get(sig, "unknown")


# ---------------------------------------------------------------------------
# Cross-chain bridge detector
# ---------------------------------------------------------------------------


class BridgeDetector:
    def detect(self, tx: Transaction) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "is_bridge": False, "bridge_type": None,
            "source_chain": tx.network, "destination_chain": None, "confidence": 0.0,
        }
        if not tx.to_address:
            return out
        to = tx.to_address.address.lower()
        for bname, baddr in KNOWN_BRIDGES.get(tx.network, {}).items():
            if to == baddr:
                out.update(
                    is_bridge=True, bridge_type=bname, confidence=0.95,
                    destination_chain=BRIDGE_DESTINATION.get(bname),
                )
                break
        return out


# ---------------------------------------------------------------------------
# MEV analyser
# ---------------------------------------------------------------------------


class MEVAnalyzer:
    def detect_sandwich(self, block_txns: List[Transaction], target: Transaction) -> Dict[str, Any]:
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
# Composite blockchain forensics engine
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
        self, address: str, network: str, max_depth: int = 10,
        direction: str = "both",
    ) -> Dict[str, Any]:
        if not validate_blockchain_address(address, network):
            return {"error": "Invalid address format"}

        txns = await self.tracer.trace_address(address, network, max_depth, direction=direction)
        mixer_res = self.mixer.detect(txns)

        defi_hits = [self.defi.analyze(t) for t in txns[:200] if self.defi.analyze(t)["is_defi"]]
        bridge_hits = [self.bridge.detect(t) for t in txns[:200] if self.bridge.detect(t)["is_bridge"]]
        risk = await self._risk(address, network)

        sanctioned_count = sum(1 for t in txns if t.is_sanctioned)
        mixer_count = sum(1 for t in txns if t.is_mixer)
        bridge_count = sum(1 for t in txns if t.is_bridge)
        defi_count = sum(1 for t in txns if t.is_defi)

        return {
            "address": address, "network": network,
            "transaction_count": len(txns),
            "unique_addresses": len(self.tracer._visited_addrs),
            "total_value": str(sum(float(t.value.value) for t in txns)),
            "mixer_analysis": mixer_res,
            "defi_interactions": defi_hits,
            "bridge_transactions": bridge_hits,
            "risk_score": risk,
            "sanctioned_transactions": sanctioned_count,
            "mixer_transactions": mixer_count,
            "bridge_transaction_count": bridge_count,
            "defi_transaction_count": defi_count,
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
