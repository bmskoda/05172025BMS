#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AEGIS Forensic Platform (demonstration / educational scaffold).

This is a self-contained research and teaching codebase. It is not affiliated
with any government agency and must not be used as a substitute for licensed
investigative or legal processes.
"""

from __future__ import annotations

import abc
import argparse
import asyncio
import base64
import binascii
import hashlib
import hmac
import json
import logging
import logging.handlers
import os
import string
import sys
import threading
import time
import uuid
import warnings
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Set, Tuple, Union
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

# -----------------------------------------------------------------------------
# Optional third-party imports (graceful degradation)
# -----------------------------------------------------------------------------

try:
    import aiohttp
    from aiohttp import ClientSession, ClientTimeout, TCPConnector

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    ClientSession = None  # type: ignore[misc, assignment]

warnings.filterwarnings("ignore", category=UserWarning)

getcontext().prec = 369

ENV_PREFIX: Final[str] = "AEGIS_"
__version__ = "16.0.1-MONOLITH"
__compliance__ = ["PEP8", "NIST-800-53 (mapping)", "ISO-27001 (mapping)"]

QUIET_IMPORT = os.environ.get(f"{ENV_PREFIX}QUIET_IMPORT", "0").lower() in (
    "1",
    "true",
    "yes",
)


def _import_log(msg: str) -> None:
    if not QUIET_IMPORT:
        print(msg, file=sys.stderr)


_import_log(f"Loaded AEGIS monolith v{__version__}")


# =============================================================================
# Enums & constants
# =============================================================================


class EvidenceType(Enum):
    BLOCKCHAIN_TRANSACTION = auto()
    PATENT_RECORD = auto()
    LLC_RECORD = auto()
    AUDIT_LOG = auto()


class TransactionType(Enum):
    STANDARD = auto()
    CONTRACT_CALL = auto()


class EntityType(Enum):
    INDIVIDUAL = "individual"
    CORPORATION = "corporation"
    CRYPTOCURRENCY_ADDRESS = "cryptocurrency_address"
    UNKNOWN = "unknown"


class RelationshipType(Enum):
    FINANCIAL_TRANSACTION = "financial_transaction"
    UNKNOWN = "unknown"


class Jurisdiction(Enum):
    USPTO = "US"
    EPO = "EP"
    WIPO = "WO"


class PatentStatus(Enum):
    PENDING = auto()
    GRANTED = auto()
    ABANDONED = auto()


def _patent_status_from_str(raw: Optional[str]) -> PatentStatus:
    if not raw:
        return PatentStatus.PENDING
    key = raw.strip().upper()
    mapping = {
        "PENDING": PatentStatus.PENDING,
        "GRANTED": PatentStatus.GRANTED,
        "ABANDONED": PatentStatus.ABANDONED,
    }
    return mapping.get(key, PatentStatus.PENDING)


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"


DEFAULT_TIMEOUT = 120.0
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 300

API_ENDPOINTS = {
    "uspto": "https://developer.uspto.gov/api/v1",
    "epo": "https://ops.epo.org/3.2",
    "wipo": "https://www3.wipo.int/wipopes/api/v1",
    "etherscan": "https://api.etherscan.io/api",
}

RATE_LIMITS = {
    "uspto": 500,
    "epo": 1000,
    "wipo": 300,
    "etherscan": 5,
}


# =============================================================================
# Core datatypes
# =============================================================================


@dataclass(frozen=True, slots=True)
class PrecisionDecimal:
    value: Decimal = field(default_factory=lambda: Decimal("0"))
    precision: int = field(default=369)

    def __post_init__(self) -> None:
        getcontext().prec = max(self.precision, 28)
        try:
            exp = Decimal("0.1") ** min(self.precision, 28)
            quantized = Decimal(str(self.value)).quantize(exp, rounding=ROUND_HALF_UP)
            object.__setattr__(self, "value", quantized)
        except (InvalidOperation, ValueError):
            object.__setattr__(self, "value", Decimal(str(self.value)))

    def __add__(self, other: "PrecisionDecimal") -> "PrecisionDecimal":
        return PrecisionDecimal(self.value + other.value, self.precision)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class Timestamp:
    nanoseconds: int = field(default_factory=lambda: int(time.time_ns()))
    timezone_offset: int = 0

    @classmethod
    def now(cls) -> "Timestamp":
        return cls(int(time.time_ns()), 0)

    @classmethod
    def from_datetime(cls, dt: datetime) -> "Timestamp":
        return cls(int(dt.timestamp() * 1e9), 0)

    @classmethod
    def from_iso(cls, iso_str: str) -> "Timestamp":
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return cls.from_datetime(dt)

    def to_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.nanoseconds / 1e9, tz=timezone.utc)

    def to_iso(self) -> str:
        return self.to_datetime().isoformat()


@dataclass(frozen=True, slots=True)
class CryptoHash:
    digest: str
    algorithm: str = "sha3_512"
    salt: str = ""

    @classmethod
    def compute(
        cls, data: Union[str, bytes], algorithm: str = "sha3_512", salt: str = ""
    ) -> "CryptoHash":
        if isinstance(data, str):
            data = data.encode("utf-8")
        if salt:
            data = salt.encode("utf-8") + data
        hash_func = getattr(hashlib, algorithm, hashlib.sha3_512)
        digest = hash_func(data).hexdigest()
        return cls(digest, algorithm, salt)

    def verify(self, data: Union[str, bytes]) -> bool:
        computed = self.compute(data, self.algorithm, self.salt)
        return hmac.compare_digest(self.digest, computed.digest)


@dataclass(slots=True)
class EvidenceMetadata:
    """
    Mutable chain-of-custody container (not frozen — lists must be updatable).
    """

    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    evidence_type: EvidenceType = EvidenceType.BLOCKCHAIN_TRANSACTION
    timestamp: Timestamp = field(default_factory=Timestamp.now)
    source: str = ""
    hash: Optional[CryptoHash] = None
    chain_of_custody: List[Dict[str, Any]] = field(default_factory=list)
    investigator_id: str = ""
    case_number: str = ""

    def add_custody_entry(
        self, action: str, actor: str, timestamp: Optional[Timestamp] = None
    ) -> None:
        ts = timestamp or Timestamp.now()
        entry = {
            "action": action,
            "actor": actor,
            "timestamp": ts.to_iso(),
            "hash": CryptoHash.compute(f"{action}:{actor}:{ts.nanoseconds}").digest,
        }
        self.chain_of_custody.append(entry)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type.name,
            "timestamp": self.timestamp.to_iso(),
            "source": self.source,
            "hash": self.hash.digest if self.hash else None,
            "chain_of_custody": list(self.chain_of_custody),
            "investigator_id": self.investigator_id,
            "case_number": self.case_number,
        }


@dataclass(frozen=True, slots=True)
class BlockchainAddress:
    address: str
    network: str

    def __post_init__(self) -> None:
        if not self.address or not self.network:
            raise ValueError("address and network are required")

    def to_dict(self) -> Dict[str, Any]:
        return {"address": self.address, "network": self.network}


@dataclass(frozen=True, slots=True)
class Transaction:
    tx_hash: str
    network: str
    block_number: int
    timestamp: Timestamp
    from_address: BlockchainAddress
    to_address: Optional[BlockchainAddress]
    value: PrecisionDecimal
    input_data: str = ""
    transaction_type: TransactionType = TransactionType.STANDARD
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_hash": self.tx_hash,
            "network": self.network,
            "block_number": self.block_number,
            "timestamp": self.timestamp.to_iso(),
            "from_address": self.from_address.to_dict(),
            "to_address": self.to_address.to_dict() if self.to_address else None,
            "value": str(self.value),
            "transaction_type": self.transaction_type.name,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class NetworkNode:
    node_id: str
    entity_type: EntityType
    name: str
    risk_score: float = 0.0
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "risk_score": self.risk_score,
            "attributes": self.attributes,
        }


@dataclass(frozen=True, slots=True)
class NetworkEdge:
    edge_id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class PatentRecord:
    patent_id: str
    jurisdiction: Jurisdiction
    application_number: str
    publication_number: str
    title: str
    abstract: str
    inventors: List[Dict[str, Any]] = field(default_factory=list)
    assignees: List[Dict[str, Any]] = field(default_factory=list)
    filing_date: Optional[Timestamp] = None
    status: PatentStatus = PatentStatus.PENDING
    family_members: List[str] = field(default_factory=list)
    h_flag_score: float = 0.0
    synthetic_identity_risk: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patent_id": self.patent_id,
            "jurisdiction": self.jurisdiction.value,
            "application_number": self.application_number,
            "publication_number": self.publication_number,
            "title": self.title,
            "status": self.status.name,
            "h_flag_score": self.h_flag_score,
            "synthetic_identity_risk": self.synthetic_identity_risk,
        }


@dataclass(frozen=True, slots=True)
class APIResponse:
    success: bool
    data: Any = None
    error: Optional[str] = None
    status_code: int = 200
    timestamp: Timestamp = field(default_factory=Timestamp.now)
    latency_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class InvestigationResult:
    investigation_id: str
    timestamp: Timestamp
    entities: List[NetworkNode] = field(default_factory=list)
    relationships: List[NetworkEdge] = field(default_factory=list)
    transactions: List[Transaction] = field(default_factory=list)
    patents: List[PatentRecord] = field(default_factory=list)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    evidence_metadata: List[EvidenceMetadata] = field(default_factory=list)


@dataclass
class UnifiedConfiguration:
    log_level: str = "INFO"
    timeout_seconds: int = 120
    uspto_api_key: str = ""
    epo_api_key: str = ""
    wipo_api_key: str = ""
    etherscan_api_key: str = ""

    @classmethod
    def from_environment(cls) -> "UnifiedConfiguration":
        c = cls()
        c.log_level = os.getenv(f"{ENV_PREFIX}LOG_LEVEL", c.log_level)
        c.timeout_seconds = int(
            os.getenv(f"{ENV_PREFIX}TIMEOUT_SECONDS", str(c.timeout_seconds))
        )
        c.uspto_api_key = os.getenv(f"{ENV_PREFIX}USPTO_API_KEY", "")
        c.epo_api_key = os.getenv(f"{ENV_PREFIX}EPO_API_KEY", "")
        c.wipo_api_key = os.getenv(f"{ENV_PREFIX}WIPO_API_KEY", "")
        c.etherscan_api_key = os.getenv(f"{ENV_PREFIX}ETHERSCAN_API_KEY", "")
        return c

    def to_dict(self) -> Dict[str, Any]:
        redact = ("key", "secret", "password", "token")
        out: Dict[str, Any] = {}
        for k, v in self.__dict__.items():
            if any(x in k.lower() for x in redact):
                out[k] = "***REDACTED***"
            else:
                out[k] = v
        return out


# =============================================================================
# Logging
# =============================================================================


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("AEGIS")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=3
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


def get_logger(name: str = "AEGIS") -> logging.Logger:
    return logging.getLogger(name)


# =============================================================================
# HTTP / API layer (aiohttp or urllib fallback)
# =============================================================================


class CircuitBreaker:
    def __init__(
        self, threshold: int = CIRCUIT_BREAKER_THRESHOLD, timeout: int = CIRCUIT_BREAKER_TIMEOUT
    ):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        with self._lock:
            if self.state == "closed":
                return True
            if self.state == "open":
                if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                    self.state = "half-open"
                    self.failure_count = 0
                    return True
                return False
            return True

    def record_success(self) -> None:
        with self._lock:
            self.failure_count = 0
            self.state = "closed"

    def record_failure(self) -> None:
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.threshold:
                self.state = "open"


class RateLimiter:
    def __init__(self, requests_per_minute: int):
        self.rate = requests_per_minute / 60.0
        self.tokens = requests_per_minute / 60.0
        self.last_update = time.time()
        self.capacity = requests_per_minute / 60.0
        self._lock = threading.Lock()

    async def wait_and_acquire(self) -> None:
        while not self._acquire():
            await asyncio.sleep(0.05)

    def _acquire(self) -> bool:
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


def _http_request_sync(
    method: str,
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]],
    data: Optional[Dict[str, Any]],
    timeout: float,
) -> Tuple[int, bytes, Dict[str, str]]:
    if params:
        q = urlencode({k: str(v) for k, v in params.items()})
        url = f"{url}?{q}" if "?" not in url else f"{url}&{q}"
    body: Optional[bytes] = None
    hdrs = dict(headers)
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = Request(url, data=body, headers=hdrs, method=method)
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        return resp.getcode(), raw, dict(resp.headers.items())


class APIClient(abc.ABC):
    def __init__(
        self,
        api_name: str,
        base_url: str,
        api_key: str = "",
        rate_limit: int = 100,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_name = api_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limiter = RateLimiter(rate_limit)
        self.circuit_breaker = CircuitBreaker()
        self._session: Optional["ClientSession"] = None
        self._logger = get_logger(f"API.{api_name}")
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix=f"aegis-{api_name}")

    async def _get_session(self) -> "ClientSession":
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp is not installed")
        if self._session is None or self._session.closed:
            connector = TCPConnector(limit=50, limit_per_host=10)
            timeout = ClientTimeout(total=self.timeout)
            self._session = ClientSession(connector=connector, timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        self._executor.shutdown(wait=False)

    async def _make_request(
        self,
        method: HTTPMethod,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        if not self.circuit_breaker.can_execute():
            return APIResponse(success=False, error="Circuit breaker is open", status_code=503)

        await self.rate_limiter.wait_and_acquire()
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        request_headers = {"Accept": "application/json", "User-Agent": f"AEGIS-Platform/{__version__}"}
        if self.api_key:
            request_headers["Authorization"] = f"Bearer {self.api_key}"
        if headers:
            request_headers.update(headers)

        start = time.perf_counter()

        try:
            if AIOHTTP_AVAILABLE:
                session = await self._get_session()
                async with session.request(
                    method.value, url, params=params, json=data, headers=request_headers
                ) as response:
                    latency_ms = (time.perf_counter() - start) * 1000
                    if response.status == 429:
                        self.circuit_breaker.record_failure()
                        return APIResponse(
                            success=False,
                            error="Rate limit exceeded",
                            status_code=429,
                            latency_ms=latency_ms,
                        )
                    text = await response.text()
                    self.circuit_breaker.record_success()
                    ctype = response.headers.get("Content-Type", "")
                    if "application/json" in ctype:
                        payload: Any = json.loads(text) if text else None
                    else:
                        payload = text
                    return APIResponse(
                        success=response.status < 400,
                        data=payload,
                        status_code=response.status,
                        latency_ms=latency_ms,
                    )

            loop = asyncio.get_running_loop()
            status, raw, _hdrs = await loop.run_in_executor(
                self._executor,
                lambda: _http_request_sync(
                    method.value,
                    url,
                    request_headers,
                    params,
                    data,
                    float(self.timeout),
                ),
            )
            latency_ms = (time.perf_counter() - start) * 1000
            if status == 429:
                self.circuit_breaker.record_failure()
                return APIResponse(
                    success=False, error="Rate limit exceeded", status_code=429, latency_ms=latency_ms
                )
            if status >= 400:
                self.circuit_breaker.record_failure()
                return APIResponse(
                    success=False,
                    error=f"HTTP {status}",
                    status_code=status,
                    latency_ms=latency_ms,
                )
            self.circuit_breaker.record_success()
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else None
            except json.JSONDecodeError:
                payload = raw.decode("utf-8", errors="replace")
            return APIResponse(success=True, data=payload, status_code=status, latency_ms=latency_ms)
        except Exception as e:
            self.circuit_breaker.record_failure()
            latency_ms = (time.perf_counter() - start) * 1000
            self._logger.error("Request failed: %s", e)
            return APIResponse(success=False, error=str(e), status_code=500, latency_ms=latency_ms)

    @abc.abstractmethod
    async def health_check(self) -> bool:
        pass


class EtherscanClient(APIClient):
    def __init__(self, api_key: str = ""):
        super().__init__(
            api_name="Etherscan",
            base_url=API_ENDPOINTS["etherscan"],
            api_key=api_key,
            rate_limit=RATE_LIMITS["etherscan"],
        )

    async def get_transactions(self, address: str, start_block: int = 0, end_block: int = 99_999_999) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET,
            "",
            params={
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": start_block,
                "endblock": end_block,
                "sort": "desc",
                "apikey": self.api_key or "",
            },
        )

    async def health_check(self) -> bool:
        r = await self._make_request(
            HTTPMethod.GET,
            "",
            params={"module": "stats", "action": "ethprice", "apikey": self.api_key or ""},
        )
        return bool(r.success)


class USPTOClient(APIClient):
    def __init__(self, api_key: str = ""):
        super().__init__(
            api_name="USPTO",
            base_url=API_ENDPOINTS["uspto"],
            api_key=api_key,
            rate_limit=RATE_LIMITS["uspto"],
        )

    async def search_patents(self, query: str, limit: int = 25) -> APIResponse:
        return await self._make_request(
            HTTPMethod.GET, "/patents/search", params={"q": query, "limit": str(limit)}
        )

    async def health_check(self) -> bool:
        r = await self._make_request(HTTPMethod.GET, "/health")
        return bool(r.success)


class APIIntegrationManager:
    def __init__(self, config: UnifiedConfiguration):
        self.config = config
        self._clients: Dict[str, APIClient] = {}
        self._logger = get_logger("API.Manager")

    async def initialize(self) -> None:
        if self.config.etherscan_api_key:
            self._clients["etherscan"] = EtherscanClient(self.config.etherscan_api_key)
        if self.config.uspto_api_key:
            self._clients["uspto"] = USPTOClient(self.config.uspto_api_key)
        self._logger.info("Initialized %d API client(s)", len(self._clients))

    def get_client(self, name: str) -> Optional[APIClient]:
        return self._clients.get(name)

    async def health_check_all(self) -> Dict[str, bool]:
        out: Dict[str, bool] = {}
        for name, client in self._clients.items():
            try:
                out[name] = await client.health_check()
            except Exception as e:
                self._logger.error("Health check failed for %s: %s", name, e)
                out[name] = False
        return out

    async def close_all(self) -> None:
        for c in self._clients.values():
            await c.close()


# =============================================================================
# Blockchain tracing (Etherscan)
# =============================================================================


def validate_blockchain_address(address: str, network: str) -> bool:
    if not address or not network:
        return False
    network = network.lower()
    if network in ("ethereum", "eth", "polygon", "arbitrum", "optimism", "base"):
        if not address.startswith("0x"):
            return False
        return len(address) == 42 and all(c in string.hexdigits for c in address[2:])
    if network in ("bitcoin", "btc"):
        if address.startswith(("1", "3")):
            return 26 <= len(address) <= 35
        if address.startswith("bc1"):
            return 42 <= len(address) <= 62
        return False
    if network in ("solana", "sol"):
        try:
            decoded = base64.b64decode(address)
            return len(decoded) == 32
        except (binascii.Error, ValueError):
            return False
    return True


class TransactionTracer:
    def __init__(self, api_manager: APIIntegrationManager):
        self.api_manager = api_manager
        self._logger = get_logger("Blockchain.Tracer")
        self._visited: Set[str] = set()

    async def trace_address(
        self, address: str, network: str, max_depth: int = 5, max_transactions: int = 500
    ) -> List[Transaction]:
        self._visited.clear()
        acc: List[Transaction] = []
        await self._trace_recursive(address, network, 0, max_depth, max_transactions, acc)
        self._logger.info("Traced %d transactions for %s", len(acc), address[:16])
        return acc

    async def _trace_recursive(
        self,
        address: str,
        network: str,
        depth: int,
        max_depth: int,
        max_transactions: int,
        transactions: List[Transaction],
    ) -> None:
        if depth >= max_depth or len(transactions) >= max_transactions:
            return
        key = f"{network}:{address.lower()}"
        if key in self._visited:
            return
        self._visited.add(key)

        etherscan = self.api_manager.get_client("etherscan")
        if not etherscan or not isinstance(etherscan, EtherscanClient):
            self._logger.warning("Etherscan client not configured; skipping trace.")
            return

        response = await etherscan.get_transactions(address)
        if not response.success or not response.data:
            return

        rows = response.data.get("result", []) if isinstance(response.data, dict) else []
        if not isinstance(rows, list):
            return

        for tx_data in rows[:50]:
            tx = self._parse_transaction(tx_data, network)
            if tx:
                transactions.append(tx)
            if tx and tx.to_address and len(transactions) < max_transactions:
                await self._trace_recursive(
                    tx.to_address.address,
                    network,
                    depth + 1,
                    max_depth,
                    max_transactions,
                    transactions,
                )

    def _parse_transaction(self, tx_data: Dict[str, Any], network: str) -> Optional[Transaction]:
        try:
            ts_raw = tx_data.get("timeStamp", "0")
            ts = Timestamp(int(ts_raw) * 1_000_000_000)
            to_raw = tx_data.get("to") or ""
            return Transaction(
                tx_hash=tx_data.get("hash", ""),
                network=network,
                block_number=int(tx_data.get("blockNumber", 0)),
                timestamp=ts,
                from_address=BlockchainAddress(address=tx_data.get("from", ""), network=network),
                to_address=BlockchainAddress(address=to_raw, network=network) if to_raw else None,
                value=PrecisionDecimal(Decimal(tx_data.get("value", "0")) / Decimal("1e18")),
                input_data=tx_data.get("input", "") or "",
                status="confirmed" if tx_data.get("txreceipt_status") == "1" else "pending",
            )
        except (ValueError, TypeError, InvalidOperation) as e:
            self._logger.error("Failed to parse transaction: %s", e)
            return None


class BlockchainForensicsEngine:
    def __init__(self, api_manager: APIIntegrationManager, config: UnifiedConfiguration):
        self.api_manager = api_manager
        self.config = config
        self.tracer = TransactionTracer(api_manager)
        self._logger = get_logger("Blockchain.Engine")

    async def analyze_address(self, address: str, network: str, max_depth: int = 5) -> Dict[str, Any]:
        if not validate_blockchain_address(address, network):
            return {"error": "Invalid address format"}
        txs = await self.tracer.trace_address(address, network, max_depth=max_depth)
        return {
            "address": address,
            "network": network,
            "transaction_count": len(txs),
            "transactions": [t.to_dict() for t in txs[:50]],
        }


# =============================================================================
# Patent engine (minimal)
# =============================================================================


class PatentAnalysisEngine:
    def __init__(self, api_manager: APIIntegrationManager, config: UnifiedConfiguration):
        self.api_manager = api_manager
        self.config = config
        self._logger = get_logger("Patent.Engine")

    async def search_patents(
        self, query: str, jurisdiction: Optional[Jurisdiction] = None, limit: int = 50
    ) -> List[PatentRecord]:
        patents: List[PatentRecord] = []
        if jurisdiction is not None and jurisdiction != Jurisdiction.USPTO:
            return patents
        uspto = self.api_manager.get_client("uspto")
        if not uspto or not isinstance(uspto, USPTOClient):
            return patents
        response = await uspto.search_patents(query, limit)
        if not response.success or not isinstance(response.data, dict):
            return patents
        for item in response.data.get("results", response.data.get("patents", [])):
            try:
                patents.append(
                    PatentRecord(
                        patent_id=str(item.get("patent_id", item.get("id", uuid.uuid4()))),
                        jurisdiction=Jurisdiction.USPTO,
                        application_number=str(item.get("application_number", "")),
                        publication_number=str(item.get("publication_number", "")),
                        title=str(item.get("title", "")),
                        abstract=str(item.get("abstract", "")),
                        inventors=list(item.get("inventors", []) or []),
                        assignees=list(item.get("assignees", []) or []),
                        filing_date=self._parse_date(item.get("filing_date")),
                        status=_patent_status_from_str(item.get("status")),
                        family_members=list(item.get("family_members", []) or []),
                    )
                )
            except (TypeError, ValueError) as e:
                self._logger.error("Failed to parse patent: %s", e)
        return patents

    def _parse_date(self, date_str: Optional[str]) -> Optional[Timestamp]:
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            return Timestamp.from_datetime(dt)
        except ValueError:
            return None


# =============================================================================
# Report + orchestrator
# =============================================================================


class ForensicReportGenerator:
    def __init__(self, config: UnifiedConfiguration):
        self.config = config
        self._logger = get_logger("Report.Generator")

    def generate_investigation_report(self, investigation_result: InvestigationResult) -> Dict[str, Any]:
        return {
            "report_metadata": {
                "report_id": str(uuid.uuid4()),
                "investigation_id": investigation_result.investigation_id,
                "generated_at": Timestamp.now().to_iso(),
            },
            "entities_count": len(investigation_result.entities),
            "transactions_count": len(investigation_result.transactions),
            "patents_count": len(investigation_result.patents),
            "risk_assessment": investigation_result.risk_assessment,
        }

    def save_report(self, report: Dict[str, Any], output_path: str) -> str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        self._logger.info("Report saved to %s", output_path)
        return output_path


class AEGISOrchestrator:
    def __init__(self, config: Optional[UnifiedConfiguration] = None):
        self.config = config or UnifiedConfiguration.from_environment()
        self._logger = get_logger("AEGIS.Orchestrator")
        self.api_manager = APIIntegrationManager(self.config)
        self.blockchain_engine = BlockchainForensicsEngine(self.api_manager, self.config)
        self.patent_engine = PatentAnalysisEngine(self.api_manager, self.config)
        self.report_generator = ForensicReportGenerator(self.config)
        self._initialized = False
        self._results: List[InvestigationResult] = []

    async def initialize(self) -> None:
        self._logger.info("Initializing AEGIS...")
        await self.api_manager.initialize()
        self._initialized = True

    async def shutdown(self) -> None:
        await self.api_manager.close_all()

    async def run_investigation(
        self, investigation_type: str, target: str, options: Optional[Dict[str, Any]] = None
    ) -> InvestigationResult:
        if not self._initialized:
            raise RuntimeError("Call initialize() first")
        options = options or {}
        if investigation_type == "blockchain":
            network = options.get("network", "ethereum")
            max_depth = int(options.get("max_depth", 5))
            analysis = await self.blockchain_engine.analyze_address(target, network, max_depth)
            txs: List[Transaction] = []
            for td in analysis.get("transactions", []):
                txs.append(
                    Transaction(
                        tx_hash=td["tx_hash"],
                        network=td["network"],
                        block_number=int(td["block_number"]),
                        timestamp=Timestamp.from_iso(td["timestamp"]),
                        from_address=BlockchainAddress(
                            address=td["from_address"]["address"], network=network
                        ),
                        to_address=BlockchainAddress(
                            address=td["to_address"]["address"], network=network
                        )
                        if td.get("to_address")
                        else None,
                        value=PrecisionDecimal(Decimal(str(td["value"]))),
                        status=td.get("status", "unknown"),
                    )
                )
            return InvestigationResult(
                investigation_id=f"BLOCKCHAIN-{uuid.uuid4().hex[:8].upper()}",
                timestamp=Timestamp.now(),
                entities=[
                    NetworkNode(
                        node_id=target,
                        entity_type=EntityType.CRYPTOCURRENCY_ADDRESS,
                        name=f"Address {target[:10]}...",
                    )
                ],
                transactions=txs,
                risk_assessment={"mode": "blockchain", "detail": analysis},
            )
        if investigation_type == "patent":
            patents = await self.patent_engine.search_patents(target, limit=10)
            return InvestigationResult(
                investigation_id=f"PATENT-{uuid.uuid4().hex[:8].upper()}",
                timestamp=Timestamp.now(),
                patents=patents,
                risk_assessment={"mode": "patent", "count": len(patents)},
            )
        raise ValueError(f"Unknown investigation type: {investigation_type}")

    def generate_report(self, investigation_result: InvestigationResult, output_path: str) -> str:
        report = self.report_generator.generate_investigation_report(investigation_result)
        return self.report_generator.save_report(report, output_path)


def create_argument_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="AEGIS demonstration CLI")
    p.add_argument("--log-level", default="INFO")
    sub = p.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("investigate")
    inv.add_argument("investigation_type", choices=["blockchain", "patent"])
    inv.add_argument("--target", required=True)
    inv.add_argument("--network", default="ethereum")
    inv.add_argument("--max-depth", type=int, default=5)
    inv.add_argument("--output", default="./output/investigation_report.json")
    st = sub.add_parser("status")
    st.set_defaults(func=lambda _: None)
    return p


async def main_async() -> int:
    parser = create_argument_parser()
    args = parser.parse_args()
    setup_logging(args.log_level)
    logger = get_logger("AEGIS")
    orch = AEGISOrchestrator(UnifiedConfiguration.from_environment())
    await orch.initialize()
    try:
        if args.command == "investigate":
            res = await orch.run_investigation(
                args.investigation_type,
                args.target,
                {"network": args.network, "max_depth": args.max_depth},
            )
            path = orch.generate_report(res, args.output)
            print(json.dumps({"investigation_id": res.investigation_id, "report": path}, indent=2))
        elif args.command == "status":
            print(json.dumps({"version": __version__, "aiohttp": AIOHTTP_AVAILABLE}, indent=2))
        return 0
    finally:
        await orch.shutdown()


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
