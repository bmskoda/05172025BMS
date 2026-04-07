"""Unit tests for configuration and API layer."""

import os
import unittest

from aegis.config import UnifiedConfiguration


class TestUnifiedConfiguration(unittest.TestCase):
    def test_defaults(self):
        c = UnifiedConfiguration()
        self.assertEqual(c.log_level, "INFO")
        self.assertEqual(c.max_workers, 256)
        self.assertEqual(c.retry_attempts, 5)

    def test_from_environment(self):
        os.environ["AEGIS_LOG_LEVEL"] = "DEBUG"
        os.environ["AEGIS_MAX_WORKERS"] = "32"
        c = UnifiedConfiguration.from_environment()
        self.assertEqual(c.log_level, "DEBUG")
        self.assertEqual(c.max_workers, 32)
        os.environ.pop("AEGIS_LOG_LEVEL", None)
        os.environ.pop("AEGIS_MAX_WORKERS", None)

    def test_to_dict_redacts_keys(self):
        c = UnifiedConfiguration()
        c.etherscan_api_key = "secret123"
        d = c.to_dict()
        self.assertEqual(d["etherscan_api_key"], "***REDACTED***")

    def test_to_dict_shows_non_sensitive(self):
        c = UnifiedConfiguration()
        d = c.to_dict()
        self.assertEqual(d["log_level"], "INFO")


if __name__ == "__main__":
    unittest.main()
