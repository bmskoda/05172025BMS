"""Tests for the AEGIS Forensic Orchestration Engine."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from aegis.orchestrator.engine import (
    AgentManager,
    AgentRole,
    AgentState,
    CryptographicEvidenceChain,
    EvidenceRecord,
    ForensicOrchestrator,
    SecureAPIClient,
    StructuredJSONFormatter,
)


class TestEvidenceRecord:
    def test_hash_deterministic(self):
        r = EvidenceRecord(
            evidence_id="E1", source_system="TEST",
            endpoint_uri="/test", payload_hash="abc",
            previous_chain_hash=None,
            ingested_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
            chain_position=0,
        )
        h1 = r.compute_chain_hash()
        h2 = r.compute_chain_hash()
        assert h1 == h2
        assert len(h1) == 128  # SHA3-512 hex

    def test_hash_changes_with_content(self):
        r1 = EvidenceRecord(
            evidence_id="E1", source_system="A",
            endpoint_uri="/a", payload_hash="x",
            previous_chain_hash=None,
            ingested_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
            chain_position=0,
        )
        r2 = EvidenceRecord(
            evidence_id="E2", source_system="B",
            endpoint_uri="/b", payload_hash="y",
            previous_chain_hash=None,
            ingested_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
            chain_position=0,
        )
        assert r1.compute_chain_hash() != r2.compute_chain_hash()


class TestCryptographicEvidenceChain:
    def test_empty_chain_verifies(self):
        chain = CryptographicEvidenceChain()
        assert chain.verify() is True
        assert chain.length == 0

    def test_single_record_verifies(self):
        chain = CryptographicEvidenceChain()
        chain.append("TEST", "/api", {"key": "value"})
        assert chain.length == 1
        assert chain.verify() is True

    def test_multiple_records_verify(self):
        chain = CryptographicEvidenceChain()
        chain.append("SRC1", "/a", {"data": 1})
        chain.append("SRC2", "/b", {"data": 2})
        chain.append("SRC3", "/c", {"data": 3})
        assert chain.length == 3
        assert chain.verify() is True

    def test_chain_linkage(self):
        chain = CryptographicEvidenceChain()
        chain.append("A", "/1", {"x": 1})
        chain.append("B", "/2", {"x": 2})
        records = chain.records_as_dicts()
        assert records[0]["previous_chain_hash"] is None
        assert records[1]["previous_chain_hash"] is not None
        assert records[1]["chain_position"] == 1

    def test_export_structure(self):
        chain = CryptographicEvidenceChain()
        chain.append("TEST", "/api", {"k": "v"})
        exported = chain.export()
        assert "chain_of_custody" in exported
        assert "terminal_hash" in exported
        assert "chain_length" in exported
        assert "verification_status" in exported
        assert "standard_compliance" in exported
        assert exported["verification_status"] is True
        assert exported["chain_length"] == 1
        assert "NIST SP 800-86" in exported["standard_compliance"]
        assert "FRE 902(13)" in exported["standard_compliance"]

    def test_tamper_detection(self):
        chain = CryptographicEvidenceChain()
        chain.append("A", "/1", {"x": 1})
        chain.append("B", "/2", {"x": 2})
        # Tamper with internal state
        chain._head_hash = "tampered"
        assert chain.verify() is False


class TestAgentManager:
    @pytest.mark.asyncio
    async def test_initialize(self):
        mgr = AgentManager(pool_size=5)
        await mgr.initialize()
        assert len(mgr.pool) == 5
        assert all(
            s.status == "IDLE" for s in mgr.pool.values()
        )

    @pytest.mark.asyncio
    async def test_assign_and_complete(self):
        mgr = AgentManager(pool_size=5)
        await mgr.initialize()
        aid = await mgr.assign({"action": "test"})
        assert mgr.pool[aid].status == "PROCESSING"
        await mgr.complete(aid)
        assert mgr.pool[aid].status == "IDLE"
        assert mgr.pool[aid].tasks_completed == 1

    @pytest.mark.asyncio
    async def test_assign_by_role(self):
        mgr = AgentManager(pool_size=10)
        await mgr.initialize()
        aid = await mgr.assign(
            {"action": "ingest"},
            role=AgentRole.DATA_INGESTOR,
        )
        assert mgr.pool[aid].role == AgentRole.DATA_INGESTOR

    @pytest.mark.asyncio
    async def test_no_agent_available_raises(self):
        mgr = AgentManager(pool_size=1)
        await mgr.initialize()
        await mgr.assign({"action": "a"})
        with pytest.raises(RuntimeError, match="No idle agent"):
            await mgr.assign({"action": "b"})

    def test_summary(self):
        mgr = AgentManager(pool_size=6)
        s = mgr.summary()
        assert s["pool_size"] == 6
        assert "by_role" in s


class TestSecureAPIClient:
    def test_instantiation(self):
        client = SecureAPIClient(timeout_seconds=10)
        assert client._timeout_seconds == 10
        assert client._max_retries == 4


class TestStructuredJSONFormatter:
    def test_format_produces_json(self):
        import logging
        fmt = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="test.py", lineno=1,
            msg="hello", args=(), exc_info=None,
        )
        output = fmt.format(record)
        data = json.loads(output)
        assert data["message"] == "hello"
        assert data["level"] == "INFO"
        assert "timestamp" in data


class TestForensicOrchestrator:
    def test_instantiation(self, tmp_path):
        orch = ForensicOrchestrator(output_dir=tmp_path)
        assert orch.chain.length == 0
        assert orch.output_dir == tmp_path

    @pytest.mark.asyncio
    async def test_full_pipeline(self, tmp_path):
        orch = ForensicOrchestrator(
            output_dir=tmp_path, agent_pool_size=5,
        )
        result = await orch.run(target="TEST_TARGET")

        assert result["target"] == "TEST_TARGET"
        assert result["chain_verified"] is True
        assert result["evidence_records"] >= 1
        assert len(result["phases"]) == 4

        # Verify files written
        assert (tmp_path / "court_package.json").exists()
        assert (tmp_path / "forensic_report.txt").exists()
        assert (tmp_path / "press_release.txt").exists()

    @pytest.mark.asyncio
    async def test_court_package_structure(self, tmp_path):
        orch = ForensicOrchestrator(
            output_dir=tmp_path, agent_pool_size=10,
        )
        orch.chain.append("TEST", "/test", {"k": "v"})
        await orch.run()
        data = json.loads(
            (tmp_path / "court_package.json").read_text()
        )
        assert "investigation_id" in data
        assert data["investigation_id"].startswith("RICO-")
        assert "chain_of_custody" in data
        assert data["compliance_attestation"][
            "chain_integrity"
        ] == "VERIFIED"
        stds = data["compliance_attestation"]["standards_met"]
        assert "NIST SP 800-53 Rev 5" in stds
        assert "ISO 27037:2012" in stds
        assert "FRE 902(13)-(14)" in stds

    @pytest.mark.asyncio
    async def test_forensic_report_content(self, tmp_path):
        orch = ForensicOrchestrator(
            output_dir=tmp_path, agent_pool_size=10,
        )
        orch.chain.append("TEST", "/test", {"k": "v"})
        await orch.run(target="IP_ANALYSIS")
        report = (tmp_path / "forensic_report.txt").read_text()
        assert "OFFICIAL FORENSIC INVESTIGATION" in report
        assert "EXECUTIVE SUMMARY" in report
        assert "METHODOLOGY" in report
        assert "FINDINGS" in report
        assert "RECOMMENDATIONS" in report
        assert "CERTIFICATION" in report
        assert "IP_ANALYSIS" in report
        assert "SHA3-512" in report
        assert "ISO 27037" in report

    @pytest.mark.asyncio
    async def test_press_release_content(self, tmp_path):
        orch = ForensicOrchestrator(
            output_dir=tmp_path, agent_pool_size=10,
        )
        orch.chain.append("TEST", "/test", {"k": "v"})
        await orch.run()
        press = (tmp_path / "press_release.txt").read_text()
        assert "FOR IMMEDIATE RELEASE" in press
        assert "DEPARTMENT OF JUSTICE" in press
        assert "KEY INVESTIGATIVE COMPONENTS" in press
        assert "NEXT STEPS" in press
        assert "VERIFIED" in press
        assert "SHA3-512" in press
