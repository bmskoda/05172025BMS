"""Unit tests for aegis.models.core dataclasses."""

import time
import unittest
from decimal import Decimal

from aegis.models.core import (
    BlockchainAddress,
    CryptoHash,
    EvidenceMetadata,
    InvestigationResult,
    LLCRecord,
    NetworkEdge,
    NetworkNode,
    PatentRecord,
    PrecisionDecimal,
    TimelineEvent,
    Timestamp,
    Transaction,
    APIResponse,
)
from aegis.constants import (
    EntityType,
    EvidenceType,
    Jurisdiction,
    PatentStatus,
    RelationshipType,
    TransactionType,
)


class TestPrecisionDecimal(unittest.TestCase):
    def test_arithmetic(self):
        a = PrecisionDecimal(Decimal("1.5"))
        b = PrecisionDecimal(Decimal("2.5"))
        self.assertEqual(float(a + b), 4.0)
        self.assertEqual(float(b - a), 1.0)

    def test_division_by_zero(self):
        a = PrecisionDecimal(Decimal("1"))
        b = PrecisionDecimal(Decimal("0"))
        with self.assertRaises(ZeroDivisionError):
            _ = a / b


class TestTimestamp(unittest.TestCase):
    def test_now(self):
        ts = Timestamp.now()
        self.assertGreater(ts.nanoseconds, 0)

    def test_iso_round_trip(self):
        ts = Timestamp.now()
        iso = ts.to_iso()
        restored = Timestamp.from_iso(iso)
        self.assertAlmostEqual(ts.nanoseconds, restored.nanoseconds, delta=1_000_000_000)

    def test_ordering(self):
        a = Timestamp(1)
        b = Timestamp(2)
        self.assertTrue(a < b)
        self.assertTrue(b > a)


class TestCryptoHash(unittest.TestCase):
    def test_compute_and_verify(self):
        h = CryptoHash.compute("hello world")
        self.assertTrue(h.verify("hello world"))
        self.assertFalse(h.verify("hello_world"))

    def test_deterministic(self):
        h1 = CryptoHash.compute("data")
        h2 = CryptoHash.compute("data")
        self.assertEqual(h1.digest, h2.digest)


class TestBlockchainAddress(unittest.TestCase):
    def test_equality_case_insensitive(self):
        a = BlockchainAddress(address="0xABC", network="ethereum")
        b = BlockchainAddress(address="0xabc", network="Ethereum")
        self.assertEqual(a, b)

    def test_to_dict(self):
        a = BlockchainAddress(address="0xABC", network="ethereum")
        d = a.to_dict()
        self.assertEqual(d["address"], "0xABC")


class TestTransaction(unittest.TestCase):
    def test_to_dict(self):
        tx = Transaction(
            tx_hash="0x123",
            network="ethereum",
            block_number=1,
            timestamp=Timestamp.now(),
            from_address=BlockchainAddress("0xA", "ethereum"),
            to_address=BlockchainAddress("0xB", "ethereum"),
            value=PrecisionDecimal(Decimal("1.0")),
        )
        d = tx.to_dict()
        self.assertEqual(d["tx_hash"], "0x123")
        self.assertEqual(d["network"], "ethereum")


class TestNetworkNode(unittest.TestCase):
    def test_hash_by_id(self):
        a = NetworkNode("id1", EntityType.INDIVIDUAL, "Alice")
        b = NetworkNode("id1", EntityType.CORPORATION, "Bob Corp")
        self.assertEqual(hash(a), hash(b))


class TestPatentRecord(unittest.TestCase):
    def test_to_dict(self):
        p = PatentRecord(
            patent_id="US123",
            jurisdiction=Jurisdiction.USPTO,
            application_number="APP1",
            publication_number="PUB1",
            title="Widget",
            abstract="A widget",
        )
        d = p.to_dict()
        self.assertEqual(d["patent_id"], "US123")
        self.assertEqual(d["jurisdiction"], "US")


class TestEvidenceMetadata(unittest.TestCase):
    def test_custody_chain(self):
        m = EvidenceMetadata()
        m.add_custody_entry("collected", "agent-1")
        self.assertEqual(len(m.chain_of_custody), 1)
        self.assertEqual(m.chain_of_custody[0]["actor"], "agent-1")


class TestInvestigationResult(unittest.TestCase):
    def test_empty(self):
        r = InvestigationResult(investigation_id="X", timestamp=Timestamp.now())
        d = r.to_dict()
        self.assertEqual(d["entities_count"], 0)


class TestAPIResponse(unittest.TestCase):
    def test_success(self):
        r = APIResponse(success=True, data={"key": "value"})
        self.assertTrue(r.success)
        self.assertEqual(r.data["key"], "value")


if __name__ == "__main__":
    unittest.main()
