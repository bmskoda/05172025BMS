"""Tests for v27 capabilities: BLAKE2b hashing, domain investigation, substance tracing, file-wrapper analysis."""

import json
import unittest

from aegis.reports.evidence import PostQuantumHasher, EvidenceChainBuilder
from aegis.engines.domain_investigation import DomainInvestigator
from aegis.engines.substance_tracing import SubstanceTracer, PRIVACY_TOKEN_CONTRACTS
from aegis.engines.patent import FileWrapperAnalyzer
from aegis.models.core import EvidenceMetadata


class TestPostQuantumHasher(unittest.TestCase):
    def test_hash_bytes(self):
        h = PostQuantumHasher()
        digest = h.hash_bytes(b"hello world")
        self.assertEqual(len(digest), 128)  # 64 bytes hex = 128 chars

    def test_deterministic(self):
        h = PostQuantumHasher()
        self.assertEqual(h.hash_bytes(b"test"), h.hash_bytes(b"test"))

    def test_keyed_hash(self):
        h = PostQuantumHasher(key=b"secret")
        d1 = h.hash_bytes(b"data")
        h2 = PostQuantumHasher()
        d2 = h2.hash_bytes(b"data")
        self.assertNotEqual(d1, d2)

    def test_key_too_long(self):
        with self.assertRaises(ValueError):
            PostQuantumHasher(key=b"x" * 65)

    def test_type_error(self):
        h = PostQuantumHasher()
        with self.assertRaises(TypeError):
            h.hash_bytes("not bytes")

    def test_create_seal(self):
        h = PostQuantumHasher()
        seal = h.create_seal({"key": "value"})
        self.assertIn("data_hash", seal)
        self.assertIn("seal_hash", seal)
        self.assertIn("nonce", seal)
        self.assertIn("timestamp", seal)

    def test_verify_seal(self):
        h = PostQuantumHasher()
        seal = h.create_seal({"key": "value"})
        self.assertTrue(h.verify_seal(seal))

    def test_verify_seal_tampered(self):
        h = PostQuantumHasher()
        seal = h.create_seal({"key": "value"})
        seal["data_hash"] = "0" * 128
        self.assertFalse(h.verify_seal(seal))

    def test_verify_seal_missing_field(self):
        h = PostQuantumHasher()
        self.assertFalse(h.verify_seal({"data_hash": "abc"}))

    def test_chain_anchor(self):
        h = PostQuantumHasher()
        anchor = h.create_chain_anchor([{"a": 1}, {"b": 2}, {"c": 3}])
        self.assertIn("root_hash", anchor)
        self.assertEqual(anchor["leaf_count"], 3)
        self.assertEqual(anchor["algorithm"], "BLAKE2b-512")

    def test_chain_anchor_single(self):
        h = PostQuantumHasher()
        anchor = h.create_chain_anchor([{"x": 1}])
        self.assertEqual(anchor["leaf_count"], 1)

    def test_chain_anchor_empty(self):
        h = PostQuantumHasher()
        with self.assertRaises(ValueError):
            h.create_chain_anchor([])


class TestEvidenceChainBlake2b(unittest.TestCase):
    def test_add_includes_blake2b(self):
        ecb = EvidenceChainBuilder()
        meta = EvidenceMetadata(evidence_id="e1", investigator_id="a1")
        ecb.add("case1", {"data": "test"}, meta)
        chain = ecb._chains["case1"]
        self.assertIn("blake2b_hash", chain[0])
        self.assertEqual(len(chain[0]["blake2b_hash"]), 128)

    def test_create_seal(self):
        ecb = EvidenceChainBuilder()
        meta = EvidenceMetadata(evidence_id="e1")
        ecb.add("case2", {"x": 1}, meta)
        seal = ecb.create_seal("case2")
        self.assertIn("seal_hash", seal)

    def test_export_blake2b_in_verification(self):
        ecb = EvidenceChainBuilder()
        meta = EvidenceMetadata(evidence_id="e1")
        ecb.add("case3", {"x": 1}, meta)
        exported = json.loads(ecb.export("case3"))
        self.assertIn("blake2b_algorithm", exported["verification"])


class TestDomainInvestigator(unittest.TestCase):
    def test_estimate_damages(self):
        d = DomainInvestigator.estimate_damages("example.com")
        self.assertIn("total_estimated_damages_usd", d)
        self.assertGreater(d["total_estimated_damages_usd"], 0)
        self.assertEqual(d["domain"], "example.com")

    def test_estimate_damages_custom(self):
        d = DomainInvestigator.estimate_damages(
            "test.com", market_value=10000, monthly_traffic=50000,
            revenue_per_visit=0.50, years_stolen=5,
        )
        self.assertEqual(d["market_value_usd"], 10000)
        self.assertEqual(d["years_assumed"], 5)


class TestSubstanceTracer(unittest.TestCase):
    def test_privacy_token_db(self):
        self.assertIn("0x77777feddddffc19ff86db637967013e6c6a116c", PRIVACY_TOKEN_CONTRACTS)
        self.assertEqual(PRIVACY_TOKEN_CONTRACTS["0x77777feddddffc19ff86db637967013e6c6a116c"], "TORN")


class TestFileWrapperAnalyzer(unittest.TestCase):
    def test_instantiation(self):
        fwa = FileWrapperAnalyzer()
        self.assertIsNotNone(fwa)


if __name__ == "__main__":
    unittest.main()
