"""Tests for the new engines: known-addresses, risk scoring, NFT, monitoring, evidence."""

import asyncio
import unittest
from decimal import Decimal

from aegis.constants import RiskLevel, PrivacyProtocol
from aegis.engines.known_addresses import (
    BLOCKCHAIN_NETWORKS,
    KNOWN_BRIDGES,
    KNOWN_DEFI,
    KNOWN_MIXERS,
    OFAC_SANCTIONED,
    NFT_MARKETPLACES,
    FRACTIONALIZATION_PROTOCOLS,
    METHOD_SIGNATURES,
    BRIDGE_DESTINATION,
)
from aegis.engines.risk_scoring import RiskScorer
from aegis.engines.nft_tracker import NFTTracker
from aegis.engines.monitoring import BlockchainMonitor
from aegis.reports.evidence import EvidenceChainBuilder
from aegis.models.core import (
    BlockchainAddress,
    EvidenceMetadata,
    PrecisionDecimal,
    Timestamp,
    Transaction,
)


def _tx(
    frm: str = "0xaaa",
    to: str = "0xbbb",
    value: float = 1.5,
    network: str = "ethereum",
    input_data: str = "0x",
) -> Transaction:
    return Transaction(
        tx_hash=f"0x{hash((frm, to)):032x}",
        network=network,
        block_number=1,
        timestamp=Timestamp.now(),
        from_address=BlockchainAddress(frm, network),
        to_address=BlockchainAddress(to, network),
        value=PrecisionDecimal(Decimal(str(value))),
        input_data=input_data,
    )


class TestKnownAddresses(unittest.TestCase):
    def test_network_count(self):
        self.assertGreaterEqual(len(BLOCKCHAIN_NETWORKS), 30)

    def test_ofac_has_ethereum(self):
        self.assertGreater(len(OFAC_SANCTIONED["ethereum"]), 10)

    def test_mixers_lower(self):
        for net, addrs in KNOWN_MIXERS.items():
            for a in addrs:
                self.assertEqual(a, a.lower(), f"Mixer addr not lowercase: {a}")

    def test_bridges_have_destinations(self):
        for name in KNOWN_BRIDGES.get("ethereum", {}):
            if name in BRIDGE_DESTINATION:
                self.assertIsInstance(BRIDGE_DESTINATION[name], str)

    def test_method_sigs(self):
        self.assertIn("0xa9059cbb", METHOD_SIGNATURES)
        self.assertEqual(METHOD_SIGNATURES["0xa9059cbb"], "transfer")


class TestRiskScorer(unittest.TestCase):
    def test_sanctioned_address(self):
        scorer = RiskScorer()
        tx = _tx(to="0x722122df12d4e14e13ac3b6895a86e84145b6967")
        result = scorer.score_transaction(tx)
        self.assertTrue(result["is_sanctioned"])
        self.assertEqual(result["risk_score"], 1.0)

    def test_mixer_address(self):
        scorer = RiskScorer()
        tx = _tx(to="0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3")
        result = scorer.score_transaction(tx)
        self.assertTrue(result["is_mixer"])
        self.assertGreaterEqual(result["risk_score"], 0.9)

    def test_clean_address(self):
        scorer = RiskScorer()
        tx = _tx(frm="0xaaa", to="0xbbb", value=0.5)
        result = scorer.score_transaction(tx)
        self.assertFalse(result["is_sanctioned"])
        self.assertFalse(result["is_mixer"])

    def test_large_amount(self):
        scorer = RiskScorer()
        tx = _tx(value=2_000_000)
        result = scorer.score_transaction(tx)
        self.assertIn("very_large_amount", result["factors"])

    def test_method_detection(self):
        scorer = RiskScorer()
        tx = _tx(input_data="0xa9059cbb0000000000000000")
        result = scorer.score_transaction(tx)
        self.assertEqual(result["method"], "transfer")

    def test_level_mapping(self):
        scorer = RiskScorer()
        self.assertEqual(scorer._level(0.95), RiskLevel.CRITICAL)
        self.assertEqual(scorer._level(0.75), RiskLevel.HIGH)
        self.assertEqual(scorer._level(0.55), RiskLevel.MEDIUM)
        self.assertEqual(scorer._level(0.35), RiskLevel.LOW)
        self.assertEqual(scorer._level(0.1), RiskLevel.MINIMAL)


class TestEvidenceChainBuilder(unittest.TestCase):
    def test_add_and_verify(self):
        ecb = EvidenceChainBuilder()
        meta1 = EvidenceMetadata(evidence_id="e1", investigator_id="agent1")
        meta2 = EvidenceMetadata(evidence_id="e2", investigator_id="agent1")
        ecb.add("case1", {"data": "first"}, meta1)
        ecb.add("case1", {"data": "second"}, meta2)
        v = ecb.verify("case1")
        self.assertTrue(v["valid"])
        self.assertEqual(v["length"], 2)

    def test_export_contains_merkle(self):
        ecb = EvidenceChainBuilder()
        meta = EvidenceMetadata(evidence_id="e1")
        ecb.add("case2", {"x": 1}, meta)
        exported = ecb.export("case2")
        import json
        d = json.loads(exported)
        self.assertIn("merkle_root", d)
        self.assertGreater(len(d["merkle_root"]), 0)

    def test_hash_chain_linkage(self):
        ecb = EvidenceChainBuilder()
        for i in range(5):
            meta = EvidenceMetadata(evidence_id=f"e{i}")
            ecb.add("case3", {"idx": i}, meta)
        chain = ecb._chains["case3"]
        for i in range(1, len(chain)):
            self.assertEqual(chain[i]["previous_hash"], chain[i - 1]["hash"])


class TestNFTTracker(unittest.TestCase):
    def test_wash_trading_zero_for_few(self):
        score = NFTTracker._wash_trading_score([{"from": "a", "to": "b"}])
        self.assertEqual(score, 0.0)

    def test_wash_trading_detected(self):
        transfers = [{"from": "a", "to": "b"}] * 5
        score = NFTTracker._wash_trading_score(transfers)
        self.assertGreater(score, 0)

    def test_trading_analysis_empty(self):
        result = NFTTracker._trading_analysis([])
        self.assertEqual(result["num_sales"], 0)

    def test_risk_score_calculation(self):
        transfers = [{"from": "a", "to": "b"}] * 15
        wash = NFTTracker._wash_trading_score(transfers)
        risk = NFTTracker._risk_score(transfers, wash)
        self.assertGreater(risk, 0)
        self.assertLessEqual(risk, 1.0)

    def test_fractionalization_check(self):
        result = NFTTracker._check_fractionalization(
            "0x3f05de786e00f2741fb0c6ffde9c1b5e4b2e1d6b", "ethereum"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["protocol"], "fractional")


class TestBlockchainMonitor(unittest.TestCase):
    def test_init(self):
        scorer = RiskScorer()
        mon = BlockchainMonitor(scorer, monitored_addresses={"0xAAA"})
        self.assertIn("0xaaa", mon.monitored)
        self.assertEqual(mon.stats["alerts"], 0)


if __name__ == "__main__":
    unittest.main()
