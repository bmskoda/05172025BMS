"""
Composite risk-scoring engine for blockchain transactions and addresses.

Scoring dimensions:
  - OFAC SDN sanctioned-address match
  - Known mixer / tumbler interaction
  - Cross-chain bridge interaction
  - DeFi protocol interaction
  - Transaction amount heuristics
  - Privacy-protocol indicators
  - Method-signature classification
  - Chainalysis / Elliptic API enrichment (when configured)
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

from aegis.api.manager import APIIntegrationManager
from aegis.constants import PrivacyProtocol, RiskLevel
from aegis.engines.known_addresses import (
    BRIDGE_DESTINATION,
    KNOWN_BRIDGES,
    KNOWN_DEFI,
    KNOWN_MIXERS,
    METHOD_SIGNATURES,
    OFAC_SANCTIONED,
)
from aegis.models.core import Transaction
from aegis.utils import get_logger


def _flat_defi_addrs(network: str) -> Set[str]:
    out: Set[str] = set()
    for _proto, chains in KNOWN_DEFI.items():
        for addr in chains.get(network, {}).values():
            out.add(addr.lower() if isinstance(addr, str) else addr)
    return out


def _flat_bridge_addrs(network: str) -> Set[str]:
    return {a for a in KNOWN_BRIDGES.get(network, {}).values()}


class RiskScorer:
    """Calculates composite risk scores for transactions and addresses."""

    def __init__(self, api_mgr: Optional[APIIntegrationManager] = None) -> None:
        self._api = api_mgr
        self._log = get_logger("RiskScorer")

    def score_transaction(self, tx: Transaction) -> Dict[str, Any]:
        score = 0.0
        factors: List[str] = []
        net = tx.network.lower()
        to = tx.to_address.address.lower() if tx.to_address else ""
        frm = tx.from_address.address.lower()

        # OFAC
        sanctioned = OFAC_SANCTIONED.get(net, set())
        if frm in sanctioned or to in sanctioned:
            score = 1.0
            factors.append("ofac_sanctioned")

        # Mixers
        mixers = KNOWN_MIXERS.get(net, set())
        if to in mixers or frm in mixers:
            score = max(score, 0.9)
            factors.append("known_mixer")

        # Bridges
        if to in _flat_bridge_addrs(net):
            score = max(score, 0.5)
            factors.append("bridge_interaction")

        # DeFi
        is_defi = to in _flat_defi_addrs(net)
        if is_defi:
            factors.append("defi_interaction")

        # Privacy-protocol signals
        privacy = tx.privacy_protocol
        if privacy != PrivacyProtocol.NONE:
            score = max(score, 0.6)
            factors.append(f"privacy:{privacy.name}")

        # Amount heuristics
        val = float(tx.value.value) if tx.value else 0.0
        if val > 1_000_000:
            score += 0.2
            factors.append("very_large_amount")
        elif val > 100_000:
            score += 0.1
            factors.append("large_amount")
        elif val > 10_000:
            score += 0.05
            factors.append("significant_amount")

        # Round-number indicator (common in mixer deposits)
        if val > 0 and val == int(val) and val in (0.1, 1, 10, 100, 1000, 10000):
            score += 0.05
            factors.append("round_amount")

        # Method-sig classification
        method = None
        if tx.input_data and len(tx.input_data) >= 10:
            method = METHOD_SIGNATURES.get(tx.input_data[:10].lower())
            if method:
                factors.append(f"method:{method}")
                if "flash" in method.lower():
                    score += 0.15
                    factors.append("flash_loan_risk")

        score = min(score, 1.0)
        level = self._level(score)
        return {
            "risk_score": score, "risk_level": level, "factors": factors,
            "is_sanctioned": "ofac_sanctioned" in factors,
            "is_mixer": "known_mixer" in factors,
            "is_bridge": "bridge_interaction" in factors,
            "is_defi": is_defi, "method": method,
        }

    async def score_address(self, address: str, network: str) -> Dict[str, Any]:
        score = 0.0
        factors: List[str] = []
        entity_info: Dict[str, Any] = {}
        addr = address.lower()

        if addr in OFAC_SANCTIONED.get(network, set()):
            score = 1.0
            factors.append("ofac_sanctioned")
        if addr in KNOWN_MIXERS.get(network, set()):
            score = max(score, 1.0)
            factors.append("known_mixer")
        if addr in _flat_bridge_addrs(network):
            score = max(score, 0.5)
            factors.append("known_bridge")
        if addr in _flat_defi_addrs(network):
            factors.append("known_defi_protocol")

        if self._api:
            for name in ("chainalysis", "elliptic"):
                cli = self._api.get_client(name)
                if not cli:
                    continue
                try:
                    if name == "chainalysis":
                        r = await cli.get_address_risk(addr, network)
                    else:
                        r = await cli.get_address_analysis(addr)
                    if r.success and isinstance(r.data, dict):
                        ext = r.data.get("risk_score", r.data.get("risk", 0.0))
                        score = max(score, ext)
                        entity_info[name] = r.data
                except Exception as exc:
                    self._log.warning("%s error: %s", name, exc)

        return {
            "risk_score": min(score, 1.0), "risk_level": self._level(score),
            "factors": factors, "entity_info": entity_info,
        }

    @staticmethod
    def _level(score: float) -> RiskLevel:
        if score >= 0.9:
            return RiskLevel.CRITICAL
        if score >= 0.7:
            return RiskLevel.HIGH
        if score >= 0.5:
            return RiskLevel.MEDIUM
        if score >= 0.3:
            return RiskLevel.LOW
        return RiskLevel.MINIMAL
