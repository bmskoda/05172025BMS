"""
Central manager that initialises and health-checks every configured API client.
"""

from __future__ import annotations

from typing import Dict, Optional

from aegis.api.base import APIClient
from aegis.api.clients import (
    AlchemyClient,
    BitqueryClient,
    BlockchairClient,
    ChainalysisClient,
    CNIPAClient,
    CoinMarketCapClient,
    CourtListenerClient,
    CovalentClient,
    CryptoCompareClient,
    DPMAClient,
    DuneClient,
    EllipticClient,
    EPOClient,
    EtherscanClient,
    EtherscanV2Client,
    EUIPOClient,
    InfuraClient,
    IPIndiaClient,
    IPOUKClient,
    JPOClient,
    KIPOClient,
    MoralisClient,
    NFTScanClient,
    OpenCorporatesClient,
    RDAPClient,
    TRMLabsClient,
    USPTOClient,
    USPTOFileWrapperClient,
    WaybackCDXClient,
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
        _r = self._clients.__setitem__

        # IP offices
        if _c.uspto_api_key:
            _r("uspto", USPTOClient(_c.uspto_api_key))
            _r("uspto_file_wrapper", USPTOFileWrapperClient(_c.uspto_api_key))
        if _c.epo_api_key:
            _r("epo", EPOClient(_c.epo_api_key))
        if _c.wipo_api_key:
            _r("wipo", WIPOClient(_c.wipo_api_key))
        if _c.cnipa_api_key:
            _r("cnipa", CNIPAClient(_c.cnipa_api_key))
        if _c.jpo_api_key:
            _r("jpo", JPOClient(_c.jpo_api_key))
        if _c.kipo_api_key:
            _r("kipo", KIPOClient(_c.kipo_api_key))
        if _c.euipo_api_key:
            _r("euipo", EUIPOClient(_c.euipo_api_key))
        if _c.ipouk_api_key:
            _r("ipouk", IPOUKClient(_c.ipouk_api_key))
        if _c.dpma_api_key:
            _r("dpma", DPMAClient(_c.dpma_api_key))
        if _c.ipindia_api_key:
            _r("ipindia", IPIndiaClient(_c.ipindia_api_key))

        # Blockchain analytics
        if _c.chainalysis_api_key:
            _r("chainalysis", ChainalysisClient(_c.chainalysis_api_key))
        if _c.elliptic_api_key:
            _r("elliptic", EllipticClient(_c.elliptic_api_key))
        if _c.trmlabs_api_key:
            _r("trmlabs", TRMLabsClient(_c.trmlabs_api_key))
        if _c.bitquery_api_key:
            _r("bitquery", BitqueryClient(_c.bitquery_api_key))
        if _c.etherscan_api_key:
            _r("etherscan", EtherscanClient(_c.etherscan_api_key))
            _r("etherscan_v2", EtherscanV2Client(_c.etherscan_api_key))
        if _c.alchemy_api_key:
            _r("alchemy", AlchemyClient(_c.alchemy_api_key))
        if _c.infura_api_key:
            _r("infura", InfuraClient(_c.infura_api_key))
        if _c.moralis_api_key:
            _r("moralis", MoralisClient(_c.moralis_api_key))
        if _c.dune_api_key:
            _r("dune", DuneClient(_c.dune_api_key))
        if _c.covalent_api_key:
            _r("covalent", CovalentClient(_c.covalent_api_key))
        if _c.blockchair_api_key:
            _r("blockchair", BlockchairClient(_c.blockchair_api_key))
        if _c.cryptocompare_api_key:
            _r("cryptocompare", CryptoCompareClient(_c.cryptocompare_api_key))
        if _c.coinmarketcap_api_key:
            _r("coinmarketcap", CoinMarketCapClient(_c.coinmarketcap_api_key))
        if _c.nftscan_api_key:
            _r("nftscan", NFTScanClient(_c.nftscan_api_key))

        # Public records
        if _c.opencorporates_api_key:
            _r("opencorporates", OpenCorporatesClient(_c.opencorporates_api_key))
        if _c.courtlistener_api_key:
            _r("courtlistener", CourtListenerClient(_c.courtlistener_api_key))

        # Always-available (no key required)
        _r("rdap", RDAPClient())
        _r("wayback_cdx", WaybackCDXClient())

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
