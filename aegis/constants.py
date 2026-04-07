"""
Constants, enumerations, and configuration values for the AEGIS platform.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Dict, Final


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class EvidenceType(Enum):
    BLOCKCHAIN_TRANSACTION = auto()
    PATENT_RECORD = auto()
    LLC_RECORD = auto()
    ENABLER_RECORD = auto()
    CARTEL_NETWORK = auto()
    COURT_DOCUMENT = auto()
    AUDIT_LOG = auto()
    FINANCIAL_TRANSACTION = auto()
    NETWORK_NODE = auto()
    TIMELINE_EVENT = auto()


class RiskLevel(Enum):
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1
    UNKNOWN = 0


class BlockchainLayer(Enum):
    L1 = auto()
    L2 = auto()
    L3 = auto()
    SIDECHAIN = auto()
    PARACHAIN = auto()
    ROLLUP = auto()
    VALIDIUM = auto()


class TransactionType(Enum):
    STANDARD = auto()
    CONTRACT_CREATION = auto()
    CONTRACT_CALL = auto()
    TOKEN_TRANSFER = auto()
    NFT_TRANSFER = auto()
    DEFI_SWAP = auto()
    DEFI_LENDING = auto()
    DEFI_STAKING = auto()
    BRIDGE_DEPOSIT = auto()
    BRIDGE_WITHDRAWAL = auto()
    MIXER_DEPOSIT = auto()
    MIXER_WITHDRAWAL = auto()
    PRIVACY_SHIELDED = auto()
    BATCH = auto()
    MULTISIG = auto()
    ATOMIC_SWAP = auto()
    FLASH_LOAN = auto()
    MEV = auto()


class EntityType(Enum):
    INDIVIDUAL = "individual"
    CORPORATION = "corporation"
    SHELL_COMPANY = "shell_company"
    TRUST = "trust"
    FOUNDATION = "foundation"
    FINANCIAL_INSTITUTION = "financial_institution"
    LAW_FIRM = "law_firm"
    ACCOUNTING_FIRM = "accounting_firm"
    REAL_ESTATE = "real_estate"
    CRYPTOCURRENCY_ADDRESS = "cryptocurrency_address"
    BANK_ACCOUNT = "bank_account"
    SMART_CONTRACT = "smart_contract"
    EXCHANGE = "exchange"
    DEFI_PROTOCOL = "defi_protocol"
    MIXER = "mixer"
    BRIDGE = "bridge"
    MINING_POOL = "mining_pool"
    UNKNOWN = "unknown"


class RelationshipType(Enum):
    OWNERSHIP = "ownership"
    BENEFICIAL_OWNERSHIP = "beneficial_ownership"
    CONTROL = "control"
    DIRECTORSHIP = "directorship"
    EMPLOYMENT = "employment"
    FAMILY = "family"
    BUSINESS_ASSOCIATE = "business_associate"
    FINANCIAL_TRANSACTION = "financial_transaction"
    MONEY_LAUNDERING = "money_laundering"
    SANCTIONS_VIOLATION = "sanctions_violation"
    SHELL_NETWORK = "shell_network"
    NOMINEE = "nominee"
    PROFESSIONAL_ENABLER = "professional_enabler"
    UNKNOWN = "unknown"


class PrivacyProtocol(Enum):
    NONE = auto()
    TOR = auto()
    I2P = auto()
    MONERO = auto()
    ZCASH_SHIELDED = auto()
    ZCASH_SAPLING = auto()
    ZCASH_ORCHARD = auto()
    TORNADO_CASH = auto()
    AZTEC = auto()
    RAILGUN = auto()


class PatentStatus(Enum):
    PENDING = auto()
    GRANTED = auto()
    EXPIRED = auto()
    ABANDONED = auto()
    WITHDRAWN = auto()
    REJECTED = auto()
    OPPOSITION = auto()
    INVALIDATED = auto()


class Jurisdiction(Enum):
    USPTO = "US"
    EPO = "EP"
    WIPO = "WO"
    JPO = "JP"
    KIPO = "KR"
    CNIPA = "CN"
    UKIPO = "GB"
    CIPO = "CA"
    IPAU = "AU"
    INPI = "FR"


class HFlagSeverity(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class EvidenceGrade(Enum):
    BRONZE = 1
    SILVER = 2
    GOLD = 3
    PLATINUM = 4
    DIAMOND = 5


class NetworkPatternType(Enum):
    LAYERING = "layering"
    INTEGRATION = "integration"
    PLACEMENT = "placement"
    SMURFING = "smurfing"
    ROUND_TRIPPING = "round_tripping"
    STRUCTURING = "structuring"
    MIXING = "mixing"
    TUMBLING = "tumbling"
    CHAIN_HOPPING = "chain_hopping"


class APIStatus(Enum):
    HEALTHY = auto()
    DEGRADED = auto()
    UNAVAILABLE = auto()
    CIRCUIT_OPEN = auto()
    RATE_LIMITED = auto()


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------

ENV_PREFIX: Final[str] = "AEGIS_"
DEFAULT_TIMEOUT: Final[float] = 120.0
MAX_RETRIES: Final[int] = 5
RETRY_BACKOFF_BASE: Final[float] = 2.0
CIRCUIT_BREAKER_THRESHOLD: Final[int] = 5
CIRCUIT_BREAKER_TIMEOUT: Final[int] = 300

# Rate limits — requests per minute per API
RATE_LIMITS: Dict[str, int] = {
    "uspto": 500, "epo": 1000, "wipo": 300, "cnipa": 200, "jpo": 300,
    "kipo": 300, "euipo": 400, "ipouk": 300, "ipindia": 200, "dpma": 300,
    "chainalysis": 2000, "elliptic": 1000, "bitquery": 500, "blockchair": 300,
    "cryptocompare": 1000, "coinmarketcap": 10000, "nftscan": 500,
    "alchemy": 1000, "infura": 100000, "moralis": 1500, "dune": 300,
    "covalent": 500, "zapper": 300, "web3index": 200, "etherscan": 5,
    "sec_edgar": 10, "fincen": 100, "ofac": 50, "wayback": 200,
    "opencorporates": 200, "sayari": 500, "courtlistener": 1000,
}

# API base URLs
API_ENDPOINTS: Dict[str, str] = {
    # Intellectual Property
    "uspto": "https://developer.uspto.gov/api/v1",
    "epo": "https://ops.epo.org/3.2",
    "wipo": "https://www3.wipo.int/wipopes/api/v1",
    # Blockchain
    "chainalysis": "https://api.chainalysis.com/api",
    "elliptic": "https://api.elliptic.co/v2",
    "bitquery": "https://graphql.bitquery.io",
    "blockchair": "https://api.blockchair.com",
    "etherscan": "https://api.etherscan.io/api",
    # Public Records
    "opencorporates": "https://api.opencorporates.com/v0.4",
    "courtlistener": "https://www.courtlistener.com/api/rest/v3",
    "wayback": "https://web.archive.org/web",
    "wayback_cdx": "https://web.archive.org/cdx/search/cdx",
}

# GNN hyper-parameters
GNN_HIDDEN_DIM: Final[int] = 256
GNN_NUM_LAYERS: Final[int] = 4
QUANTUM_N_QUBITS: Final[int] = 8
