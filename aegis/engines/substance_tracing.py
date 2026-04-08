"""
Illicit substance / fentanyl-token tracing engine.

Identifies privacy-token contracts (e.g. TORN), traces token deployment
provenance, and detects drug-market interaction patterns via on-chain
transaction heuristics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from aegis.api.manager import APIIntegrationManager
from aegis.engines.known_addresses import KNOWN_MIXERS, OFAC_SANCTIONED
from aegis.utils import get_logger

PRIVACY_TOKEN_CONTRACTS: Dict[str, str] = {
    "0x77777feddddffc19ff86db637967013e6c6a116c": "TORN",
}

DARKNET_HEURISTIC_SIGS: Dict[str, str] = {
    "0xa9059cbb": "transfer",
    "0x095ea7b3": "approve",
}


class SubstanceTracer:
    """Traces blockchain tokens linked to illicit substance supply chains."""

    def __init__(self, api_mgr: APIIntegrationManager) -> None:
        self._api = api_mgr
        self._log = get_logger("SubstanceTracer")

    async def trace_token(self, contract: str, chain_id: int = 1) -> Dict[str, Any]:
        """Trace a token contract's deployment and transfer patterns."""
        known = PRIVACY_TOKEN_CONTRACTS.get(contract.lower())
        risk_indicators: List[str] = []
        if known:
            risk_indicators.append(f"privacy_token:{known}")

        cli = self._api.get_client("etherscan_v2")
        if not cli:
            cli = self._api.get_client("etherscan")
        deployer = "unknown"
        if cli:
            resp = await cli.get_transactions(contract, chain_id=chain_id) if hasattr(cli, "get_transactions") else None
            if resp and resp.success and isinstance(resp.data, dict):
                results = resp.data.get("result", [])
                if results:
                    deployer = results[-1].get("from", "unknown")
                    if deployer.lower() in OFAC_SANCTIONED.get("ethereum", set()):
                        risk_indicators.append("deployer_sanctioned")

        return {
            "contract_address": contract,
            "chain_id": chain_id,
            "deployer": deployer,
            "is_privacy_token": known is not None,
            "risk_indicators": risk_indicators,
        }

    async def detect_market_patterns(self, address: str, chain_id: int = 1) -> List[Dict[str, Any]]:
        """Detect drug-market interaction patterns for *address*."""
        patterns: List[Dict[str, Any]] = []
        cli = self._api.get_client("etherscan_v2") or self._api.get_client("etherscan")
        if not cli:
            return patterns

        resp = await cli.get_transactions(address) if hasattr(cli, "get_transactions") else None
        if not (resp and resp.success and isinstance(resp.data, dict)):
            return patterns

        mixers = KNOWN_MIXERS.get("ethereum", set())
        for tx in resp.data.get("result", [])[:200]:
            to = tx.get("to", "").lower()
            inp = tx.get("input", "")[:10].lower()
            if to in mixers:
                patterns.append({"tx_hash": tx.get("hash"), "pattern": "mixer_interaction", "address": to})
            if to in PRIVACY_TOKEN_CONTRACTS:
                patterns.append({"tx_hash": tx.get("hash"), "pattern": "privacy_token_interaction", "token": PRIVACY_TOKEN_CONTRACTS[to]})
            if inp in DARKNET_HEURISTIC_SIGS and float(tx.get("value", 0)) == 0:
                patterns.append({"tx_hash": tx.get("hash"), "pattern": "zero_value_token_transfer"})

        self._log.info("Detected %d market patterns for %s", len(patterns), address)
        return patterns
