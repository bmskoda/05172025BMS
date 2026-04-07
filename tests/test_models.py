"""Unit tests for aegis.models.core dataclasses."""

import unittest
from decimal import Decimal

from aegis.models.core import (
    BlockchainAddress,
    CrossChainBridge,
    CryptoHash,
    DeFiInteraction,
    EvidenceMetadata,
    InvestigationResult,
    LLCRecord,
    MixerTransaction,
    NetworkEdge,
    NetworkNode,
    NFTTransferRecord,
    PatentRecord,
    PrecisionDecimal,
    TimelineEvent,
    Timestamp,
    Transaction,
    WalletEntity,
    APIResponse,
)
from aegis.constants import (
    EntityType,
    EvidenceType,
    Jurisdiction,
    PatentStatus,
    PrivacyProtocol,
    RelationshipType,
    RiskLevel,
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

    def test_from_epoch(self):
        ts = Timestamp.from_epoch(1704067200)
        self.assertIsInstance(ts, Timestamp)
        ts_ms = Timestamp.from_epoch(1704067200000)
        self.assertAlmostEqual(ts.nanoseconds, ts_ms.nanoseconds, delta=1_000_000_000)


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
            tx_hash="0x123", network="ethereum", block_number=1,
            timestamp=Timestamp.now(),
            from_address=BlockchainAddress("0xA", "ethereum"),
            to_address=BlockchainAddress("0xB", "ethereum"),
            value=PrecisionDecimal(Decimal("1.0")),
        )
        d = tx.to_dict()
        self.assertEqual(d["tx_hash"], "0x123")
        self.assertIn("is_sanctioned", d)
        self.assertIn("risk_level", d)


class TestWalletEntity(unittest.TestCase):
    def test_to_dict(self):
        w = WalletEntity(address="0xABC", blockchain="ethereum")
        d = w.to_dict()
        self.assertEqual(d["address"], "0xABC")
        self.assertEqual(d["entity_type"], EntityType.UNKNOWN.value)

    def test_mutable(self):
        w = WalletEntity(address="0xABC", blockchain="ethereum")
        w.risk_score = 0.9
        w.tags.append("exchange")
        self.assertEqual(w.risk_score, 0.9)
        self.assertIn("exchange", w.tags)


class TestCrossChainBridge(unittest.TestCase):
    def test_to_dict(self):
        b = CrossChainBridge(
            bridge_name="polygon", source_chain="ethereum", target_chain="polygon",
            deposit_tx="0x1", withdrawal_tx=None, depositor="0xA", recipient=None,
            amount=PrecisionDecimal(Decimal("10")), token="ETH",
            timestamp=Timestamp.now(),
        )
        d = b.to_dict()
        self.assertEqual(d["bridge_name"], "polygon")


class TestMixerTransaction(unittest.TestCase):
    def test_to_dict(self):
        m = MixerTransaction(
            mixer_name="tornado", mixer_protocol=PrivacyProtocol.TORNADO_CASH,
            deposit_tx="0x1", withdrawal_tx=None, depositor="0xA", recipient=None,
            amount=PrecisionDecimal(Decimal("1")), currency="ETH",
            timestamp=Timestamp.now(),
        )
        self.assertEqual(m.to_dict()["mixer_protocol"], "TORNADO_CASH")


class TestDeFiInteraction(unittest.TestCase):
    def test_to_dict(self):
        d = DeFiInteraction(
            protocol_name="uniswap", interaction_type="swap", tx_hash="0x1",
            user_address="0xA", contract_address="0xB",
            input_amount=PrecisionDecimal(Decimal("100")),
            output_amount=PrecisionDecimal(Decimal("99")),
            input_token="USDC", output_token="ETH",
            timestamp=Timestamp.now(),
            gas_cost=PrecisionDecimal(Decimal("0.01")),
        )
        self.assertEqual(d.to_dict()["protocol_name"], "uniswap")


class TestNFTTransferRecord(unittest.TestCase):
    def test_to_dict(self):
        n = NFTTransferRecord(
            nft_contract="0xNFT", token_id="42", nft_standard="ERC721",
            from_address="0xA", to_address="0xB", tx_hash="0x1",
            timestamp=Timestamp.now(),
        )
        self.assertEqual(n.to_dict()["token_id"], "42")


class TestNetworkNode(unittest.TestCase):
    def test_hash_by_id(self):
        a = NetworkNode("id1", EntityType.INDIVIDUAL, "Alice")
        b = NetworkNode("id1", EntityType.CORPORATION, "Bob Corp")
        self.assertEqual(hash(a), hash(b))


class TestPatentRecord(unittest.TestCase):
    def test_to_dict(self):
        p = PatentRecord(
            patent_id="US123", jurisdiction=Jurisdiction.USPTO,
            application_number="APP1", publication_number="PUB1",
            title="Widget", abstract="A widget",
        )
        d = p.to_dict()
        self.assertEqual(d["patent_id"], "US123")


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
        self.assertEqual(d["wallet_entities_count"], 0)
        self.assertEqual(d["bridge_transactions_count"], 0)
        self.assertEqual(d["nft_transfers_count"], 0)


class TestAPIResponse(unittest.TestCase):
    def test_success(self):
        r = APIResponse(success=True, data={"key": "value"})
        self.assertTrue(r.success)
        self.assertEqual(r.data["key"], "value")


if __name__ == "__main__":
    unittest.main()
