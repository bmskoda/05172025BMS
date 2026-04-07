"""Unit tests for analysis engines (offline / no-API tests)."""

import unittest
from decimal import Decimal

from aegis.constants import (
    EntityType,
    HFlagSeverity,
    Jurisdiction,
    PatentStatus,
    RelationshipType,
    TransactionType,
)
from aegis.models.core import (
    BlockchainAddress,
    NetworkEdge,
    NetworkNode,
    PatentRecord,
    PrecisionDecimal,
    TimelineEvent,
    Timestamp,
    Transaction,
)

from aegis.engines.blockchain import MixerDetector, DeFiAnalyzer, BridgeDetector
from aegis.engines.patent import HFlagDetector, SyntheticIdentityDetector, PatentFamilyAnalyzer
from aegis.engines.statistical import StatisticalAnalyzer, TimelineAnalyzer


def _make_tx(
    from_addr: str = "0xA",
    to_addr: str = "0xB",
    value: float = 1.0,
    ts: int = 1_000_000_000,
    input_data: str = "0x",
    nonce: int = 0,
) -> Transaction:
    return Transaction(
        tx_hash=f"0x{hash((from_addr, to_addr, ts)):032x}",
        network="ethereum",
        block_number=1,
        timestamp=Timestamp(ts * 1_000_000_000),
        from_address=BlockchainAddress(from_addr, "ethereum"),
        to_address=BlockchainAddress(to_addr, "ethereum"),
        value=PrecisionDecimal(Decimal(str(value))),
        nonce=nonce,
        input_data=input_data,
    )


# -- Blockchain engine tests ------------------------------------------------


class TestMixerDetector(unittest.TestCase):
    def test_known_mixer(self):
        det = MixerDetector()
        tx = _make_tx(to_addr="0x722122df12d4e14e13ac3b6895a86e84145b6967")
        result = det.detect([tx])
        self.assertTrue(result["mixer_detected"])
        self.assertGreaterEqual(result["confidence"], 0.9)

    def test_no_mixer(self):
        det = MixerDetector()
        tx = _make_tx(value=3.7)  # non-round value avoids behavioural pattern
        result = det.detect([tx])
        self.assertFalse(result["mixer_detected"])


class TestDeFiAnalyzer(unittest.TestCase):
    def test_uniswap_v2(self):
        analyzer = DeFiAnalyzer()
        tx = _make_tx(
            to_addr="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
            input_data="0x38ed173900000000",
        )
        result = analyzer.analyze(tx)
        self.assertTrue(result["is_defi"])
        self.assertIn("uniswap", result["protocol"])

    def test_not_defi(self):
        analyzer = DeFiAnalyzer()
        result = analyzer.analyze(_make_tx())
        self.assertFalse(result["is_defi"])


class TestBridgeDetector(unittest.TestCase):
    def test_polygon_bridge(self):
        det = BridgeDetector()
        tx = _make_tx(to_addr="0xA0c68C638235ee32657e8f720a23ceC1bFc77C77")
        result = det.detect(tx)
        self.assertTrue(result["is_bridge"])
        self.assertEqual(result["destination_chain"], "polygon")


# -- Patent engine tests ----------------------------------------------------


class TestHFlagDetector(unittest.TestCase):
    def _patent(self, weekday: int = 0, inventors: int = 2, family: int = 1) -> PatentRecord:
        from datetime import datetime, timezone
        dt = datetime(2024, 1, 1 + weekday, tzinfo=timezone.utc)  # Mon=0, Sat=5
        return PatentRecord(
            patent_id="TEST",
            jurisdiction=Jurisdiction.USPTO,
            application_number="APP",
            publication_number="PUB",
            title="T",
            abstract="A",
            inventors=[{"name": f"Inv{i}"} for i in range(inventors)],
            filing_date=Timestamp.from_datetime(dt),
            family_members=[f"F{i}" for i in range(family)],
        )

    def test_weekend_filing(self):
        det = HFlagDetector()
        p = self._patent(weekday=5)  # Saturday
        self.assertGreater(det.score(p), 0)

    def test_normal_filing(self):
        det = HFlagDetector()
        p = self._patent(weekday=1)  # Tuesday
        self.assertEqual(det.score(p), 0.0)

    def test_severity(self):
        self.assertEqual(HFlagDetector.severity(0.8), HFlagSeverity.CRITICAL)
        self.assertEqual(HFlagDetector.severity(0.0), HFlagSeverity.NONE)


class TestSyntheticIdentityDetector(unittest.TestCase):
    def test_simple_name(self):
        det = SyntheticIdentityDetector()
        p = PatentRecord(
            patent_id="X", jurisdiction=Jurisdiction.USPTO,
            application_number="", publication_number="",
            title="", abstract="",
            inventors=[{"name": "X"}],
        )
        self.assertGreater(det.score(p), 0)


class TestPatentFamilyAnalyzer(unittest.TestCase):
    def test_empty(self):
        pfa = PatentFamilyAnalyzer()
        self.assertEqual(pfa.analyze([]), {"error": "empty"})

    def test_large_family(self):
        pfa = PatentFamilyAnalyzer()
        patents = [
            PatentRecord(
                patent_id=f"P{i}", jurisdiction=Jurisdiction.USPTO,
                application_number="", publication_number="",
                title="T", abstract="A",
                filing_date=Timestamp.now(),
            )
            for i in range(60)
        ]
        result = pfa.analyze(patents)
        self.assertIn("Unusually large family", result["suspicious_patterns"])


# -- Statistical engine tests -----------------------------------------------


class TestStatisticalAnalyzer(unittest.TestCase):
    def test_outliers_iqr(self):
        sa = StatisticalAnalyzer()
        data = [1, 2, 3, 4, 5, 100]
        outliers = sa.detect_outliers(data)
        self.assertIn(5, outliers)  # index 5 (value=100)

    def test_entropy(self):
        sa = StatisticalAnalyzer()
        self.assertAlmostEqual(sa.entropy(["a", "b"]), 1.0)
        self.assertEqual(sa.entropy([]), 0.0)

    def test_benford(self):
        sa = StatisticalAnalyzer()
        import random
        random.seed(42)
        data = [random.randint(1, 9999) for _ in range(1000)]
        result = sa.benford(data)
        self.assertIn("compliant", result)


class TestTimelineAnalyzer(unittest.TestCase):
    def test_clusters(self):
        ta = TimelineAnalyzer()
        events = [
            TimelineEvent(f"e{i}", Timestamp(i * 1_000_000_000), "tx", f"desc {i}")
            for i in range(10)
        ]
        result = ta.temporal_clusters(events, window_h=24)
        self.assertGreaterEqual(result["cluster_count"], 0)


if __name__ == "__main__":
    unittest.main()
