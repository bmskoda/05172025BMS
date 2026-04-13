"""
Concrete API client implementations for patent offices,
blockchain analytics services, and public-records databases.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from aegis.api.base import APIClient
from aegis.constants import API_ENDPOINTS, APIStatus, HTTPMethod, RATE_LIMITS
from aegis.models.core import APIResponse


# ===================================================================
# Intellectual-property office clients
# ===================================================================


class USPTOClient(APIClient):
    def __init__(self, api_key: str = "") -> None:
        super().__init__("USPTO", API_ENDPOINTS["uspto"], api_key, RATE_LIMITS["uspto"])

    async def search_patents(self, query: str, limit: int = 100) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "/patents/search", params={"q": query, "limit": limit}
        )

    async def get_patent(self, patent_id: str) -> APIResponse:
        return await self._make_request(HTTPMethod.GET, f"/patents/{patent_id}")

    async def get_assignments(self, patent_id: str) -> APIResponse:
        return await self._make_request(HTTPMethod.GET, f"/patents/{patent_id}/assignments")

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/health")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class EPOClient(APIClient):
    def __init__(self, api_key: str = "") -> None:
        super().__init__("EPO", API_ENDPOINTS["epo"], api_key, RATE_LIMITS["epo"])

    async def search_patents(self, query: str, limit: int = 100) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET,
            "/rest-services/published-data/search",
            params={"q": query, "Range": f"1-{limit}"},
        )

    async def get_patent_family(self, pub_number: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET,
            f"/rest-services/family/publication/epodoc/{pub_number}",
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(
            HTTPMethod.GET,
            "/rest-services/published-data/search",
            params={"q": "test", "Range": "1-1"},
        )
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class WIPOClient(APIClient):
    def __init__(self, api_key: str = "") -> None:
        super().__init__("WIPO", API_ENDPOINTS["wipo"], api_key, RATE_LIMITS["wipo"])

    async def search_patents(self, query: str, limit: int = 100) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "/patents/search", params={"q": query, "rows": limit}
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(
            HTTPMethod.GET, "/patents/search", params={"q": "test", "rows": 1}
        )
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


# ===================================================================
# Blockchain analytics clients
# ===================================================================


class ChainalysisClient(APIClient):
    def __init__(self, api_key: str = "") -> None:
        super().__init__("Chainalysis", API_ENDPOINTS["chainalysis"], api_key, RATE_LIMITS["chainalysis"])

    async def get_address_risk(self, address: str, network: str = "bitcoin") -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, f"/v1/risk/{network}/address/{address}"
        )

    async def get_transaction_risk(self, tx_hash: str, network: str = "bitcoin") -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, f"/v1/risk/{network}/transaction/{tx_hash}"
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/v1/health")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class EllipticClient(APIClient):
    def __init__(self, api_key: str = "") -> None:
        super().__init__("Elliptic", API_ENDPOINTS["elliptic"], api_key, RATE_LIMITS["elliptic"])

    async def get_address_analysis(self, address: str) -> APIResponse:
        return await self._make_request(HTTPMethod.GET, f"/v2/address/{address}")

    async def get_wallet_analysis(self, wallet_id: str) -> APIResponse:
        return await self._make_request(HTTPMethod.GET, f"/v2/wallet/{wallet_id}")

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/v2/health")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class BitqueryClient(APIClient):
    def __init__(self, api_key: str = "") -> None:
        super().__init__("Bitquery", API_ENDPOINTS["bitquery"], api_key, RATE_LIMITS["bitquery"])

    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> APIResponse:
        return await self._make_request(
            HTTPMethod.POST, "", data={"query": query, "variables": variables or {}}
        )

    async def get_address_transactions(
        self, address: str, network: str = "ethereum", limit: int = 100
    ) -> APIResponse:
        gql = """
        query($addr: String!, $net: EthereumNetwork!, $lim: Int!) {
          ethereum(network: $net) {
            transactions(txSender: {is: $addr}, options: {limit: $lim, desc: "block.timestamp.time"}) {
              hash block { timestamp { time } height } value gas_value
            }
          }
        }
        """
        return await self.execute_query(gql, {"addr": address, "net": network.upper(), "lim": limit})

    async def health_check(self) -> APIStatus:
        r = await self.execute_query("{ ethereum { blocks(options:{limit:1}) { height } } }")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class EtherscanClient(APIClient):
    def __init__(self, api_key: str = "") -> None:
        super().__init__("Etherscan", API_ENDPOINTS["etherscan"], api_key, RATE_LIMITS["etherscan"])

    async def get_balance(self, address: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET,
            "",
            params={
                "module": "account", "action": "balance",
                "address": address, "tag": "latest", "apikey": self.api_key,
            },
        )

    async def get_transactions(
        self, address: str, start_block: int = 0, end_block: int = 99_999_999
    ) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET,
            "",
            params={
                "module": "account", "action": "txlist",
                "address": address, "startblock": start_block,
                "endblock": end_block, "sort": "desc", "apikey": self.api_key,
            },
        )

    async def get_token_transfers(self, address: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET,
            "",
            params={
                "module": "account", "action": "tokentx",
                "address": address, "sort": "desc", "apikey": self.api_key,
            },
        )

    async def get_nft_transfers(self, address: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET,
            "",
            params={
                "module": "account", "action": "tokennfttx",
                "address": address, "sort": "desc", "apikey": self.api_key,
            },
        )

    async def get_contract_abi(self, address: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET,
            "",
            params={
                "module": "contract", "action": "getabi",
                "address": address, "apikey": self.api_key,
            },
        )

    async def get_internal_transactions(self, address: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET,
            "",
            params={
                "module": "account", "action": "txlistinternal",
                "address": address, "sort": "desc", "apikey": self.api_key,
            },
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(
            HTTPMethod.GET,
            "",
            params={"module": "stats", "action": "ethprice", "apikey": self.api_key},
        )
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class NFTScanClient(APIClient):
    """NFTScan REST API v2 — tracks NFT mints, transfers, and metadata."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("NFTScan", "https://restapi.nftscan.com/api/v2", api_key, 500)

    async def get_nfts_by_account(self, address: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, f"/account/own/all/{address}",
            headers={"X-API-KEY": self.api_key},
        )

    async def get_nft_transactions(self, contract: str, token_id: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, f"/transactions/{contract}/{token_id}",
            headers={"X-API-KEY": self.api_key},
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/health")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


# ===================================================================
# Public-records clients
# ===================================================================


class OpenCorporatesClient(APIClient):
    def __init__(self, api_key: str = "") -> None:
        super().__init__(
            "OpenCorporates", API_ENDPOINTS["opencorporates"], api_key, RATE_LIMITS["opencorporates"]
        )

    async def search_company(self, name: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "/companies/search", params={"q": name, "api_token": self.api_key}
        )

    async def get_company(self, jurisdiction: str, company_number: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, f"/companies/{jurisdiction}/{company_number}"
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/companies/search", params={"q": "test"})
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class CourtListenerClient(APIClient):
    def __init__(self, api_key: str = "") -> None:
        super().__init__(
            "CourtListener", API_ENDPOINTS["courtlistener"], api_key, RATE_LIMITS["courtlistener"]
        )

    async def search_dockets(self, case_name: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "/dockets/", params={"case_name": case_name}
        )

    async def search_opinions(self, query: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "/search/", params={"q": query, "type": "o"}
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/dockets/", params={"case_name": "test"})
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


# ===================================================================
# Etherscan v2 multi-chain client
# ===================================================================


class EtherscanV2Client(APIClient):
    """Etherscan v2 API — single endpoint, multi-chain via ``chainid`` param."""

    CHAIN_NAMES = {1: "mainnet", 137: "polygon", 56: "bsc", 42161: "arbitrum", 10: "optimism", 8453: "base"}

    def __init__(self, api_key: str = "") -> None:
        super().__init__("EtherscanV2", "https://api.etherscan.io/v2/api", api_key, 5)

    async def get_balance(self, address: str, chain_id: int = 1) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "",
            params={"module": "account", "action": "balance", "address": address,
                    "tag": "latest", "apikey": self.api_key, "chainid": chain_id},
        )

    async def get_transactions(self, address: str, chain_id: int = 1, limit: int = 50) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "",
            params={"module": "account", "action": "txlist", "address": address,
                    "startblock": 0, "endblock": 99999999, "page": 1, "offset": limit,
                    "sort": "desc", "apikey": self.api_key, "chainid": chain_id},
        )

    async def get_token_transfers(self, address: str, chain_id: int = 1) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "",
            params={"module": "account", "action": "tokentx", "address": address,
                    "sort": "desc", "apikey": self.api_key, "chainid": chain_id},
        )

    async def profile_address(self, address: str, chain_id: int = 1) -> APIResponse:
        """Convenience: balance + recent tx count in one call."""
        bal = await self.get_balance(address, chain_id)
        txs = await self.get_transactions(address, chain_id, limit=50)
        tx_list = txs.data.get("result", []) if txs.success and isinstance(txs.data, dict) else []
        return APIResponse(
            success=True,
            data={
                "address": address,
                "chain": self.CHAIN_NAMES.get(chain_id, f"chain-{chain_id}"),
                "balance_wei": int(bal.data.get("result", 0)) if bal.success and isinstance(bal.data, dict) else 0,
                "tx_count": len(tx_list),
                "risk_indicators": ["high-volume"] if len(tx_list) > 100 else [],
            },
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(
            HTTPMethod.GET, "",
            params={"module": "stats", "action": "ethprice", "apikey": self.api_key, "chainid": 1},
        )
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


# ===================================================================
# RDAP domain lookup client
# ===================================================================


class RDAPClient(APIClient):
    """RDAP (Registration Data Access Protocol) client for domain investigation."""

    def __init__(self) -> None:
        super().__init__("RDAP", "https://rdap.org", "", 60)

    async def lookup_domain(self, domain: str) -> APIResponse:
        return await self._make_request(HTTPMethod.GET, f"/domain/{domain}")

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/domain/example.com")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


# ===================================================================
# Wayback Machine CDX API client
# ===================================================================


class WaybackCDXClient(APIClient):
    """Internet Archive Wayback Machine CDX API for historical snapshots."""

    def __init__(self) -> None:
        super().__init__("WaybackCDX", "https://web.archive.org/cdx/search/cdx", "", 30)

    async def search(self, url: str, limit: int = 50) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "",
            params={"url": url, "output": "json", "limit": limit, "fl": "timestamp,original,statuscode"},
        )

    async def health_check(self) -> APIStatus:
        r = await self.search("example.com", limit=1)
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


# ===================================================================
# USPTO Patent File Wrapper API client
# ===================================================================


class USPTOFileWrapperClient(APIClient):
    """USPTO Patent Application File Wrapper search API."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("USPTOFileWrapper", "https://data.uspto.gov/apis/patent-file-wrapper", api_key, 30)

    async def search(self, application_number: str, rows: int = 500) -> APIResponse:
        return await self._make_request(
            HTTPMethod.POST, "/search",
            data={"searchText": application_number, "start": 0, "rows": rows},
        )

    async def health_check(self) -> APIStatus:
        r = await self.search("16000001", rows=1)
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


# ===================================================================
# Alchemy Transfers API client
# ===================================================================


class AlchemyClient(APIClient):
    """Alchemy JSON-RPC client for asset transfers (ERC-20/721/1155)."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("Alchemy", f"https://eth-mainnet.g.alchemy.com/v2/{api_key}", api_key, 1000)

    async def get_asset_transfers(
        self, address: str, direction: str = "from", categories: Optional[list] = None,
    ) -> APIResponse:
        cats = categories or ["erc20", "erc721", "erc1155"]
        params = {
            "fromBlock": "0x0", "toBlock": "latest",
            "category": cats,
        }
        if direction == "from":
            params["fromAddress"] = address
        else:
            params["toAddress"] = address
        return await self._make_request(
            HTTPMethod.POST, "",
            data={"jsonrpc": "2.0", "id": 1, "method": "alchemy_getAssetTransfers", "params": [params]},
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(
            HTTPMethod.POST, "",
            data={"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []},
        )
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


# ===================================================================
# Additional IP office clients (7 jurisdictions)
# ===================================================================


class CNIPAClient(APIClient):
    """China National Intellectual Property Administration."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("CNIPA", "https://api.cnipa.gov.cn/patent", api_key, 200)

    async def get_patent(self, app_number: str) -> APIResponse:
        return await self._make_request(HTTPMethod.GET, f"/{app_number}")

    async def health_check(self) -> APIStatus:
        return APIStatus.UNAVAILABLE  # requires gateway registration


class JPOClient(APIClient):
    """Japan Patent Office (J-PlatPat)."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("JPO", "https://api.j-platpat.inpit.go.jp/api/v1", api_key, 300)

    async def search(self, query: str) -> APIResponse:
        return await self._make_request(HTTPMethod.GET, "/patent", params={"query": query})

    async def health_check(self) -> APIStatus:
        r = await self.search("test")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class KIPOClient(APIClient):
    """Korean Intellectual Property Office."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("KIPO", "https://api.kipo.go.kr/openapi/service/rest/PatentService", api_key, 300)

    async def search(self, keyword: str) -> APIResponse:
        return await self._make_request(HTTPMethod.GET, "", params={"ServiceKey": self.api_key, "keyword": keyword})

    async def health_check(self) -> APIStatus:
        r = await self.search("test")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class EUIPOClient(APIClient):
    """European Union Intellectual Property Office (TMview / DesignView)."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("EUIPO", "https://euipo.europa.eu/eSearchAPI/api", api_key, 400)

    async def search_trademarks(self, query: str) -> APIResponse:
        return await self._make_request(HTTPMethod.GET, "/tm/search", params={"q": query})

    async def health_check(self) -> APIStatus:
        r = await self.search_trademarks("test")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class IPOUKClient(APIClient):
    """UK Intellectual Property Office."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("IPOUK", "https://api.ipo.gov.uk/1.0", api_key, 300)

    async def get_patent(self, pub_number: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, f"/patent/{pub_number}",
            headers={"Ocp-Apim-Subscription-Key": self.api_key},
        )

    async def health_check(self) -> APIStatus:
        r = await self.get_patent("GB2000000")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class DPMAClient(APIClient):
    """German Patent and Trade Mark Office (DPMAregister)."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("DPMA", "https://register.dpma.de/DPMAregister/rest", api_key, 300)

    async def search(self, aktenzeichen: str) -> APIResponse:
        return await self._make_request(HTTPMethod.GET, f"/application/{aktenzeichen}")

    async def health_check(self) -> APIStatus:
        r = await self.search("102020000000")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class IPIndiaClient(APIClient):
    """Indian Intellectual Property Office."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("IPIndia", "https://ipindiaservices.gov.in/api", api_key, 200)

    async def get_application(self, app_number: str) -> APIResponse:
        return await self._make_request(HTTPMethod.GET, f"/patent/{app_number}")

    async def health_check(self) -> APIStatus:
        return APIStatus.UNAVAILABLE  # requires portal registration


# ===================================================================
# Additional blockchain analytics clients (8 services)
# ===================================================================


class TRMLabsClient(APIClient):
    """TRM Labs screening API."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("TRMLabs", "https://api.trmlabs.com/public/v1", api_key, 500)

    async def screen_address(self, address: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.POST, "/screening/addresses", data={"address": address},
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/health")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class InfuraClient(APIClient):
    """Infura JSON-RPC gateway."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("Infura", f"https://mainnet.infura.io/v3/{api_key}", api_key, 100_000)

    async def eth_get_logs(self, address: str, topics: Optional[list] = None) -> APIResponse:
        return await self._make_request(
            HTTPMethod.POST, "",
            data={"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
                  "params": [{"address": address, "topics": topics or [], "fromBlock": "earliest", "toBlock": "latest"}]},
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(
            HTTPMethod.POST, "",
            data={"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []},
        )
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class MoralisClient(APIClient):
    """Moralis Web3 API."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("Moralis", "https://deep-index.moralis.io/api/v2", api_key, 1500)

    async def get_token_transfers(self, address: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, f"/{address}/erc20/transfers",
            headers={"X-API-Key": self.api_key},
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/web3/version")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class CovalentClient(APIClient):
    """Covalent Unified API."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("Covalent", "https://api.covalenthq.com/v1", api_key, 500)

    async def get_transactions(self, chain_id: int, address: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, f"/{chain_id}/address/{address}/transactions_v2/",
            params={"key": self.api_key},
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/1/block/latest/", params={"key": self.api_key})
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class DuneClient(APIClient):
    """Dune Analytics API."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("Dune", "https://api.dune.com/api/v1", api_key, 300)

    async def execute_query(self, query_id: int) -> APIResponse:
        return await self._make_request(
            HTTPMethod.POST, f"/query/{query_id}/execute",
            headers={"x-dune-api-key": self.api_key},
        )

    async def get_query_results(self, execution_id: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, f"/execution/{execution_id}/results",
            headers={"x-dune-api-key": self.api_key},
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/health")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class BlockchairClient(APIClient):
    """Blockchair multi-chain explorer API."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("Blockchair", "https://api.blockchair.com", api_key, 300)

    async def get_address(self, chain: str, address: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, f"/{chain}/dashboards/address/{address}",
            params={"key": self.api_key} if self.api_key else None,
        )

    async def health_check(self) -> APIStatus:
        r = await self._make_request(HTTPMethod.GET, "/ethereum/stats")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class CryptoCompareClient(APIClient):
    """CryptoCompare market data API."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("CryptoCompare", "https://min-api.cryptocompare.com/data", api_key, 1000)

    async def get_price(self, fsym: str, tsyms: str = "USD") -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "/price",
            params={"fsym": fsym, "tsyms": tsyms, "api_key": self.api_key},
        )

    async def health_check(self) -> APIStatus:
        r = await self.get_price("BTC")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE


class CoinMarketCapClient(APIClient):
    """CoinMarketCap Pro API."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__("CoinMarketCap", "https://pro-api.coinmarketcap.com/v1", api_key, 10_000)

    async def get_quotes(self, symbol: str) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "/cryptocurrency/quotes/latest",
            params={"symbol": symbol},
            headers={"X-CMC_PRO_API_KEY": self.api_key},
        )

    async def health_check(self) -> APIStatus:
        r = await self.get_quotes("BTC")
        return APIStatus.HEALTHY if r.success else APIStatus.UNAVAILABLE
