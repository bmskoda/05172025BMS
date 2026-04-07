"""
Frozen, slot-based dataclasses for the AEGIS forensic platform.

Every domain object is immutable by default to preserve evidence integrity.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, getcontext, InvalidOperation
from typing import Any, Dict, List, Optional, Set, Union

from aegis.constants import (
    EvidenceGrade,
    EvidenceType,
    EntityType,
    Jurisdiction,
    PatentStatus,
    PrivacyProtocol,
    RelationshipType,
    RiskLevel,
    TransactionType,
)


@dataclass(frozen=True, slots=True)
class PrecisionDecimal:
    """Arbitrary-precision decimal for financial / forensic calculations."""

    value: Decimal = field(default_factory=lambda: Decimal("0"))
    precision: int = field(default=28)

    def __post_init__(self) -> None:
        ctx = getcontext()
        ctx.prec = max(self.precision, ctx.prec)
        try:
            exp = Decimal("0.1") ** min(self.precision, 28)
            quantized = Decimal(str(self.value)).quantize(exp, rounding=ROUND_HALF_UP)
            object.__setattr__(self, "value", quantized)
        except (InvalidOperation, ValueError):
            object.__setattr__(self, "value", Decimal(str(self.value)))

    def __add__(self, other: PrecisionDecimal) -> PrecisionDecimal:
        return PrecisionDecimal(self.value + other.value, self.precision)

    def __sub__(self, other: PrecisionDecimal) -> PrecisionDecimal:
        return PrecisionDecimal(self.value - other.value, self.precision)

    def __mul__(self, other: PrecisionDecimal) -> PrecisionDecimal:
        return PrecisionDecimal(self.value * other.value, self.precision)

    def __truediv__(self, other: PrecisionDecimal) -> PrecisionDecimal:
        if other.value == 0:
            raise ZeroDivisionError("Division by zero")
        return PrecisionDecimal(self.value / other.value, self.precision)

    def __str__(self) -> str:
        return str(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def __hash__(self) -> int:
        return hash((self.value, self.precision))


@dataclass(frozen=True, slots=True)
class Timestamp:
    """High-precision nanosecond timestamp (UTC)."""

    nanoseconds: int = field(default_factory=lambda: int(time.time_ns()))
    timezone_offset: int = field(default=0)

    @classmethod
    def now(cls) -> Timestamp:
        return cls(int(time.time_ns()), 0)

    @classmethod
    def from_datetime(cls, dt: datetime) -> Timestamp:
        return cls(int(dt.timestamp() * 1e9), 0)

    @classmethod
    def from_iso(cls, iso_str: str) -> Timestamp:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return cls.from_datetime(dt)

    @classmethod
    def from_epoch(cls, epoch: Union[int, float]) -> Timestamp:
        if epoch > 1e12:
            epoch = epoch / 1000
        return cls(int(epoch * 1e9), 0)

    def to_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.nanoseconds / 1e9, tz=timezone.utc)

    def to_iso(self) -> str:
        return self.to_datetime().isoformat()

    def __str__(self) -> str:
        return self.to_iso()

    def __lt__(self, other: Timestamp) -> bool:
        return self.nanoseconds < other.nanoseconds

    def __le__(self, other: Timestamp) -> bool:
        return self.nanoseconds <= other.nanoseconds

    def __gt__(self, other: Timestamp) -> bool:
        return self.nanoseconds > other.nanoseconds

    def __ge__(self, other: Timestamp) -> bool:
        return self.nanoseconds >= other.nanoseconds

    def __hash__(self) -> int:
        return hash(self.nanoseconds)


@dataclass(frozen=True, slots=True)
class CryptoHash:
    """Cryptographic hash with algorithm metadata."""

    digest: str
    algorithm: str = field(default="sha3_256")
    salt: str = field(default="")

    @classmethod
    def compute(cls, data: Union[str, bytes], algorithm: str = "sha3_256", salt: str = "") -> CryptoHash:
        raw = data.encode("utf-8") if isinstance(data, str) else data
        if salt:
            raw = salt.encode("utf-8") + raw
        hash_func = getattr(hashlib, algorithm, hashlib.sha3_256)
        return cls(hash_func(raw).hexdigest(), algorithm, salt)

    def verify(self, data: Union[str, bytes]) -> bool:
        computed = self.compute(data, self.algorithm, self.salt)
        return hmac.compare_digest(self.digest, computed.digest)

    def __str__(self) -> str:
        return f"{self.algorithm}:{self.digest[:16]}..."

    def __hash__(self) -> int:
        return hash((self.digest, self.algorithm))


@dataclass(slots=True)
class EvidenceMetadata:
    """Chain-of-custody metadata for a single piece of evidence."""

    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    evidence_type: EvidenceType = EvidenceType.BLOCKCHAIN_TRANSACTION
    timestamp: Timestamp = field(default_factory=Timestamp.now)
    source: str = ""
    hash: Optional[CryptoHash] = None
    grade: EvidenceGrade = EvidenceGrade.BRONZE
    chain_of_custody: List[Dict[str, Any]] = field(default_factory=list)
    investigator_id: str = ""
    case_number: str = ""
    jurisdiction: str = ""
    classification: str = "PRIVILEGED — ATTORNEY WORK PRODUCT"
    retention_period_days: int = 2555

    def add_custody_entry(self, action: str, actor: str, ts: Optional[Timestamp] = None) -> None:
        self.chain_of_custody.append({
            "action": action,
            "actor": actor,
            "timestamp": (ts or Timestamp.now()).to_iso(),
            "hash": CryptoHash.compute(f"{action}:{actor}").digest,
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type.name,
            "timestamp": self.timestamp.to_iso(),
            "source": self.source,
            "hash": self.hash.digest if self.hash else None,
            "grade": self.grade.name,
            "chain_of_custody": self.chain_of_custody,
            "jurisdiction": self.jurisdiction,
        }


# ---------------------------------------------------------------------------
# Blockchain models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BlockchainAddress:
    address: str
    network: str
    address_type: str = ""
    label: Optional[str] = None
    risk_score: float = 0.0
    tags: Set[str] = field(default_factory=set)
    first_seen: Optional[Timestamp] = None
    last_seen: Optional[Timestamp] = None

    def __hash__(self) -> int:
        return hash((self.address.lower(), self.network.lower()))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BlockchainAddress):
            return NotImplemented
        return self.address.lower() == other.address.lower() and self.network.lower() == other.network.lower()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address, "network": self.network,
            "address_type": self.address_type, "label": self.label,
            "risk_score": self.risk_score, "tags": list(self.tags),
            "first_seen": self.first_seen.to_iso() if self.first_seen else None,
            "last_seen": self.last_seen.to_iso() if self.last_seen else None,
        }


@dataclass(frozen=True, slots=True)
class Transaction:
    tx_hash: str
    network: str
    block_number: int
    timestamp: Timestamp
    from_address: BlockchainAddress
    to_address: Optional[BlockchainAddress]
    value: PrecisionDecimal
    gas_price: Optional[PrecisionDecimal] = None
    gas_used: Optional[int] = None
    nonce: Optional[int] = None
    input_data: str = ""
    transaction_type: TransactionType = TransactionType.STANDARD
    status: str = "pending"
    confirmations: int = 0
    fee: Optional[PrecisionDecimal] = None
    token_transfers: List[Dict[str, Any]] = field(default_factory=list)
    privacy_protocol: PrivacyProtocol = PrivacyProtocol.NONE
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.MINIMAL
    trace_depth: int = 0
    parent_tx: Optional[str] = None
    child_txs: List[str] = field(default_factory=list)
    is_sanctioned: bool = False
    is_mixer: bool = False
    is_bridge: bool = False
    is_defi: bool = False
    is_nft: bool = False
    bridge_info: Optional[Dict[str, Any]] = None
    mixer_info: Optional[Dict[str, Any]] = None
    defi_info: Optional[Dict[str, Any]] = None
    nft_metadata: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_hash": self.tx_hash, "network": self.network,
            "block_number": self.block_number, "timestamp": self.timestamp.to_iso(),
            "from_address": self.from_address.to_dict(),
            "to_address": self.to_address.to_dict() if self.to_address else None,
            "value": str(self.value), "gas_price": str(self.gas_price) if self.gas_price else None,
            "gas_used": self.gas_used, "transaction_type": self.transaction_type.name,
            "status": self.status, "confirmations": self.confirmations,
            "fee": str(self.fee) if self.fee else None,
            "token_transfers": self.token_transfers,
            "privacy_protocol": self.privacy_protocol.name,
            "risk_score": self.risk_score, "risk_level": self.risk_level.name,
            "trace_depth": self.trace_depth,
            "is_sanctioned": self.is_sanctioned, "is_mixer": self.is_mixer,
            "is_bridge": self.is_bridge, "is_defi": self.is_defi, "is_nft": self.is_nft,
            "bridge_info": self.bridge_info, "defi_info": self.defi_info,
        }


@dataclass(frozen=True, slots=True)
class TokenTransfer:
    tx_hash: str
    token_address: str
    token_type: str
    token_symbol: str
    token_decimals: int
    from_address: BlockchainAddress
    to_address: BlockchainAddress
    value: PrecisionDecimal
    token_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_hash": self.tx_hash, "token_address": self.token_address,
            "token_type": self.token_type, "token_symbol": self.token_symbol,
            "from_address": self.from_address.to_dict(),
            "to_address": self.to_address.to_dict(), "value": str(self.value),
            "token_id": self.token_id,
        }


# ---------------------------------------------------------------------------
# Wallet entity (mutable for enrichment)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class WalletEntity:
    """Wallet entity with attribution and risk profiling."""

    address: str
    blockchain: str
    entity_type: EntityType = EntityType.UNKNOWN
    entity_name: Optional[str] = None
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.MINIMAL
    is_sanctioned: bool = False
    is_exchange: bool = False
    exchange_name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    first_seen: Optional[Timestamp] = None
    last_seen: Optional[Timestamp] = None
    total_received: Decimal = field(default_factory=lambda: Decimal("0"))
    total_sent: Decimal = field(default_factory=lambda: Decimal("0"))
    balance: Decimal = field(default_factory=lambda: Decimal("0"))
    transaction_count: int = 0
    related_addresses: List[str] = field(default_factory=list)
    cluster_id: Optional[str] = None
    cluster_size: int = 0
    attribution_sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address, "blockchain": self.blockchain,
            "entity_type": self.entity_type.value, "entity_name": self.entity_name,
            "risk_score": self.risk_score, "risk_level": self.risk_level.name,
            "is_sanctioned": self.is_sanctioned, "is_exchange": self.is_exchange,
            "exchange_name": self.exchange_name, "tags": self.tags,
            "balance": str(self.balance), "transaction_count": self.transaction_count,
            "cluster_id": self.cluster_id, "cluster_size": self.cluster_size,
        }


# ---------------------------------------------------------------------------
# Cross-chain / mixer / DeFi interaction records
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CrossChainBridge:
    """Records a deposit → withdrawal pair across chains."""

    bridge_name: str
    source_chain: str
    target_chain: str
    deposit_tx: str
    withdrawal_tx: Optional[str]
    depositor: str
    recipient: Optional[str]
    amount: PrecisionDecimal
    token: str
    timestamp: Timestamp
    status: str = "pending"
    risk_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bridge_name": self.bridge_name, "source_chain": self.source_chain,
            "target_chain": self.target_chain, "deposit_tx": self.deposit_tx,
            "withdrawal_tx": self.withdrawal_tx, "depositor": self.depositor,
            "recipient": self.recipient, "amount": str(self.amount),
            "token": self.token, "timestamp": self.timestamp.to_iso(),
            "status": self.status, "risk_score": self.risk_score,
        }


@dataclass(frozen=True, slots=True)
class MixerTransaction:
    """Records a mixer/tumbler deposit or withdrawal."""

    mixer_name: str
    mixer_protocol: PrivacyProtocol
    deposit_tx: str
    withdrawal_tx: Optional[str]
    depositor: str
    recipient: Optional[str]
    amount: PrecisionDecimal
    currency: str
    timestamp: Timestamp
    anonymity_set_size: int = 0
    time_delay_hours: float = 0.0
    risk_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mixer_name": self.mixer_name, "mixer_protocol": self.mixer_protocol.name,
            "deposit_tx": self.deposit_tx, "withdrawal_tx": self.withdrawal_tx,
            "depositor": self.depositor, "recipient": self.recipient,
            "amount": str(self.amount), "currency": self.currency,
            "timestamp": self.timestamp.to_iso(),
            "anonymity_set_size": self.anonymity_set_size,
            "risk_score": self.risk_score,
        }


@dataclass(frozen=True, slots=True)
class DeFiInteraction:
    """Records a DeFi protocol interaction (swap, lend, borrow, etc.)."""

    protocol_name: str
    interaction_type: str
    tx_hash: str
    user_address: str
    contract_address: str
    input_amount: PrecisionDecimal
    output_amount: Optional[PrecisionDecimal]
    input_token: str
    output_token: Optional[str]
    timestamp: Timestamp
    gas_cost: PrecisionDecimal
    risk_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocol_name": self.protocol_name, "interaction_type": self.interaction_type,
            "tx_hash": self.tx_hash, "user_address": self.user_address,
            "input_amount": str(self.input_amount), "input_token": self.input_token,
            "output_token": self.output_token, "timestamp": self.timestamp.to_iso(),
            "risk_score": self.risk_score,
        }


@dataclass(frozen=True, slots=True)
class NFTTransferRecord:
    """NFT transfer record with marketplace attribution."""

    nft_contract: str
    token_id: str
    nft_standard: str
    from_address: str
    to_address: str
    tx_hash: str
    timestamp: Timestamp
    price: Optional[PrecisionDecimal] = None
    currency: Optional[str] = None
    marketplace: Optional[str] = None
    is_fractionalized: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nft_contract": self.nft_contract, "token_id": self.token_id,
            "nft_standard": self.nft_standard, "tx_hash": self.tx_hash,
            "from": self.from_address, "to": self.to_address,
            "timestamp": self.timestamp.to_iso(),
            "price": str(self.price) if self.price else None,
            "marketplace": self.marketplace, "is_fractionalized": self.is_fractionalized,
        }


# ---------------------------------------------------------------------------
# Network graph models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NetworkNode:
    node_id: str
    entity_type: EntityType
    name: str
    aliases: Set[str] = field(default_factory=set)
    attributes: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    first_seen: Optional[Timestamp] = None
    last_seen: Optional[Timestamp] = None
    sources: Set[str] = field(default_factory=set)

    def __hash__(self) -> int:
        return hash(self.node_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id, "entity_type": self.entity_type.value,
            "name": self.name, "aliases": list(self.aliases),
            "attributes": self.attributes, "risk_score": self.risk_score,
            "first_seen": self.first_seen.to_iso() if self.first_seen else None,
            "last_seen": self.last_seen.to_iso() if self.last_seen else None,
            "sources": list(self.sources),
        }


@dataclass(frozen=True, slots=True)
class NetworkEdge:
    edge_id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    weight: float = 1.0
    attributes: Dict[str, Any] = field(default_factory=dict)
    first_seen: Optional[Timestamp] = None
    last_seen: Optional[Timestamp] = None
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id, "source_id": self.source_id,
            "target_id": self.target_id, "relationship_type": self.relationship_type.value,
            "weight": self.weight,
            "first_seen": self.first_seen.to_iso() if self.first_seen else None,
            "last_seen": self.last_seen.to_iso() if self.last_seen else None,
        }


# ---------------------------------------------------------------------------
# Patent model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PatentRecord:
    patent_id: str
    jurisdiction: Jurisdiction
    application_number: str
    publication_number: str
    title: str
    abstract: str
    claims: List[str] = field(default_factory=list)
    inventors: List[Dict[str, Any]] = field(default_factory=list)
    assignees: List[Dict[str, Any]] = field(default_factory=list)
    filing_date: Optional[Timestamp] = None
    publication_date: Optional[Timestamp] = None
    grant_date: Optional[Timestamp] = None
    status: PatentStatus = PatentStatus.PENDING
    classification: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    family_members: List[str] = field(default_factory=list)
    h_flag_score: float = 0.0
    synthetic_identity_risk: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patent_id": self.patent_id, "jurisdiction": self.jurisdiction.value,
            "application_number": self.application_number,
            "publication_number": self.publication_number,
            "title": self.title,
            "abstract": self.abstract[:500] + "..." if len(self.abstract) > 500 else self.abstract,
            "claims_count": len(self.claims), "inventors_count": len(self.inventors),
            "filing_date": self.filing_date.to_iso() if self.filing_date else None,
            "status": self.status.name,
            "h_flag_score": self.h_flag_score, "synthetic_identity_risk": self.synthetic_identity_risk,
        }


@dataclass(frozen=True, slots=True)
class LLCRecord:
    llc_id: str
    name: str
    jurisdiction: str
    registration_number: str
    formation_date: Optional[Timestamp] = None
    dissolution_date: Optional[Timestamp] = None
    status: str = "active"
    registered_agent: Optional[str] = None
    principal_address: Optional[str] = None
    members: List[Dict[str, Any]] = field(default_factory=list)
    managers: List[Dict[str, Any]] = field(default_factory=list)
    beneficial_owners: List[Dict[str, Any]] = field(default_factory=list)
    risk_score: float = 0.0
    shell_indicators: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "llc_id": self.llc_id, "name": self.name, "jurisdiction": self.jurisdiction,
            "status": self.status, "risk_score": self.risk_score,
            "shell_indicators": self.shell_indicators,
        }


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    event_id: str
    timestamp: Timestamp
    event_type: str
    description: str
    entities: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id, "timestamp": self.timestamp.to_iso(),
            "event_type": self.event_type, "description": self.description,
            "entities": self.entities,
        }


@dataclass(frozen=True, slots=True)
class APIResponse:
    success: bool
    data: Any = None
    error: Optional[str] = None
    status_code: int = 200
    timestamp: Timestamp = field(default_factory=Timestamp.now)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    latency_ms: float = 0.0
    rate_limit_remaining: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success, "data": self.data, "error": self.error,
            "status_code": self.status_code, "timestamp": self.timestamp.to_iso(),
            "latency_ms": self.latency_ms,
        }


@dataclass(frozen=True, slots=True)
class InvestigationResult:
    investigation_id: str
    timestamp: Timestamp
    entities: List[NetworkNode] = field(default_factory=list)
    relationships: List[NetworkEdge] = field(default_factory=list)
    transactions: List[Transaction] = field(default_factory=list)
    patents: List[PatentRecord] = field(default_factory=list)
    llcs: List[LLCRecord] = field(default_factory=list)
    timeline: List[TimelineEvent] = field(default_factory=list)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    evidence_metadata: List[EvidenceMetadata] = field(default_factory=list)
    wallet_entities: List[WalletEntity] = field(default_factory=list)
    bridge_transactions: List[CrossChainBridge] = field(default_factory=list)
    mixer_transactions: List[MixerTransaction] = field(default_factory=list)
    defi_interactions: List[DeFiInteraction] = field(default_factory=list)
    nft_transfers: List[NFTTransferRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "timestamp": self.timestamp.to_iso(),
            "entities_count": len(self.entities),
            "relationships_count": len(self.relationships),
            "transactions_count": len(self.transactions),
            "patents_count": len(self.patents),
            "llcs_count": len(self.llcs),
            "timeline_events_count": len(self.timeline),
            "wallet_entities_count": len(self.wallet_entities),
            "bridge_transactions_count": len(self.bridge_transactions),
            "mixer_transactions_count": len(self.mixer_transactions),
            "defi_interactions_count": len(self.defi_interactions),
            "nft_transfers_count": len(self.nft_transfers),
            "risk_assessment": self.risk_assessment,
        }
