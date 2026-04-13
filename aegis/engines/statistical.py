"""
Statistical analysis utilities: outlier detection, Shannon entropy,
Benford's-Law fraud screening, and temporal-cluster analysis.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List

from aegis.models.core import TimelineEvent
from aegis.utils import get_logger


class StatisticalAnalyzer:

    def detect_outliers(self, values: List[float], method: str = "iqr") -> List[int]:
        if len(values) < 4:
            return []
        if method == "iqr":
            s = sorted(values)
            q1, q3 = s[len(s) // 4], s[3 * len(s) // 4]
            iqr = q3 - q1
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            return [i for i, v in enumerate(values) if v < lo or v > hi]
        if method == "zscore":
            mu = sum(values) / len(values)
            sd = (sum((v - mu) ** 2 for v in values) / len(values)) ** 0.5
            if sd == 0:
                return []
            return [i for i, v in enumerate(values) if abs(v - mu) / sd > 3]
        return []

    def entropy(self, values: List[Any]) -> float:
        if not values:
            return 0.0
        freq: Dict[Any, int] = defaultdict(int)
        for v in values:
            freq[v] += 1
        n = len(values)
        return -sum((c / n) * math.log2(c / n) for c in freq.values())

    def benford(self, values: List[int]) -> Dict[str, Any]:
        first = [int(str(abs(v))[0]) for v in values if v > 0]
        if not first:
            return {"error": "no valid values"}
        n = len(first)
        obs: Dict[int, int] = defaultdict(int)
        for d in first:
            obs[d] += 1
        expected = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
        chi2 = sum(
            ((obs.get(d, 0) - expected[d] * n) ** 2) / (expected[d] * n)
            for d in range(1, 10)
        )
        crit = 15.51  # chi-square critical value, df=8, alpha=0.05
        return {
            "compliant": chi2 < crit,
            "chi_square": chi2,
            "critical_value": crit,
            "fraud_risk": "HIGH" if chi2 > crit * 2 else "MEDIUM" if chi2 > crit else "LOW",
        }


class TimelineAnalyzer:

    def __init__(self) -> None:
        self._log = get_logger("Timeline")

    def temporal_clusters(
        self, events: List[TimelineEvent], window_h: float = 24.0
    ) -> Dict[str, Any]:
        if not events:
            return {"clusters": []}
        ordered = sorted(events, key=lambda e: e.timestamp.nanoseconds)
        clusters: List[List[TimelineEvent]] = []
        cur = [ordered[0]]
        for ev in ordered[1:]:
            gap = (ev.timestamp.nanoseconds - cur[-1].timestamp.nanoseconds) / 1e9 / 3600
            if gap <= window_h:
                cur.append(ev)
            else:
                if len(cur) > 1:
                    clusters.append(cur)
                cur = [ev]
        if len(cur) > 1:
            clusters.append(cur)
        suspicious = [
            {
                "count": len(c),
                "start": c[0].timestamp.to_iso(),
                "end": c[-1].timestamp.to_iso(),
            }
            for c in clusters
            if len(c) >= 5
        ]
        return {
            "cluster_count": len(clusters),
            "suspicious_patterns": suspicious,
        }

    def coordination(self, events: List[TimelineEvent]) -> Dict[str, Any]:
        by_entity: Dict[str, List[TimelineEvent]] = defaultdict(list)
        for ev in events:
            for eid in ev.entities:
                by_entity[eid].append(ev)
        patterns: List[Dict[str, Any]] = []
        entities = list(by_entity.keys())
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                sim = sum(
                    1
                    for e1 in by_entity[entities[i]]
                    for e2 in by_entity[entities[j]]
                    if abs(e1.timestamp.nanoseconds - e2.timestamp.nanoseconds) / 1e9 < 300
                )
                if sim >= 3:
                    patterns.append({
                        "entity_a": entities[i],
                        "entity_b": entities[j],
                        "simultaneous": sim,
                    })
        return {"coordination_detected": bool(patterns), "patterns": patterns}
