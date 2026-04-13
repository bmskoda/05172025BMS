"""Unit tests for aegis.utils."""

import unittest
from decimal import Decimal
from datetime import datetime, timezone

from aegis.utils import (
    validate_blockchain_address,
    format_currency,
    parse_timestamp,
    sanitize_filename,
    chunk_list,
    hash_evidence,
    generate_evidence_id,
    generate_case_number,
    PerformanceMonitor,
)
from aegis.models.core import Timestamp


class TestValidateAddress(unittest.TestCase):
    def test_eth_valid(self):
        self.assertTrue(
            validate_blockchain_address(
                "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEbD", "ethereum"
            )
        )

    def test_eth_invalid(self):
        self.assertFalse(validate_blockchain_address("not_an_address", "ethereum"))

    def test_btc_legacy(self):
        self.assertTrue(
            validate_blockchain_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin")
        )

    def test_btc_bech32(self):
        self.assertTrue(
            validate_blockchain_address(
                "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", "bitcoin"
            )
        )

    def test_empty(self):
        self.assertFalse(validate_blockchain_address("", "ethereum"))


class TestFormatCurrency(unittest.TestCase):
    def test_usd(self):
        self.assertEqual(format_currency(Decimal("1234.56")), "$1,234.56")

    def test_btc(self):
        result = format_currency(Decimal("0.001"), "BTC")
        self.assertIn("0.00100000", result)


class TestParseTimestamp(unittest.TestCase):
    def test_from_iso(self):
        ts = parse_timestamp("2024-01-01T00:00:00+00:00")
        self.assertIsInstance(ts, Timestamp)

    def test_from_unix(self):
        ts = parse_timestamp(1704067200)
        self.assertIsInstance(ts, Timestamp)

    def test_from_datetime(self):
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        ts = parse_timestamp(dt)
        self.assertIsInstance(ts, Timestamp)


class TestSanitizeFilename(unittest.TestCase):
    def test_removes_special(self):
        self.assertEqual(sanitize_filename('a<b>c:d"e'), "a_b_c_d_e")


class TestChunkList(unittest.TestCase):
    def test_even(self):
        self.assertEqual(chunk_list([1, 2, 3, 4], 2), [[1, 2], [3, 4]])

    def test_uneven(self):
        self.assertEqual(chunk_list([1, 2, 3], 2), [[1, 2], [3]])


class TestHashEvidence(unittest.TestCase):
    def test_dict(self):
        h = hash_evidence({"key": "value"})
        self.assertTrue(len(h.digest) > 0)


class TestGenerateIDs(unittest.TestCase):
    def test_evidence_id(self):
        eid = generate_evidence_id()
        self.assertTrue(eid.startswith("EVD-"))

    def test_case_number(self):
        cn = generate_case_number()
        self.assertTrue(cn.startswith("CASE-"))


class TestPerformanceMonitor(unittest.TestCase):
    def test_timer(self):
        pm = PerformanceMonitor()
        pm.start_timer("test")
        dur = pm.end_timer("test")
        self.assertGreaterEqual(dur, 0)

    def test_counter(self):
        pm = PerformanceMonitor()
        pm.increment_counter("ops", 5)
        summary = pm.get_summary()
        self.assertEqual(summary["counters"]["ops"], 5)


if __name__ == "__main__":
    unittest.main()
