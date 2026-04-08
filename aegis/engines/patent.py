"""
Patent forensics engine.

H-FLAG backdating detection, synthetic-inventor identity scoring,
patent-family anomaly analysis, and ghost-docket identification.
"""

from __future__ import annotations

import re
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from aegis.api.manager import APIIntegrationManager
from aegis.config import UnifiedConfiguration
from aegis.constants import HFlagSeverity, Jurisdiction, PatentStatus
from aegis.models.core import PatentRecord, Timestamp
from aegis.utils import get_logger


# ---------------------------------------------------------------------------
# H-FLAG Backdating Detector
# ---------------------------------------------------------------------------


class HFlagDetector:
    """Identifies suspicious filing-date anomalies (weekend / holiday
    filings, rapid family expansions, improbable examiner timelines)."""

    _US_HOLIDAYS = {"01-01", "07-04", "11-11", "12-25"}

    def __init__(self) -> None:
        self._log = get_logger("Patent.HFlag")

    def score(self, patent: PatentRecord) -> float:
        if not patent.filing_date:
            return 0.0
        dt = patent.filing_date.to_datetime()
        s = 0.0
        if dt.weekday() >= 5:
            s += 0.15
        if dt.strftime("%m-%d") in self._US_HOLIDAYS:
            s += 0.20
        if len(patent.family_members) > 5:
            s += min(0.1 * (len(patent.family_members) - 5), 0.30)
        if len(patent.inventors) > 10:
            s += 0.10
        if len(patent.assignees) > 3:
            s += 0.10
        if patent.status == PatentStatus.ABANDONED:
            s += 0.10
        return min(s, 1.0)

    @staticmethod
    def severity(score: float) -> HFlagSeverity:
        if score >= 0.7:
            return HFlagSeverity.CRITICAL
        if score >= 0.5:
            return HFlagSeverity.HIGH
        if score >= 0.3:
            return HFlagSeverity.MEDIUM
        if score >= 0.1:
            return HFlagSeverity.LOW
        return HFlagSeverity.NONE


# ---------------------------------------------------------------------------
# Synthetic Inventor Identity Detector
# ---------------------------------------------------------------------------


class SyntheticIdentityDetector:
    """Flags fabricated inventor names by analysing character-repetition,
    geographic scatter, and cross-family inconsistencies."""

    def __init__(self) -> None:
        self._log = get_logger("Patent.SyntheticID")

    def score(self, patent: PatentRecord) -> float:
        if not patent.inventors:
            return 0.0
        s = 0.0
        for inv in patent.inventors:
            name = inv.get("name", "").lower()
            if len(set(name)) < len(name) * 0.5:
                s += 0.10
            if re.search(r"(.)\1{2,}", name):
                s += 0.05
            if len(name.split()) < 2:
                s += 0.10
        countries = {inv.get("country", "") for inv in patent.inventors if inv.get("country")}
        if len(countries) > 5:
            s += min(0.05 * (len(countries) - 5), 0.20)
        if len(patent.family_members) > 3:
            s += 0.10
        return min(s, 1.0)

    def analyze_network(self, patents: List[PatentRecord]) -> Dict[str, Any]:
        inv_pats: Dict[str, List[str]] = defaultdict(list)
        inv_coauth: Dict[str, Set[str]] = defaultdict(set)
        for p in patents:
            names = [i.get("name", "") for i in p.inventors]
            for n in names:
                inv_pats[n].append(p.patent_id)
                inv_coauth[n].update(x for x in names if x != n)
        suspicious = [
            {"inventor": n, "patent_count": len(ps), "coauthors": len(inv_coauth[n])}
            for n, ps in inv_pats.items()
            if len(ps) > 100
        ]
        return {
            "total_inventors": len(inv_pats),
            "suspicious_inventors": suspicious,
        }


# ---------------------------------------------------------------------------
# Ghost-docket detector
# ---------------------------------------------------------------------------


class GhostDocketDetector:
    """Flags dockets that appear in assignment records but have no
    corresponding prosecution history — indicative of stealth or
    fraudulent filings."""

    def __init__(self) -> None:
        self._log = get_logger("Patent.GhostDocket")

    async def detect(
        self, api_mgr: APIIntegrationManager, patent_ids: List[str]
    ) -> List[Dict[str, Any]]:
        ghosts: List[Dict[str, Any]] = []
        uspto = api_mgr.get_client("uspto")
        if not uspto:
            return ghosts
        for pid in patent_ids:
            assign_resp = await uspto.get_assignments(pid)
            doc_resp = await uspto.get_patent(pid)
            if assign_resp.success and not (doc_resp.success and doc_resp.data):
                ghosts.append({
                    "patent_id": pid,
                    "has_assignments": True,
                    "has_prosecution": False,
                    "risk": "ghost_docket",
                })
        self._log.info("Ghost-docket scan: %d ghosts in %d patents", len(ghosts), len(patent_ids))
        return ghosts


# ---------------------------------------------------------------------------
# USPTO file-wrapper H-flag & prosecution-timeline analyser
# ---------------------------------------------------------------------------


class FileWrapperAnalyzer:
    """Queries the USPTO Patent File Wrapper API to detect hold (H-flag)
    events, examiner changes, and prosecution-timeline anomalies."""

    def __init__(self) -> None:
        self._log = get_logger("Patent.FileWrapper")

    async def detect_h_flags(
        self, api_mgr: APIIntegrationManager, application_number: str
    ) -> Dict[str, Any]:
        """Search file-wrapper transactions for hold events."""
        cli = api_mgr.get_client("uspto_file_wrapper")
        if not cli:
            return {"has_h_flag": False, "transactions": [], "error": "client not configured"}
        resp = await cli.search(application_number)
        if not resp.success:
            return {"has_h_flag": False, "transactions": [], "error": resp.error}
        results = resp.data.get("results", []) if isinstance(resp.data, dict) else []
        h_flags = [r for r in results if "H" in str(r.get("transactionCode", "")).upper()]
        return {
            "application_number": application_number,
            "has_h_flag": len(h_flags) > 0,
            "h_flag_count": len(h_flags),
            "transaction_count": len(results),
            "transactions": results[:50],
        }

    async def analyze_prosecution_timeline(
        self, api_mgr: APIIntegrationManager, application_number: str
    ) -> Dict[str, Any]:
        """Analyze prosecution timeline for anomalies."""
        h_result = await self.detect_h_flags(api_mgr, application_number)
        transactions = h_result.get("transactions", [])
        anomalies: List[str] = []

        examiners: Set[str] = set()
        for txn in transactions:
            examiner = txn.get("examinerName", "")
            if examiner:
                examiners.add(examiner)
        if len(examiners) > 3:
            anomalies.append(f"excessive_examiner_changes:{len(examiners)}")

        if h_result.get("has_h_flag"):
            anomalies.append("h_flag_detected")

        return {
            "application_number": application_number,
            "transaction_count": len(transactions),
            "examiner_count": len(examiners),
            "anomalies": anomalies,
            "h_flag": h_result.get("has_h_flag", False),
        }


# ---------------------------------------------------------------------------
# Patent-family analyser
# ---------------------------------------------------------------------------


class PatentFamilyAnalyzer:
    def analyze(self, patents: List[PatentRecord]) -> Dict[str, Any]:
        if not patents:
            return {"error": "empty"}
        jurisdictions = list({p.jurisdiction.value for p in patents})
        dates = [p.filing_date for p in patents if p.filing_date]
        date_range = None
        if dates:
            mn, mx = min(dates), max(dates)
            date_range = {
                "earliest": mn.to_iso(),
                "latest": mx.to_iso(),
                "span_days": (mx.nanoseconds - mn.nanoseconds) / 1e9 / 86400,
            }
        inv_sets = [set(i.get("name", "") for i in p.inventors) for p in patents]
        overlap = 0.0
        pairs = 0
        for i in range(len(inv_sets)):
            for j in range(i + 1, len(inv_sets)):
                u = inv_sets[i] | inv_sets[j]
                if u:
                    overlap += len(inv_sets[i] & inv_sets[j]) / len(u)
                pairs += 1
        flags: List[str] = []
        if len(patents) > 50:
            flags.append("Unusually large family")
        if len(jurisdictions) > 20:
            flags.append("Extensive geographic coverage")
        return {
            "family_size": len(patents),
            "jurisdictions": jurisdictions,
            "filing_date_range": date_range,
            "inventor_overlap": overlap / pairs if pairs else 0.0,
            "suspicious_patterns": flags,
        }


# ---------------------------------------------------------------------------
# Composite patent engine
# ---------------------------------------------------------------------------


class PatentAnalysisEngine:
    def __init__(self, api_mgr: APIIntegrationManager, config: UnifiedConfiguration) -> None:
        self._api = api_mgr
        self._cfg = config
        self.h_flag = HFlagDetector()
        self.synth_id = SyntheticIdentityDetector()
        self.family = PatentFamilyAnalyzer()
        self.ghost = GhostDocketDetector()
        self._log = get_logger("Patent.Engine")

    async def search(
        self, query: str, jurisdiction: Optional[Jurisdiction] = None, limit: int = 100
    ) -> List[PatentRecord]:
        patents: List[PatentRecord] = []
        for name in ("uspto", "epo", "wipo"):
            if jurisdiction and name != jurisdiction.name.lower()[:4]:
                continue
            cli = self._api.get_client(name)
            if not cli:
                continue
            resp = await cli.search_patents(query, limit)
            if resp.success and resp.data:
                patents.extend(self._parse(resp.data, Jurisdiction[name.upper()] if name in ("uspto",) else Jurisdiction.EPO))
        self._log.info("Patent search '%s': %d results", query, len(patents))
        return patents

    def _parse(self, data: Dict[str, Any], jur: Jurisdiction) -> List[PatentRecord]:
        out: List[PatentRecord] = []
        items = data.get("results", data.get("patents", []))
        for item in items:
            try:
                p = PatentRecord(
                    patent_id=item.get("patent_id", str(uuid.uuid4())),
                    jurisdiction=jur,
                    application_number=item.get("application_number", ""),
                    publication_number=item.get("publication_number", ""),
                    title=item.get("title", ""),
                    abstract=item.get("abstract", ""),
                    claims=item.get("claims", []),
                    inventors=item.get("inventors", []),
                    assignees=item.get("assignees", []),
                    filing_date=self._ts(item.get("filing_date")),
                    publication_date=self._ts(item.get("publication_date")),
                    grant_date=self._ts(item.get("grant_date")),
                    classification=item.get("classification", []),
                    citations=item.get("citations", []),
                    family_members=item.get("family_members", []),
                )
                p = self._enrich(p)
                out.append(p)
            except Exception as exc:
                self._log.error("Patent parse error: %s", exc)
        return out

    def _enrich(self, p: PatentRecord) -> PatentRecord:
        return PatentRecord(
            patent_id=p.patent_id,
            jurisdiction=p.jurisdiction,
            application_number=p.application_number,
            publication_number=p.publication_number,
            title=p.title,
            abstract=p.abstract,
            claims=p.claims,
            inventors=p.inventors,
            assignees=p.assignees,
            filing_date=p.filing_date,
            publication_date=p.publication_date,
            grant_date=p.grant_date,
            status=p.status,
            classification=p.classification,
            citations=p.citations,
            family_members=p.family_members,
            h_flag_score=self.h_flag.score(p),
            synthetic_identity_risk=self.synth_id.score(p),
            metadata=p.metadata,
        )

    @staticmethod
    def _ts(s: Optional[str]) -> Optional[Timestamp]:
        if not s:
            return None
        try:
            return Timestamp.from_iso(s.replace("Z", "+00:00"))
        except Exception:
            return None

    async def analyze_family(self, patent_id: str) -> Dict[str, Any]:
        epo = self._api.get_client("epo")
        if not epo:
            return {"error": "EPO client not configured"}
        resp = await epo.get_patent_family(patent_id)
        if not resp.success:
            return {"error": resp.error}
        fam = self._parse(resp.data or {}, Jurisdiction.EPO)
        return self.family.analyze(fam)

    def detect_stolen(self, patents: List[PatentRecord], threshold: float = 0.7) -> List[PatentRecord]:
        return [p for p in patents if (p.h_flag_score + p.synthetic_identity_risk) / 2 >= threshold]
