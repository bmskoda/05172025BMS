"""Tests for the AEGIS Forensic Report & Press Release Generator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aegis.reports.generator import (
    Finding,
    ForensicReportGenerator,
    ReportMetadata,
)


def _sample_findings() -> list[Finding]:
    return [
        Finding(
            category="Sanctions",
            severity="CRITICAL",
            title="OFAC-sanctioned address detected",
            description=(
                "Address 0xabc interacted with a Tornado Cash "
                "deposit contract listed on the OFAC SDN list."
            ),
            evidence_refs=["EVD-001", "EVD-002"],
            confidence=0.98,
            legal_citations=["31 CFR 501"],
        ),
        Finding(
            category="Mixer",
            severity="HIGH",
            title="Mixer interaction detected",
            description=(
                "Address 0xdef deposited 10 ETH into a known "
                "mixer contract."
            ),
            evidence_refs=["EVD-003"],
            confidence=0.92,
        ),
        Finding(
            category="Bridge",
            severity="MEDIUM",
            title="Cross-chain bridge transfer",
            description=(
                "5 ETH bridged from Ethereum to Arbitrum via "
                "Optimism Bridge."
            ),
            evidence_refs=["EVD-004"],
            confidence=0.85,
        ),
        Finding(
            category="NFT",
            severity="LOW",
            title="Potential wash trading",
            description=(
                "NFT #42 traded 8 times between 2 addresses "
                "in 24 hours."
            ),
            confidence=0.65,
        ),
    ]


class TestFinding:
    def test_auto_id(self):
        f = Finding(title="Test")
        assert f.finding_id.startswith("FND-")
        assert len(f.finding_id) == 16

    def test_explicit_id(self):
        f = Finding(finding_id="FND-CUSTOM", title="Test")
        assert f.finding_id == "FND-CUSTOM"


class TestReportMetadata:
    def test_auto_fields(self):
        m = ReportMetadata()
        assert m.report_id.startswith("RPT-")
        assert m.generated_at != ""
        assert m.temporal_scope_start == "1985-08-20"
        assert len(m.compliance_standards) >= 8

    def test_explicit_fields(self):
        m = ReportMetadata(
            report_id="RPT-TEST",
            investigation_id="INV-123",
        )
        assert m.report_id == "RPT-TEST"
        assert m.investigation_id == "INV-123"


class TestForensicReportGenerator:
    def test_generate_creates_three_files(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        findings = _sample_findings()
        result = gen.generate(
            findings=findings,
            data_sources=["Etherscan", "Chainalysis"],
            summary="Test investigation completed.",
        )
        assert result["json"].exists()
        assert result["html"].exists()
        assert result["press_release"].exists()

    def test_json_report_structure(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        result = gen.generate(
            findings=_sample_findings(),
            data_sources=["USPTO", "EPO"],
        )
        data = json.loads(result["json"].read_text())
        assert "report_metadata" in data
        assert "executive_summary" in data
        assert "methodology" in data
        assert "findings" in data
        assert "statistics" in data
        assert "integrity" in data

    def test_json_metadata_compliance(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        result = gen.generate(
            findings=_sample_findings(),
            data_sources=["Etherscan"],
        )
        data = json.loads(result["json"].read_text())
        meta = data["report_metadata"]
        assert meta["report_id"].startswith("RPT-")
        assert "FRE 902(13)" in meta["compliance_standards"]
        assert "NIST SP 800-86" in meta["compliance_standards"]
        assert "FBI CJIS v5.9.2" in meta["compliance_standards"]
        assert meta["temporal_scope_start"] == "1985-08-20"

    def test_json_integrity_hash(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        result = gen.generate(
            findings=_sample_findings(),
            data_sources=["Etherscan"],
        )
        data = json.loads(result["json"].read_text())
        assert data["integrity"]["content_hash_algorithm"] == "SHA3-512"
        assert len(data["integrity"]["content_hash"]) == 128

    def test_json_statistics(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        findings = _sample_findings()
        result = gen.generate(
            findings=findings,
            data_sources=["Etherscan"],
        )
        data = json.loads(result["json"].read_text())
        stats = data["statistics"]
        assert stats["total_findings"] == 4
        assert stats["by_severity"]["CRITICAL"] == 1
        assert stats["by_severity"]["HIGH"] == 1
        assert stats["by_severity"]["MEDIUM"] == 1
        assert stats["by_severity"]["LOW"] == 1
        assert stats["avg_confidence"] > 0

    def test_json_daubert_factors(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        result = gen.generate(
            findings=_sample_findings(),
            data_sources=["Etherscan"],
        )
        data = json.loads(result["json"].read_text())
        factors = data["methodology"]["daubert_factors"]
        assert len(factors) == 5
        assert any("Testability" in f for f in factors)
        assert any("General Acceptance" in f for f in factors)

    def test_html_contains_key_elements(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        result = gen.generate(
            findings=_sample_findings(),
            data_sources=["Etherscan"],
        )
        html = result["html"].read_text()
        assert "<!DOCTYPE html>" in html
        assert "Executive Summary" in html
        assert "Findings" in html
        assert "Methodology" in html
        assert "Compliance" in html
        assert "Integrity Verification" in html
        assert "SHA3-512" in html
        assert "CRITICAL" in html
        assert "OFAC-sanctioned" in html

    def test_press_release_structure(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        result = gen.generate(
            findings=_sample_findings(),
            data_sources=["Etherscan"],
        )
        text = result["press_release"].read_text()
        assert "FOR IMMEDIATE RELEASE" in text
        assert "Investigation ID" in text
        assert "SUMMARY" in text
        assert "KEY METRICS" in text
        assert "TOP FINDINGS" in text
        assert "METHODOLOGY" in text
        assert "COMPLIANCE" in text
        assert "INTEGRITY" in text
        assert "SHA3-512" in text

    def test_auto_summary(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        result = gen.generate(
            findings=_sample_findings(),
            data_sources=["Etherscan"],
        )
        data = json.loads(result["json"].read_text())
        assert "4 finding(s)" in data["executive_summary"]

    def test_custom_summary(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        result = gen.generate(
            findings=_sample_findings(),
            data_sources=["Etherscan"],
            summary="Custom summary text.",
        )
        data = json.loads(result["json"].read_text())
        assert data["executive_summary"] == "Custom summary text."

    def test_empty_findings(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        result = gen.generate(
            findings=[],
            data_sources=["Etherscan"],
        )
        data = json.loads(result["json"].read_text())
        assert data["statistics"]["total_findings"] == 0
        assert data["statistics"]["avg_confidence"] == 0.0

    def test_supplemental_metadata(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        result = gen.generate(
            findings=_sample_findings(),
            data_sources=["Etherscan"],
            extra_metadata={"custom_field": "value"},
        )
        data = json.loads(result["json"].read_text())
        assert data["supplemental"]["custom_field"] == "value"

    def test_investigation_id_propagation(self, tmp_path):
        gen = ForensicReportGenerator(output_dir=tmp_path)
        result = gen.generate(
            findings=_sample_findings(),
            data_sources=["Etherscan"],
            investigation_id="INV-TEST-999",
        )
        data = json.loads(result["json"].read_text())
        assert data["report_metadata"]["investigation_id"] == "INV-TEST-999"
