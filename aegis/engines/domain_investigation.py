"""
Stolen / hijacked domain investigation engine.

Uses RDAP for live registration data and Wayback Machine CDX API
for historical ownership snapshots.  Computes estimated damages
from traffic and market-value heuristics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aegis.api.manager import APIIntegrationManager
from aegis.utils import get_logger


class DomainInvestigator:
    """Investigates domain registration, ownership history, and damages."""

    def __init__(self, api_mgr: APIIntegrationManager) -> None:
        self._api = api_mgr
        self._log = get_logger("Domain.Investigator")

    async def investigate(self, domain: str) -> Dict[str, Any]:
        """Full domain investigation: RDAP lookup + Wayback history."""
        rdap = await self._rdap_lookup(domain)
        history = await self._wayback_history(domain)
        return {
            "domain": domain,
            "rdap": rdap,
            "wayback_snapshots": len(history),
            "history": history[:20],
            "damages": self.estimate_damages(domain),
        }

    async def _rdap_lookup(self, domain: str) -> Dict[str, Any]:
        cli = self._api.get_client("rdap")
        if not cli:
            return {"error": "RDAP client not configured"}
        resp = await cli.lookup_domain(domain)
        if not resp.success:
            return {"error": resp.error}
        data = resp.data if isinstance(resp.data, dict) else {}
        nameservers = [ns.get("ldhName") for ns in data.get("nameservers", [])]
        entities = data.get("entities", [])
        return {
            "status": data.get("status", []),
            "nameservers": nameservers,
            "entities_count": len(entities),
            "events": data.get("events", []),
        }

    async def _wayback_history(self, domain: str) -> List[Dict[str, Any]]:
        cli = self._api.get_client("wayback_cdx")
        if not cli:
            return []
        resp = await cli.search(domain, limit=100)
        if not resp.success or not isinstance(resp.data, list):
            return []
        rows = resp.data[1:] if resp.data else []
        return [{"timestamp": r[0], "url": r[1], "status": r[2]} for r in rows if len(r) >= 3]

    @staticmethod
    def estimate_damages(
        domain: str,
        market_value: float = 5_000.0,
        monthly_traffic: int = 10_000,
        revenue_per_visit: float = 0.10,
        years_stolen: int = 3,
    ) -> Dict[str, Any]:
        annual_revenue = monthly_traffic * revenue_per_visit * 12
        total = market_value + annual_revenue + (annual_revenue * years_stolen)
        return {
            "domain": domain,
            "market_value_usd": market_value,
            "annual_revenue_loss_usd": annual_revenue,
            "years_assumed": years_stolen,
            "total_estimated_damages_usd": total,
        }
