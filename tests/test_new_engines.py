"""Tests for engines: known-addresses, risk scoring, NFT, monitoring, evidence, blockchain enrichment."""

import asyncio
import json
import unittest
from decimal import Decimal

from aegis.constants import PrivacyProtocol, RiskLevel
from aegis.engines.known_addresses import (
    BLOCKCHAIN_NETWORKS, KNOWN_BRIDGES, KNOWN_DEFI, KNOWN_MIXERS,
    OFAC_SANCTIONED, NFT_MARKETPLACES, FRACTIONALIZATION_PROTOCOLS,
    METHOD_SIGNATURES, BRIDGE_DESTINATION,
)
from aegis.engines.risk_scoring import RiskScorer
from aegis.engines.nft_tracker import NFTTracker
from aegis.engines.monitoring import BlockchainMonitor
from aegis.engines.blockchain import TransactionTracer
from aegis.reports.evidence import EvidenceChainBuilder
from aegis.models.core import (
    BlockchainAddress, EvidenceMetadata, PrecisionDecimal, Timestamp, Transaction,
)


def _tx(frm="0xaaa", to="0xbbb", value=1.5, network="ethereum", input_data="0x", depth=0):
    return Transaction(
        tx_hash=f"0x{hash((frm, to, value)):032x}", network=network, block_number=1,
        timestamp=Timestamp.now(),
        from_address=BlockchainAddress(frm, network),
        to_address=BlockchainAddress(to, network),
        value=PrecisionDecimal(Decimal(str(value))),
        input_data=input_data, trace_depth=depth,
    )


class TestKnownAddresses(unittest.TestCase):
    def test_network_count(self):
        self.assertGreaterEqual(len(BLOCKCHAIN_NETWORKS), 30)

    def test_ofac_has_ethereum(self):
        self.assertGreater(len(OFAC_SANCTIONED["ethereum"]), 10)

    def test_mixers_lower(self):
        for net, addrs in KNOWN_MIXERS.items():
            for a in addrs:
                self.assertEqual(a, a.lower(), f"Not lowercase: {a}")

    def test_bridges_have_destinations(self):
        for name in KNOWN_BRIDGES.get("ethereum", {}):
            if name in BRIDGE_DESTINATION:
                self.assertIsInstance(BRIDGE_DESTINATION[name], str)

    def test_method_sigs(self):
        self.assertIn("0xa9059cbb", METHOD_SIGNATURES)
        self.assertEqual(METHOD_SIGNATURES["0xa9059cbb"], "transfer")

    def test_defi_multichain(self):
        self.assertIn("ethereum", KNOWN_DEFI["aave_v3"])
        self.assertIn("polygon", KNOWN_DEFI["aave_v3"])

    def test_nft_marketplaces(self):
        self.assertIn("opensea", NFT_MARKETPLACES.get("ethereum", {}))


class TestRiskScorer(unittest.TestCase):
    def test_sanctioned(self):
        s = RiskScorer()
        r = s.score_transaction(_tx(to="0x722122df12d4e14e13ac3b6895a86e84145b6967"))
        self.assertTrue(r["is_sanctioned"])
        self.assertEqual(r["risk_score"], 1.0)

    def test_mixer(self):
        s = RiskScorer()
        r = s.score_transaction(_tx(to="0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3"))
        self.assertTrue(r["is_mixer"])
        self.assertGreaterEqual(r["risk_score"], 0.9)

    def test_clean(self):
        s = RiskScorer()
        r = s.score_transaction(_tx(frm="0xaaa", to="0xbbb", value=0.5))
        self.assertFalse(r["is_sanctioned"])
        self.assertFalse(r["is_mixer"])

    def test_large_amount(self):
        s = RiskScorer()
        r = s.score_transaction(_tx(value=2_000_000))
        self.assertIn("very_large_amount", r["factors"])

    def test_method_detection(self):
        s = RiskScorer()
        r = s.score_transaction(_tx(input_data="0xa9059cbb0000000000000000"))
        self.assertEqual(r["method"], "transfer")

    def test_flash_loan_risk(self):
        s = RiskScorer()
        r = s.score_transaction(_tx(input_data="0x5b41b908" + "00" * 28))
        self.assertIn("flash_loan_risk", r["factors"])

    def test_round_amount(self):
        s = RiskScorer()
        r = s.score_transaction(_tx(value=100))
        self.assertIn("round_amount", r["factors"])

    def test_level_mapping(self):
        s = RiskScorer()
        self.assertEqual(s._level(0.95), RiskLevel.CRITICAL)
        self.assertEqual(s._level(0.75), RiskLevel.HIGH)
        self.assertEqual(s._level(0.55), RiskLevel.MEDIUM)
        self.assertEqual(s._level(0.35), RiskLevel.LOW)
        self.assertEqual(s._level(0.1), RiskLevel.MINIMAL)


class TestBlockchainEnrichment(unittest.TestCase):
    def test_enrich_sanctioned(self):
        tx = _tx(to="0x722122df12d4e14e13ac3b6895a86e84145b6967")
        enriched = TransactionTracer._enrich_inline(tx)
        self.assertTrue(enriched.is_sanctioned)
        self.assertGreaterEqual(enriched.risk_score, 0.9)

    def test_enrich_bridge(self):
        tx = _tx(to="0x99c9fc46f92e8a1c0dec1b1747d010903e884be1")
        enriched = TransactionTracer._enrich_inline(tx)
        self.assertTrue(enriched.is_bridge)
        self.assertIsNotNone(enriched.bridge_info)
        self.assertEqual(enriched.bridge_info["destination"], "optimism")

    def test_enrich_defi(self):
        tx = _tx(to="0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2")
        enriched = TransactionTracer._enrich_inline(tx)
        self.assertTrue(enriched.is_defi)
        self.assertEqual(enriched.defi_info["protocol"], "aave_v3")

    def test_enrich_clean(self):
        tx = _tx()
        enriched = TransactionTracer._enrich_inline(tx)
        self.assertFalse(enriched.is_sanctioned)
        self.assertFalse(enriched.is_mixer)


class TestEvidenceChainBuilder(unittest.TestCase):
    def test_add_and_verify(self):
        ecb = EvidenceChainBuilder()
        ecb.add("case1", {"d": "first"}, EvidenceMetadata(evidence_id="e1", investigator_id="a1"))
        ecb.add("case1", {"d": "second"}, EvidenceMetadata(evidence_id="e2", investigator_id="a1"))
        v = ecb.verify("case1")
        self.assertTrue(v["valid"])
        self.assertEqual(v["length"], 2)

    def test_export_merkle(self):
        ecb = EvidenceChainBuilder()
        ecb.add("c", {"x": 1}, EvidenceMetadata(evidence_id="e1"))
        d = json.loads(ecb.export("c"))
        self.assertIn("merkle_root", d)
        self.assertGreater(len(d["merkle_root"]), 0)

    def test_hash_chain(self):
        ecb = EvidenceChainBuilder()
        for i in range(5):
            ecb.add("c3", {"i": i}, EvidenceMetadata(evidence_id=f"e{i}"))
        chain = ecb._chains["c3"]
        for i in range(1, len(chain)):
            self.assertEqual(chain[i]["previous_hash"], chain[i - 1]["hash"])

    def test_export_verification_section(self):
        ecb = EvidenceChainBuilder()
        ecb.add("c4", {"a": 1}, EvidenceMetadata(evidence_id="e0"))
        d = json.loads(ecb.export("c4"))
        self.assertIn("verification", d)
        self.assertIn("hash_algorithm", d["verification"])


class TestNFTTracker(unittest.TestCase):
    def test_wash_zero_few(self):
        self.assertEqual(NFTTracker._wash_trading_score([{"from": "a", "to": "b"}]), 0.0)

    def test_wash_detected(self):
        self.assertGreater(NFTTracker._wash_trading_score([{"from": "a", "to": "b"}] * 5), 0)

    def test_trading_empty(self):
        self.assertEqual(NFTTracker._trading_analysis([])["num_sales"], 0)

    def test_risk(self):
        t = [{"from": "a", "to": "b"}] * 15
        self.assertGreater(NFTTracker._risk_score(t, NFTTracker._wash_trading_score(t)), 0)
        self.assertLessEqual(NFTTracker._risk_score(t, NFTTracker._wash_trading_score(t)), 1.0)

    def test_frac_check(self):
        r = NFTTracker._check_fractionalization("0x3f05de786e00f2741fb0c6ffde9c1b5e4b2e1d6b", "ethereum")
        self.assertIsNotNone(r)
        self.assertEqual(r["protocol"], "fractional")


class TestBlockchainMonitor(unittest.TestCase):
    def test_init(self):
        mon = BlockchainMonitor(RiskScorer(), monitored_addresses={"0xAAA"})
        self.assertIn("0xaaa", mon.monitored)

    def test_classify_sanctioned(self):
        mon = BlockchainMonitor(RiskScorer())
        self.assertEqual(
            mon.classify_alert("0x722122df12d4e14e13ac3b6895a86e84145b6967", "ethereum"),
            "SANCTIONED_ADDRESS",
        )

    def test_classify_mixer(self):
        mon = BlockchainMonitor(RiskScorer())
        self.assertEqual(
            mon.classify_alert("0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3", "ethereum"),
            "MIXER_TRANSACTION",
        )


if __name__ == "__main__":
    unittest.main()
