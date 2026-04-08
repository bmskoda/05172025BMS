"""Smoke tests for the AEGIS monolith module."""

from __future__ import annotations

import asyncio
import json
import pytest


class TestMonolithImport:
    """Verify the monolith module can be imported without errors."""

    def test_import_monolith(self):
        from aegis import aegis_monolith

        assert aegis_monolith.__version__ == "16.0.0-MONOLITH"

    def test_enums_exist(self):
        from aegis.aegis_monolith import (
            ComplianceLevel,
            EvidenceType,
            RiskLevel,
            BlockchainLayer,
            TransactionType,
            EntityType,
            RelationshipType,
            PrivacyProtocol,
            PatentStatus,
            Jurisdiction,
            HFlagSeverity,
            EvidenceGrade,
            NetworkPatternType,
            StateActorGroup,
            CartelOrganization,
            APIStatus,
        )

        assert ComplianceLevel.PEP8.value == "PEP8"
        assert RiskLevel.CRITICAL.value == 5
        assert BlockchainLayer.L1 is not None
        assert Jurisdiction.USPTO.value == "US"

    def test_precision_decimal(self):
        from aegis.aegis_monolith import PrecisionDecimal
        from decimal import Decimal

        a = PrecisionDecimal(Decimal("1.5"))
        b = PrecisionDecimal(Decimal("2.5"))
        c = a + b
        assert float(c.value) == pytest.approx(4.0, abs=0.01)

    def test_timestamp(self):
        from aegis.aegis_monolith import Timestamp

        ts = Timestamp.now()
        iso = ts.to_iso()
        assert "T" in iso

    def test_crypto_hash(self):
        from aegis.aegis_monolith import CryptoHash

        h = CryptoHash.compute("hello world")
        assert len(h.digest) == 128  # sha3_512 hex length
        assert h.verify("hello world") is True
        assert h.verify("different") is False

    def test_unified_configuration(self):
        from aegis.aegis_monolith import UnifiedConfiguration

        config = UnifiedConfiguration.from_environment()
        d = config.to_dict()
        assert "***REDACTED***" in d.values() or config.encryption_key == ""

    def test_validate_blockchain_address(self):
        from aegis.aegis_monolith import validate_blockchain_address

        assert validate_blockchain_address(
            "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            "ethereum",
        ) is True
        assert validate_blockchain_address("", "ethereum") is False
        assert validate_blockchain_address("invalid", "ethereum") is False

    def test_format_currency(self):
        from aegis.aegis_monolith import format_currency

        assert format_currency(1234.56, "USD").startswith("$")
        assert "BTC" not in format_currency(1.0, "USD")

    def test_chunk_list(self):
        from aegis.aegis_monolith import chunk_list

        chunks = chunk_list([1, 2, 3, 4, 5], 2)
        assert len(chunks) == 3
        assert chunks[0] == [1, 2]

    def test_evidence_metadata(self):
        from aegis.aegis_monolith import EvidenceMetadata

        meta = EvidenceMetadata()
        d = meta.to_dict()
        assert "evidence_id" in d
        assert "LAW ENFORCEMENT SENSITIVE" in d["classification"]

    def test_blockchain_address(self):
        from aegis.aegis_monolith import BlockchainAddress

        addr = BlockchainAddress(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            network="ethereum",
        )
        assert addr.to_dict()["network"] == "ethereum"

    def test_network_node(self):
        from aegis.aegis_monolith import NetworkNode, EntityType

        node = NetworkNode(
            node_id="test-1",
            entity_type=EntityType.INDIVIDUAL,
            name="John Doe",
        )
        assert node.to_dict()["name"] == "John Doe"

    def test_investigation_result(self):
        from aegis.aegis_monolith import InvestigationResult, Timestamp

        result = InvestigationResult(
            investigation_id="TEST-001",
            timestamp=Timestamp.now(),
        )
        d = result.to_dict()
        assert d["investigation_id"] == "TEST-001"

    def test_h_flag_detector(self):
        from aegis.aegis_monolith import (
            HFlagDetector,
            PatentRecord,
            Jurisdiction,
            PatentStatus,
        )

        detector = HFlagDetector()
        patent = PatentRecord(
            patent_id="P001",
            jurisdiction=Jurisdiction.USPTO,
            application_number="APP001",
            publication_number="PUB001",
            title="Test Patent",
            abstract="A test patent.",
            status=PatentStatus.PENDING,
        )
        score = detector.calculate_h_flag_score(patent)
        assert 0.0 <= score <= 1.0

    def test_statistical_analyzer_entropy(self):
        from aegis.aegis_monolith import StatisticalAnalyzer

        sa = StatisticalAnalyzer()
        entropy = sa.calculate_entropy(["a", "b", "a", "c"])
        assert entropy > 0

    def test_benford_analysis(self):
        from aegis.aegis_monolith import StatisticalAnalyzer
        import random

        sa = StatisticalAnalyzer()
        values = [random.randint(1, 99999) for _ in range(500)]
        result = sa.benford_analysis(values)
        assert "chi_square_statistic" in result
        assert "fraud_risk" in result

    def test_available_features_dict(self):
        from aegis.aegis_monolith import AVAILABLE_FEATURES

        assert isinstance(AVAILABLE_FEATURES, dict)
        assert "numpy" in AVAILABLE_FEATURES
