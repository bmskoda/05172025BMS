"""
NFT tracking engine — provenance, fractionalization detection,
wash-trading scoring, and marketplace attribution.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional

from aegis.api.manager import APIIntegrationManager
from aegis.engines.known_addresses import FRACTIONALIZATION_PROTOCOLS, NFT_MARKETPLACES
from aegis.utils import get_logger

try:
    from cachetools import TTLCache
    _CACHE_CLS = TTLCache
except ImportError:
    _CACHE_CLS = dict  # type: ignore[assignment,misc]


class NFTTracker:
    """Full-lifecycle NFT analysis: provenance, wash-trading, fractionalization."""

    def __init__(self, api_mgr: APIIntegrationManager) -> None:
        self._api = api_mgr
        self._log = get_logger("NFT.Tracker")
        self._cache: Dict[str, Any] = (
            _CACHE_CLS(maxsize=100_000, ttl=3600)
            if _CACHE_CLS is not dict
            else {}
        )

    async def track(
        self, contract: str, token_id: str, network: str = "ethereum"
    ) -> Dict[str, Any]:
        cache_key = f"{network}:{contract}:{token_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        transfers = await self._fetch_transfers(contract, token_id, network)
        frac = self._check_fractionalization(contract, network)
        wash = self._wash_trading_score(transfers)
        trading = self._trading_analysis(transfers)
        risk = self._risk_score(transfers, wash)

        result = {
            "contract": contract,
            "token_id": token_id,
            "network": network,
            "transfer_count": len(transfers),
            "transfers": transfers[:50],
            "trading_analysis": trading,
            "wash_trading_score": wash,
            "is_fractionalized": frac is not None,
            "fractionalization": frac,
            "risk_score": risk,
        }
        self._cache[cache_key] = result
        return result

    async def _fetch_transfers(
        self, contract: str, token_id: str, network: str
    ) -> List[Dict[str, Any]]:
        nftscan = self._api.get_client("nftscan")
        if nftscan:
            resp = await nftscan.get_nft_transactions(contract, token_id)
            if resp.success and isinstance(resp.data, list):
                return resp.data

        etherscan = self._api.get_client("etherscan")
        if not etherscan:
            return []
        resp = await etherscan.get_nft_transfers(contract)
        if not (resp.success and isinstance(resp.data, dict)):
            return []
        return [
            t for t in resp.data.get("result", [])
            if str(t.get("tokenID")) == str(token_id)
        ][:500]

    @staticmethod
    def _check_fractionalization(
        contract: str, network: str
    ) -> Optional[Dict[str, Any]]:
        protos = FRACTIONALIZATION_PROTOCOLS.get(network, {})
        c = contract.lower()
        for name, addr in protos.items():
            if c == addr:
                return {"protocol": name, "contract": addr}
        return None

    @staticmethod
    def _wash_trading_score(transfers: List[Dict[str, Any]]) -> float:
        if len(transfers) < 2:
            return 0.0
        pairs: Dict[tuple, int] = defaultdict(int)
        for t in transfers:
            pair = tuple(sorted([
                t.get("from", "").lower(),
                t.get("to", "").lower(),
            ]))
            pairs[pair] += 1
        mx = max(pairs.values()) if pairs else 0
        return min(1.0, mx / 10.0) if mx >= 3 else 0.0

    @staticmethod
    def _trading_analysis(transfers: List[Dict[str, Any]]) -> Dict[str, Any]:
        prices = []
        for t in transfers:
            p = t.get("price") or t.get("value")
            if p:
                try:
                    prices.append(float(p))
                except (ValueError, TypeError):
                    pass
        if not prices:
            return {"num_sales": 0}
        return {
            "num_sales": len(prices),
            "avg_price": sum(prices) / len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "total_volume": sum(prices),
        }

    @staticmethod
    def _risk_score(transfers: List[Dict[str, Any]], wash: float) -> float:
        risk = wash * 0.5
        if len(transfers) > 10:
            risk += 0.2
        return min(1.0, risk)
