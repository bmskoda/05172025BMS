"""Tests for temporal correlation engine, LCS diff, and evidence bag."""

import datetime
import json
import unittest
from decimal import Decimal

from aegis.engines.correlation import (
    CrossDomainCorrelator,
    LCSDiffDetector,
    TemporalWindow,
)
from aegis.models.core import (
    BlockchainAddress,
    PatentRecord,
    PrecisionDecimal,
    Timestamp,
    Transaction,
)
from aegis.constants import Jurisdiction
from aegis.reports.evidence import EvidenceChainBuilder, PostQuantumHasher


def _pat(patent_id: str, filing_ts: float) -> PatentRecord:
    return PatentRecord(
        patent_id=patent_id,
        jurisdiction=Jurisdiction.USPTO,
        application_number="APP",
        publication_number="PUB",
        title="T",
        abstract="A",
        filing_date=Timestamp(int(filing_ts * 1e9)),
    )


def _tx(tx_hash: str, ts: float) -> Transaction:
    return Transaction(
        tx_hash=tx_hash,
        network="ethereum",
        block_number=1,
        timestamp=Timestamp(int(ts * 1e9)),
        from_address=BlockchainAddress("0xA", "ethereum"),
        to_address=BlockchainAddress("0xB", "ethereum"),
        value=PrecisionDecimal(Decimal("1")),
    )


class TestTemporalWindow(unittest.TestCase):
    def test_contains(self):
        w = TemporalWindow(
            datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
            datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
        )
        inside = datetime.datetime(2022, 6, 1, tzinfo=datetime.timezone.utc)
        outside = datetime.datetime(2019, 1, 1, tzinfo=datetime.timezone.utc)
        self.assertTrue(w.contains(inside))
        self.assertFalse(w.contains(outside))

    def test_contains_naive(self):
        w = TemporalWindow()
        naive = datetime.datetime(2020, 1, 1)
        self.assertTrue(w.contains(naive))

    def test_to_dict(self):
        w = TemporalWindow()
        d = w.to_dict()
        self.assertIn("start", d)
        self.assertIn("end", d)


class TestCrossDomainCorrelator(unittest.TestCase):
    def test_exact_match(self):
        t = 1_700_000_000.0
        patents = [_pat("P1", t)]
        txns = [_tx("0xABC", t)]
        corr = CrossDomainCorrelator(correlation_window_seconds=1.0)
        results = corr.correlate(patents, txns)
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0]["delta_seconds"], 0.0, places=2)

    def test_within_window(self):
        t = 1_700_000_000.0
        patents = [_pat("P1", t)]
        txns = [_tx("0xABC", t + 0.5)]
        corr = CrossDomainCorrelator(correlation_window_seconds=1.0)
        results = corr.correlate(patents, txns)
        self.assertEqual(len(results), 1)

    def test_outside_window(self):
        t = 1_700_000_000.0
        patents = [_pat("P1", t)]
        txns = [_tx("0xABC", t + 5.0)]
        corr = CrossDomainCorrelator(correlation_window_seconds=1.0)
        results = corr.correlate(patents, txns)
        self.assertEqual(len(results), 0)

    def test_empty_inputs(self):
        corr = CrossDomainCorrelator()
        self.assertEqual(corr.correlate([], []), [])


class TestLCSDiffDetector(unittest.TestCase):
    def test_identical(self):
        r = LCSDiffDetector.detect_tampering("abc", "abc")
        self.assertFalse(r["tampered"])
        self.assertAlmostEqual(r["diff_ratio"], 0.0)

    def test_completely_different(self):
        r = LCSDiffDetector.detect_tampering("abc", "xyz")
        self.assertTrue(r["tampered"])
        self.assertAlmostEqual(r["diff_ratio"], 1.0)

    def test_minor_change(self):
        r = LCSDiffDetector.detect_tampering(
            "The quick brown fox", "The quick brown fox jumps"
        )
        self.assertGreater(r["diff_ratio"], 0.0)
        self.assertLess(r["diff_ratio"], 0.5)

    def test_empty_strings(self):
        r = LCSDiffDetector.detect_tampering("", "")
        self.assertFalse(r["tampered"])

    def test_lcs_basic(self):
        lcs = LCSDiffDetector.lcs("abcde", "ace")
        self.assertEqual(lcs, "ace")


class TestEvidenceBag(unittest.TestCase):
    def test_create_bag(self):
        ecb = EvidenceChainBuilder()
        from aegis.models.core import EvidenceMetadata
        ecb.add("case_bag", {"d": "test"}, EvidenceMetadata(evidence_id="e1"))
        bag = ecb.create_evidence_bag("case_bag")
        self.assertIn("bag_id", bag)
        self.assertEqual(bag["bag_version"], "AEGIS-EVIDENCE-BAG-V2")
        self.assertEqual(bag["evidence_count"], 1)
        self.assertIn("FRE 902(13)", bag["fre_compliance"])
        self.assertIn("chain_hash_sha3", bag)
        self.assertIn("blake2b_seal", bag)

    def test_bag_empty_case(self):
        ecb = EvidenceChainBuilder()
        bag = ecb.create_evidence_bag("nonexistent")
        self.assertEqual(bag["evidence_count"], 0)


if __name__ == "__main__":
    unittest.main()
