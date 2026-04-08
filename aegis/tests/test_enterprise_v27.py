"""Tests for SYSTEM AEGIS Enterprise v27 module."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import orjson
import pytest

from aegis.aegis_enterprise_v27 import (
    OMEGA_VERSION,
    CL_V4_ENDPOINTS,
    ComplianceConfig,
    CryptoVault,
    EvidenceChain,
    AsyncAPIGateway,
    CourtListenerV4Adapter,
    ProsecutionAnomalyEngine,
    BlockchainProfiler,
    SubstanceTraceEngine,
    AegisOrchestrator,
    ReportGenerator,
)


# ── EvidenceChain Pydantic model ────────────────────────────────────────


class TestEvidenceChain:
    def test_creation(self):
        item = EvidenceChain(
            item_id="EV-000001-ABCD",
            source="test",
            timestamp_utc="2026-01-01T00:00:00+00:00",
            category="unit_test",
            data_hash="a" * 128,
            prev_hash="b" * 128,
            chain_hash="c" * 128,
        )
        assert item.item_id == "EV-000001-ABCD"
        assert item.metadata == {}

    def test_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            EvidenceChain(
                item_id="EV-1",
                source="t",
                timestamp_utc="t",
                category="c",
                data_hash="h",
                prev_hash="p",
                chain_hash="ch",
                rogue_field="should_fail",
            )


# ── CryptoVault ─────────────────────────────────────────────────────────


class TestCryptoVault:
    def test_hash_payload_deterministic(self, tmp_path):
        vault = CryptoVault(evidence_dir=tmp_path)
        h1 = vault.hash_payload({"a": 1, "b": 2})
        h2 = vault.hash_payload({"b": 2, "a": 1})
        assert h1 == h2
        assert len(h1) == 128

    def test_keyed_hash_differs(self, tmp_path):
        v1 = CryptoVault(evidence_dir=tmp_path)
        v2 = CryptoVault(evidence_dir=tmp_path, key=b"secret_key_1234!")
        h1 = v1.hash_payload({"x": 1})
        h2 = v2.hash_payload({"x": 1})
        assert h1 != h2

    def test_append_and_verify(self, tmp_path):
        vault = CryptoVault(evidence_dir=tmp_path)
        item = vault.append("src", "cat", {"key": "value"})
        assert item.item_id.startswith("EV-")
        assert vault.verify() is True

    def test_chain_linkage(self, tmp_path):
        vault = CryptoVault(evidence_dir=tmp_path)
        i1 = vault.append("s1", "c1", {"a": 1})
        i2 = vault.append("s2", "c2", {"b": 2})
        genesis = hashlib.blake2b(
            CryptoVault.GENESIS_SEED, digest_size=64
        ).hexdigest()
        assert i1.prev_hash == genesis
        assert i2.prev_hash == i1.chain_hash

    def test_persistence_roundtrip(self, tmp_path):
        v1 = CryptoVault(evidence_dir=tmp_path)
        v1.append("s", "c", {"d": 1})
        v1.append("s", "c", {"d": 2})

        v2 = CryptoVault(evidence_dir=tmp_path)
        assert len(v2.items) == 2
        assert v2.verify() is True
        assert v2.prev_hash == v1.prev_hash

    def test_tamper_detection(self, tmp_path):
        vault = CryptoVault(evidence_dir=tmp_path)
        vault.append("s", "c", {"x": 1})
        vault.append("s", "c", {"y": 2})
        vault.items[0].data_hash = "0" * 128
        assert vault.verify() is False

    def test_empty_chain_verifies(self, tmp_path):
        vault = CryptoVault(evidence_dir=tmp_path)
        assert vault.verify() is True

    def test_merkle_anchor_single(self, tmp_path):
        vault = CryptoVault(evidence_dir=tmp_path)
        root = vault.create_merkle_anchor([{"a": 1}])
        assert len(root) == 128

    def test_merkle_anchor_multiple(self, tmp_path):
        vault = CryptoVault(evidence_dir=tmp_path)
        root = vault.create_merkle_anchor(
            [{"a": 1}, {"b": 2}, {"c": 3}]
        )
        assert len(root) == 128

    def test_merkle_anchor_deterministic(self, tmp_path):
        vault = CryptoVault(evidence_dir=tmp_path)
        batch = [{"x": i} for i in range(5)]
        r1 = vault.create_merkle_anchor(batch)
        r2 = vault.create_merkle_anchor(batch)
        assert r1 == r2

    def test_merkle_anchor_empty_raises(self, tmp_path):
        vault = CryptoVault(evidence_dir=tmp_path)
        with pytest.raises(ValueError, match="Empty batch"):
            vault.create_merkle_anchor([])

    def test_evidence_chain_json_schema(self, tmp_path):
        vault = CryptoVault(evidence_dir=tmp_path)
        vault.append("src", "cat", {"k": "v"})
        chain_file = tmp_path / "evidence_chain.json"
        assert chain_file.exists()
        data = orjson.loads(chain_file.read_bytes())
        assert data["version"] == OMEGA_VERSION
        assert data["chain_valid"] is True
        assert len(data["chain"]) == 1


# ── ComplianceConfig ────────────────────────────────────────────────────


class TestComplianceConfig:
    def test_constants(self):
        assert ComplianceConfig.HASH_ALGORITHM == "blake2b"
        assert ComplianceConfig.DIGEST_SIZE == 64
        assert ComplianceConfig.MAX_RETRIES == 3
        assert "courtlistener.com" in ComplianceConfig.RATE_LIMIT_PER_DOMAIN


# ── CL_V4_ENDPOINTS ────────────────────────────────────────────────────


class TestEndpoints:
    def test_endpoint_count(self):
        assert len(CL_V4_ENDPOINTS) == 11

    def test_all_v4_urls(self):
        for name, url in CL_V4_ENDPOINTS.items():
            assert "/api/rest/v4/" in url, f"{name} missing v4 path"

    def test_key_endpoints_present(self):
        required = {
            "search",
            "dockets",
            "opinions",
            "financial_disclosures",
            "investments",
            "citation_lookup",
        }
        assert required.issubset(CL_V4_ENDPOINTS.keys())


# ── Analysis engines ────────────────────────────────────────────────────


class TestProsecutionAnomalyEngine:
    @pytest.mark.asyncio
    async def test_analyze_application(self):
        engine = ProsecutionAnomalyEngine()
        result = await engine.analyze_application("16123456")
        assert result["application_number"] == "16123456"
        assert result["anomaly_score"] == 0.0


class TestBlockchainProfiler:
    @pytest.mark.asyncio
    async def test_profile_batch(self):
        profiler = BlockchainProfiler()
        results = await profiler.profile_batch(
            ["0xaaa", "0xbbb", "0xccc"]
        )
        assert len(results) == 3
        assert results[0]["address"] == "0xaaa"
        assert results[0]["risk_score"] == 0.0


class TestSubstanceTraceEngine:
    @pytest.mark.asyncio
    async def test_map_supply_chain(self):
        engine = SubstanceTraceEngine()
        result = await engine.map_supply_chain(["0xa", "0xb"])
        assert result["nodes"] == 2
        assert result["edges"] == 0


# ── ReportGenerator ─────────────────────────────────────────────────────


class TestReportGenerator:
    def _sample_results(self) -> Dict[str, Any]:
        return {
            "phase_30_post_quantum_anchor": {"merkle_root": "abc123"},
            "phase_31_blockchain_profiling": [
                {"address": "0x1", "role": "unknown", "risk_score": 0.0}
            ],
            "phase_32_prosecution_anomalies": {
                "application_number": "16123456",
                "anomaly_score": 0.0,
            },
            "_meta": {
                "version": OMEGA_VERSION,
                "elapsed_seconds": 1.23,
                "evidence_intact": True,
                "merkle_root": "a" * 128,
            },
        }

    def test_forensic_report_structure(self):
        gen = ReportGenerator(self._sample_results())
        report = gen.generate_forensic_report()
        assert "SYSTEM AEGIS v27" in report
        assert "EXECUTIVE SUMMARY" in report
        assert "FRE 902(13)-(14)" in report
        assert "VERIFIED" in report

    def test_forensic_report_tamper_detected(self):
        results = self._sample_results()
        results["_meta"]["evidence_intact"] = False
        gen = ReportGenerator(results)
        report = gen.generate_forensic_report()
        assert "TAMPER DETECTED" in report

    def test_forensic_report_phase_listing(self):
        gen = ReportGenerator(self._sample_results())
        report = gen.generate_forensic_report()
        assert "Phase 30" in report
        assert "COMPLETED" in report

    def test_forensic_report_failed_phase(self):
        results = self._sample_results()
        results["phase_99_broken"] = {"error": "something went wrong"}
        gen = ReportGenerator(results)
        report = gen.generate_forensic_report()
        assert "FAILED" in report

    def test_press_release_structure(self):
        gen = ReportGenerator(self._sample_results())
        press = gen.generate_press_release()
        assert "FOR IMMEDIATE RELEASE" in press
        assert "SYSTEM AEGIS v27" in press
        assert "CourtListener v4" in press
        assert "BLAKE2b" in press
        assert "NIST SP 800-53" in press
        assert "FRE 902(13)-(14)" in press


# ── AegisOrchestrator ───────────────────────────────────────────────────


class TestAegisOrchestrator:
    @pytest.mark.asyncio
    async def test_execute_offline(self, tmp_path):
        config = {
            "courtlistener_token": "",
            "etherscan_key": "",
            "evidence_dir": str(tmp_path),
        }
        orch = AegisOrchestrator(config)
        results = await orch.execute()
        assert "_meta" in results
        assert results["_meta"]["version"] == OMEGA_VERSION
        assert isinstance(results["_meta"]["elapsed_seconds"], float)

        assert "phase_30_post_quantum_anchor" in results
        assert "phase_31_blockchain_profiling" in results
        assert "phase_32_prosecution_anomalies" in results
        assert "phase_33_domain_investigation" in results
        assert "phase_34_substance_tracing" in results

    @pytest.mark.asyncio
    async def test_vault_integrity_after_execute(self, tmp_path):
        config = {
            "courtlistener_token": "",
            "etherscan_key": "",
            "evidence_dir": str(tmp_path),
        }
        orch = AegisOrchestrator(config)
        await orch.execute()
        assert orch.vault.verify() is True
        assert len(orch.vault.items) > 0


# ── Module-level checks ────────────────────────────────────────────────


class TestModuleLevel:
    def test_version_string(self):
        assert OMEGA_VERSION == "27.0.0.ENTERPRISE"

    def test_import_succeeds(self):
        from aegis import aegis_enterprise_v27

        assert aegis_enterprise_v27.__version__ == "27.0.0.ENTERPRISE"
