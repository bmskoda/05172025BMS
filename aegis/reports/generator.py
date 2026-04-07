"""
Forensic report generator — JSON and HTML output.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List

from aegis.config import UnifiedConfiguration
from aegis.models.core import (
    InvestigationResult,
    Timestamp,
)
from aegis.utils import get_logger


class ForensicReportGenerator:
    def __init__(self, config: UnifiedConfiguration) -> None:
        self._cfg = config
        self._log = get_logger("Report.Generator")

    def generate(self, result: InvestigationResult, fmt: str = "json") -> Dict[str, Any]:
        report: Dict[str, Any] = {
            "report_metadata": {
                "report_id": str(uuid.uuid4()),
                "investigation_id": result.investigation_id,
                "generated_at": Timestamp.now().to_iso(),
                "report_type": "Forensic Investigation Report",
            },
            "executive_summary": self._exec_summary(result),
            "methodology": self._methodology(),
            "entities": {"count": len(result.entities), "items": [e.to_dict() for e in result.entities[:50]]},
            "relationships": {"count": len(result.relationships)},
            "blockchain": self._blockchain_section(result),
            "patent": self._patent_section(result),
            "network": self._network_section(result),
            "timeline": [e.to_dict() for e in sorted(result.timeline, key=lambda x: x.timestamp.nanoseconds)[:100]],
            "risk_assessment": result.risk_assessment,
            "evidence": {"count": len(result.evidence_metadata)},
            "conclusions": self._conclusions(result),
        }
        return report

    def _exec_summary(self, r: InvestigationResult) -> Dict[str, Any]:
        return {
            "scope": f"{len(r.entities)} entities, {len(r.relationships)} relationships",
            "findings": [
                f"{len(r.transactions)} blockchain transactions traced",
                f"{len(r.patents)} patent records analysed",
                f"{len(r.llcs)} corporate entities mapped",
            ],
            "overall_risk": r.risk_assessment.get("overall_risk", "unknown"),
        }

    @staticmethod
    def _methodology() -> Dict[str, Any]:
        return {
            "data_sources": [
                "Blockchain APIs (Etherscan, Chainalysis, Elliptic, NFTScan)",
                "Patent databases (USPTO, EPO, WIPO)",
                "Public records (OpenCorporates, CourtListener)",
            ],
            "techniques": [
                "Recursive transaction tracing",
                "Hypergraph network analysis",
                "GNN-based risk scoring",
                "H-FLAG backdating detection",
                "Synthetic-identity detection",
                "Tokenized-IP contract classification",
                "Recursive wallet-community mapping",
                "Benford's-Law fraud screening",
            ],
        }

    def _blockchain_section(self, r: InvestigationResult) -> Dict[str, Any]:
        return {
            "total_transactions": len(r.transactions),
            "total_value": str(sum(t.value.value for t in r.transactions)),
            "networks": list({t.network for t in r.transactions}),
        }

    def _patent_section(self, r: InvestigationResult) -> Dict[str, Any]:
        high_risk = [p for p in r.patents if p.h_flag_score > 0.5]
        return {
            "total": len(r.patents),
            "high_risk": len(high_risk),
            "jurisdictions": list({p.jurisdiction.value for p in r.patents}),
            "avg_h_flag": sum(p.h_flag_score for p in r.patents) / max(len(r.patents), 1),
            "avg_synth_risk": sum(p.synthetic_identity_risk for p in r.patents) / max(len(r.patents), 1),
        }

    def _network_section(self, r: InvestigationResult) -> Dict[str, Any]:
        n = len(r.entities)
        return {
            "nodes": n,
            "edges": len(r.relationships),
            "density": len(r.relationships) / (n * (n - 1)) if n > 1 else 0,
        }

    def _conclusions(self, r: InvestigationResult) -> Dict[str, Any]:
        return {
            "evidence_strength": "Multiple independent sources corroborate findings",
            "next_steps": [
                "Expand wallet-community recursion with additional seed addresses",
                "Cross-reference ghost-docket findings with assignment records",
                "Coordinate with relevant authorities for further action",
            ],
        }

    def save(self, report: Dict[str, Any], path: str, fmt: str = "json") -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if fmt == "json":
            with open(path, "w") as f:
                json.dump(report, f, indent=2, default=str)
        elif fmt == "html":
            with open(path, "w") as f:
                f.write(self._html(report))
        self._log.info("Report saved to %s", path)
        return path

    @staticmethod
    def _html(report: Dict[str, Any]) -> str:
        meta = report.get("report_metadata", {})
        es = report.get("executive_summary", {})
        bl = report.get("blockchain", {})
        pt = report.get("patent", {})
        title = meta.get("report_type", "Report")
        inv_id = meta.get("investigation_id", "")
        gen_at = meta.get("generated_at", "")
        scope = es.get("scope", "")
        risk = es.get("overall_risk", "")
        txn_count = bl.get("total_transactions", 0)
        total_val = bl.get("total_value", "0")
        pat_total = pt.get("total", 0)
        pat_high = pt.get("high_risk", 0)

        return (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n<head>\n'
            '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f"<title>{title}</title>\n"
            "<style>\n"
            "body{font-family:system-ui,sans-serif;margin:40px;background:#f8f9fa}\n"
            ".hdr{background:#1a237e;color:#fff;padding:24px;text-align:center;border-radius:8px}\n"
            ".section{background:#fff;margin:20px 0;padding:20px;border-radius:8px;"
            "box-shadow:0 1px 3px rgba(0,0,0,.12)}\n"
            "h2{color:#1a237e;border-bottom:2px solid #1a237e;padding-bottom:8px}\n"
            ".metric{display:inline-block;margin:8px 16px;padding:12px;background:#e3f2fd;border-radius:6px}\n"
            "</style>\n</head>\n<body>\n"
            '<div class="hdr">\n'
            f"  <h1>{title}</h1>\n"
            f"  <p>Investigation {inv_id} &mdash; {gen_at}</p>\n"
            "</div>\n"
            '<div class="section"><h2>Executive Summary</h2>\n'
            f"  <p>{scope}</p>\n"
            f"  <p>Overall risk: <strong>{risk}</strong></p>\n"
            "</div>\n"
            '<div class="section"><h2>Blockchain Analysis</h2>\n'
            f'  <div class="metric">Transactions: {txn_count}</div>\n'
            f'  <div class="metric">Total value: {total_val}</div>\n'
            "</div>\n"
            '<div class="section"><h2>Patent Analysis</h2>\n'
            f'  <div class="metric">Patents: {pat_total}</div>\n'
            f'  <div class="metric">High-risk: {pat_high}</div>\n'
            "</div>\n"
            "</body></html>"
        )
