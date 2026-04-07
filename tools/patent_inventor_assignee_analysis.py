#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patent inventor vs assignee cross-check (US-focused records).

This tool helps find patent/application rows where a specified person appears
among inventors but does not appear among assignees *as represented in your
input data*.

IMPORTANT:
- Inventor-without-assignee is common and lawful (e.g., employer assignment,
  later-recorded assignments, different naming conventions). It is not evidence
  of USPTO record tampering or any internal USPTO flag by itself.
- Official USPTO systems and bulk products must be consulted for authoritative
  inventorship, ownership, and assignment status.

Official references (documentation only; this script does not call APIs):
- USPTO Open Data Portal: https://data.uspto.gov
- Patent Examination Data System (PEDS): https://developer.uspto.gov/api-catalog/peds-api
- USPTO Open Data API (api.uspto.gov): https://developer.uspto.gov/api-catalog
- Patent assignment search (bulk + web): https://assignment.uspto.gov/
- Patent Center (prosecution/file history): https://patentcenter.uspto.gov/

Input: JSON array of objects with keys compatible with the sample schema.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def normalize_person_name(name: str) -> str:
    """Normalize a person name for loose matching."""
    s = name.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[.,]", "", s)
    return s


def iter_inventor_names(inventors: Sequence[Dict[str, Any]]) -> Iterable[str]:
    for inv in inventors:
        n = inv.get("name") or inv.get("inventor_name") or ""
        if isinstance(n, str) and n.strip():
            yield n.strip()


def iter_assignee_names(assignees: Sequence[Dict[str, Any]]) -> Iterable[str]:
    for a in assignees:
        # Organization or individual assignee fields vary by export
        for key in ("name", "assignee_name", "organization", "assignee_organization"):
            n = a.get(key)
            if isinstance(n, str) and n.strip():
                yield n.strip()


@dataclass
class MatchResult:
    patent_id: str
    application_number: str
    publication_number: str
    victim_normalized: str
    victim_found_as_inventor: bool
    victim_found_as_assignee: bool
    inventors: List[str] = field(default_factory=list)
    assignees: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patent_id": self.patent_id,
            "application_number": self.application_number,
            "publication_number": self.publication_number,
            "victim_normalized": self.victim_normalized,
            "victim_found_as_inventor": self.victim_found_as_inventor,
            "victim_found_as_assignee": self.victim_found_as_assignee,
            "inventor_not_assignee_in_input": (
                self.victim_found_as_inventor and not self.victim_found_as_assignee
            ),
            "inventors": self.inventors,
            "assignees": self.assignees,
            "notes": self.notes,
        }


def person_matches_target(person_name: str, target: str) -> bool:
    pn = normalize_person_name(person_name)
    tn = normalize_person_name(target)
    if not pn or not tn:
        return False
    if pn == tn:
        return True
    # Last resort: token subset (handles "Smith, John" vs "John Smith")
    pt, tt = set(pn.split()), set(tn.split())
    if len(pt) >= 2 and len(tt) >= 2 and pt == tt:
        return True
    return False


def analyze_records(
    records: Sequence[Dict[str, Any]],
    victim_name: str,
) -> Tuple[List[MatchResult], Dict[str, Any]]:
    """
    For each record, determine if victim appears as inventor but not assignee
    in the provided snapshot.
    """
    flagged: List[MatchResult] = []
    stats = {"total": 0, "victim_as_inventor": 0, "inventor_not_assignee": 0}

    for row in records:
        stats["total"] += 1
        inventors = row.get("inventors") or []
        assignees = row.get("assignees") or []
        if not isinstance(inventors, list):
            inventors = []
        if not isinstance(assignees, list):
            assignees = []

        inv_names = list(iter_inventor_names(inventors))
        asn_names = list(iter_assignee_names(assignees))

        victim_inv = any(person_matches_target(n, victim_name) for n in inv_names)
        victim_asn = any(person_matches_target(n, victim_name) for n in asn_names)

        if victim_inv:
            stats["victim_as_inventor"] += 1

        notes: List[str] = []
        if victim_inv and not victim_asn:
            stats["inventor_not_assignee"] += 1
            notes.append(
                "In this input snapshot, the target person is listed as inventor "
                "but not among assignee name fields. Verify assignment records in "
                "USPTO assignment data and the prosecution file history; this "
                "pattern alone is not proof of misconduct."
            )

        if victim_inv and not victim_asn:
            flagged.append(
                MatchResult(
                    patent_id=str(row.get("patent_id", "")),
                    application_number=str(row.get("application_number", "")),
                    publication_number=str(row.get("publication_number", "")),
                    victim_normalized=normalize_person_name(victim_name),
                    victim_found_as_inventor=victim_inv,
                    victim_found_as_assignee=victim_asn,
                    inventors=inv_names,
                    assignees=asn_names,
                    notes=notes,
                )
            )

    return flagged, stats


def load_json(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict) and "patents" in data and isinstance(data["patents"], list):
        return [x for x in data["patents"] if isinstance(x, dict)]
    raise ValueError("JSON must be a list of patent objects or { 'patents': [ ... ] }")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Find records where a person appears as inventor but not assignee "
            "in your JSON export (informational; not legal or forensic proof)."
        )
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to JSON file (see sample in data/sample_patents.json)",
    )
    parser.add_argument(
        "--victim",
        "-v",
        required=True,
        help='Person name to match (e.g., "Jane Q. Inventor")',
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Write JSON report to this path (default: stdout)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    records = load_json(args.input)
    flagged, stats = analyze_records(records, args.victim)

    report = {
        "disclaimer": (
            "Results depend entirely on your input file. They do not access "
            "USPTO live systems, prove record tampering, or map to any internal "
            "USPTO flag."
        ),
        "official_uspto_data_pointers": {
            "open_data_portal": "https://data.uspto.gov",
            "developer_catalog": "https://developer.uspto.gov/api-catalog",
            "peds_api": "https://developer.uspto.gov/api-catalog/peds-api",
            "assignment_search": "https://assignment.uspto.gov/",
            "patent_center": "https://patentcenter.uspto.gov/",
        },
        "victim_query": args.victim,
        "statistics": stats,
        "matches_inventor_not_assignee_in_input": [m.to_dict() for m in flagged],
    }

    out_json = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out_json, encoding="utf-8")
    else:
        print(out_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
