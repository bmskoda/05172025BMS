"""
Central manager that initialises and health-checks every configured API client.
"""

from __future__ import annotations

from typing import Dict, Optional

from aegis.api.base import APIClient
from aegis.api.clients import (
    BitqueryClient,
    ChainalysisClient,
    CourtListenerClient,
    EllipticClient,
    EPOClient,
    EtherscanClient,
    NFTScanClient,
    OpenCorporatesClient,
    USPTOClient,
    WIPOClient,
)
from aegis.config import UnifiedConfiguration
from aegis.constants import APIStatus
from aegis.utils import get_logger


class APIIntegrationManager:
    """Unified gateway to all external APIs."""

    def __init__(self, config: UnifiedConfiguration) -> None:
        self.config = config
        self._clients: Dict[str, APIClient] = {}
        self._health: Dict[str, APIStatus] = {}
        self._logger = get_logger("API.Manager")

    async def initialize(self) -> None:
        _c = self.config
        _register = self._clients.__setitem__

        if _c.uspto_api_key:
            _register("uspto", USPTOClient(_c.uspto_api_key))
        if _c.epo_api_key:
            _register("epo", EPOClient(_c.epo_api_key))
        if _c.wipo_api_key:
            _register("wipo", WIPOClient(_c.wipo_api_key))
        if _c.chainalysis_api_key:
            _register("chainalysis", ChainalysisClient(_c.chainalysis_api_key))
        if _c.elliptic_api_key:
            _register("elliptic", EllipticClient(_c.elliptic_api_key))
        if _c.bitquery_api_key:
            _register("bitquery", BitqueryClient(_c.bitquery_api_key))
        if _c.etherscan_api_key:
            _register("etherscan", EtherscanClient(_c.etherscan_api_key))
        if _c.nftscan_api_key:
            _register("nftscan", NFTScanClient(_c.nftscan_api_key))
        if _c.opencorporates_api_key:
            _register("opencorporates", OpenCorporatesClient(_c.opencorporates_api_key))
        if _c.courtlistener_api_key:
            _register("courtlistener", CourtListenerClient(_c.courtlistener_api_key))

        self._logger.info("Initialized %d API clients", len(self._clients))

    def get_client(self, name: str) -> Optional[APIClient]:
        return self._clients.get(name)

    async def health_check_all(self) -> Dict[str, APIStatus]:
        self._health = {}
        for name, client in self._clients.items():
            try:
                self._health[name] = await client.health_check()
            except Exception as exc:
                self._logger.error("Health-check %s failed: %s", name, exc)
                self._health[name] = APIStatus.UNAVAILABLE
        return self._health

    async def close_all(self) -> None:
        for c in self._clients.values():
            await c.close()
        self._logger.info("All API clients closed")
