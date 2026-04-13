"""
Cross-domain temporal correlation engine.

Finds nanosecond-aligned events between patent amendments and blockchain
transactions using a configurable sliding-window algorithm.  All timestamps
are normalised to UTC and bounded by a configurable temporal epoch.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Tuple

from aegis.models.core import PatentRecord, Timestamp, Transaction
from aegis.utils import get_logger

DEFAULT_EPOCH_START = datetime.datetime(1985, 8, 20, tzinfo=datetime.timezone.utc)
DEFAULT_EPOCH_END = datetime.datetime(2026, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)


class TemporalWindow:
    """Enforces a bounding epoch on all ingested data."""

    def __init__(
        self,
        start: datetime.datetime = DEFAULT_EPOCH_START,
        end: datetime.datetime = DEFAULT_EPOCH_END,
    ) -> None:
        self.start = start
        self.end = end

    def contains(self, dt: datetime.datetime) -> bool:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return self.start <= dt <= self.end

    def contains_ts(self, ts: Timestamp) -> bool:
        return self.contains(ts.to_datetime())

    def to_dict(self) -> Dict[str, str]:
        return {"start": self.start.isoformat(), "end": self.end.isoformat()}


class CrossDomainCorrelator:
    """Finds temporal correlations between patent events and blockchain
    transactions with configurable window precision."""

    def __init__(
        self,
        window: Optional[TemporalWindow] = None,
        correlation_window_seconds: float = 1.0,
    ) -> None:
        self._window = window or TemporalWindow()
        self._corr_window = correlation_window_seconds
        self._log = get_logger("Correlation")

    def correlate(
        self,
        patents: List[PatentRecord],
        transactions: List[Transaction],
    ) -> List[Dict[str, Any]]:
        """Return a list of (patent, transaction) pairs whose timestamps
        fall within ``correlation_window_seconds`` of each other."""

        pat_dated = [
            (p, p.filing_date.to_datetime())
            for p in patents
            if p.filing_date and self._window.contains_ts(p.filing_date)
        ]
        tx_dated = [
            (t, t.timestamp.to_datetime())
            for t in transactions
            if self._window.contains_ts(t.timestamp)
        ]

        pat_dated.sort(key=lambda x: x[1])
        tx_dated.sort(key=lambda x: x[1])

        results: List[Dict[str, Any]] = []
        pi = 0
        for tx, tx_dt in tx_dated:
            while pi > 0 and (tx_dt - pat_dated[pi - 1][1]).total_seconds() <= self._corr_window:
                pi -= 1
            while pi < len(pat_dated):
                pat, pat_dt = pat_dated[pi]
                delta = (tx_dt - pat_dt).total_seconds()
                if delta > self._corr_window:
                    break
                if abs(delta) <= self._corr_window:
                    results.append({
                        "patent_id": pat.patent_id,
                        "patent_jurisdiction": pat.jurisdiction.value,
                        "patent_ts": pat_dt.isoformat(),
                        "tx_hash": tx.tx_hash,
                        "tx_network": tx.network,
                        "tx_ts": tx_dt.isoformat(),
                        "delta_seconds": delta,
                        "delta_nanoseconds": delta * 1e9,
                    })
                pi += 1

        self._log.info(
            "Correlation complete: %d pairs (window=%.3fs, %d patents, %d txns)",
            len(results), self._corr_window, len(pat_dated), len(tx_dated),
        )
        return results


class LCSDiffDetector:
    """Computes Longest Common Subsequence between two strings and reports
    the diff — used to detect unauthorised changes in patent file-wrapper
    text across snapshots."""

    @staticmethod
    def lcs(seq1: str, seq2: str) -> str:
        m, n = len(seq1), len(seq2)
        dp = [[""] * (n + 1) for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                if seq1[i] == seq2[j]:
                    dp[i + 1][j + 1] = dp[i][j] + seq1[i]
                else:
                    dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j], key=len)
        return dp[m][n]

    @classmethod
    def diff_ratio(cls, before: str, after: str) -> float:
        """Return 0.0 (identical) to 1.0 (completely different)."""
        if not before and not after:
            return 0.0
        common = cls.lcs(before, after)
        max_len = max(len(before), len(after))
        return 1.0 - (len(common) / max_len) if max_len else 0.0

    @classmethod
    def detect_tampering(cls, before: str, after: str, threshold: float = 0.05) -> Dict[str, Any]:
        ratio = cls.diff_ratio(before, after)
        return {
            "tampered": ratio > threshold,
            "diff_ratio": ratio,
            "lcs_length": len(cls.lcs(before, after)),
            "before_length": len(before),
            "after_length": len(after),
            "threshold": threshold,
        }
