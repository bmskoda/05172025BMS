"""
Unified configuration loaded from environment variables.

Every API key, RPC URL, and tuning knob lives here so callers never
import ``os.getenv`` directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict

from aegis.constants import ENV_PREFIX


@dataclass
class UnifiedConfiguration:
    # General
    log_level: str = "INFO"
    max_workers: int = 256
    batch_size: int = 10_000
    timeout_seconds: int = 120
    retry_attempts: int = 5
    backoff_seconds: int = 2

    # Databases (optional — used when available)
    redis_url: str = "redis://localhost:6379"
    postgres_url: str = "postgresql://localhost:5432/aegis"

    # --- API keys (loaded from env) ---
    # IP offices
    uspto_api_key: str = ""
    epo_api_key: str = ""
    wipo_api_key: str = ""
    # Blockchain analytics
    chainalysis_api_key: str = ""
    elliptic_api_key: str = ""
    bitquery_api_key: str = ""
    etherscan_api_key: str = ""
    infura_api_key: str = ""
    alchemy_api_key: str = ""
    moralis_api_key: str = ""
    dune_api_key: str = ""
    cryptocompare_api_key: str = ""
    coinmarketcap_api_key: str = ""
    nftscan_api_key: str = ""
    # Public records
    opencorporates_api_key: str = ""
    courtlistener_api_key: str = ""

    # Blockchain RPC
    ethereum_rpc_url: str = ""
    bitcoin_rpc_url: str = ""
    polygon_rpc_url: str = ""
    arbitrum_rpc_url: str = ""
    solana_rpc_url: str = ""

    # ML / AI
    model_cache_dir: str = "./models"
    enable_gpu: bool = True

    # Security
    encryption_key: str = ""

    # Output
    output_dir: str = "./output"
    report_format: str = "json"

    @classmethod
    def from_environment(cls) -> UnifiedConfiguration:
        """Populate every field from ``AEGIS_*`` env-vars."""
        c = cls()
        _e = os.getenv

        c.log_level = _e(f"{ENV_PREFIX}LOG_LEVEL", c.log_level)
        c.max_workers = int(_e(f"{ENV_PREFIX}MAX_WORKERS", str(c.max_workers)))
        c.batch_size = int(_e(f"{ENV_PREFIX}BATCH_SIZE", str(c.batch_size)))
        c.timeout_seconds = int(_e(f"{ENV_PREFIX}TIMEOUT_SECONDS", str(c.timeout_seconds)))
        c.retry_attempts = int(_e(f"{ENV_PREFIX}RETRY_ATTEMPTS", str(c.retry_attempts)))

        c.redis_url = _e(f"{ENV_PREFIX}REDIS_URL", c.redis_url)
        c.postgres_url = _e(f"{ENV_PREFIX}POSTGRES_URL", c.postgres_url)

        c.uspto_api_key = _e(f"{ENV_PREFIX}USPTO_API_KEY", "")
        c.epo_api_key = _e(f"{ENV_PREFIX}EPO_API_KEY", "")
        c.wipo_api_key = _e(f"{ENV_PREFIX}WIPO_API_KEY", "")
        c.chainalysis_api_key = _e(f"{ENV_PREFIX}CHAINALYSIS_API_KEY", "")
        c.elliptic_api_key = _e(f"{ENV_PREFIX}ELLIPTIC_API_KEY", "")
        c.bitquery_api_key = _e(f"{ENV_PREFIX}BITQUERY_API_KEY", "")
        c.etherscan_api_key = _e(f"{ENV_PREFIX}ETHERSCAN_API_KEY", "")
        c.infura_api_key = _e(f"{ENV_PREFIX}INFURA_API_KEY", "")
        c.alchemy_api_key = _e(f"{ENV_PREFIX}ALCHEMY_API_KEY", "")
        c.moralis_api_key = _e(f"{ENV_PREFIX}MORALIS_API_KEY", "")
        c.dune_api_key = _e(f"{ENV_PREFIX}DUNE_API_KEY", "")
        c.cryptocompare_api_key = _e(f"{ENV_PREFIX}CRYPTOCOMPARE_API_KEY", "")
        c.coinmarketcap_api_key = _e(f"{ENV_PREFIX}COINMARKETCAP_API_KEY", "")
        c.nftscan_api_key = _e(f"{ENV_PREFIX}NFTSCAN_API_KEY", "")
        c.opencorporates_api_key = _e(f"{ENV_PREFIX}OPENCORPORATES_API_KEY", "")
        c.courtlistener_api_key = _e(f"{ENV_PREFIX}COURTLISTENER_API_KEY", "")

        c.ethereum_rpc_url = _e(f"{ENV_PREFIX}ETHEREUM_RPC_URL", "")
        c.bitcoin_rpc_url = _e(f"{ENV_PREFIX}BITCOIN_RPC_URL", "")
        c.polygon_rpc_url = _e(f"{ENV_PREFIX}POLYGON_RPC_URL", "")
        c.arbitrum_rpc_url = _e(f"{ENV_PREFIX}ARBITRUM_RPC_URL", "")
        c.solana_rpc_url = _e(f"{ENV_PREFIX}SOLANA_RPC_URL", "")

        c.model_cache_dir = _e(f"{ENV_PREFIX}MODEL_CACHE_DIR", c.model_cache_dir)
        c.enable_gpu = _e(f"{ENV_PREFIX}ENABLE_GPU", "true").lower() == "true"
        c.encryption_key = _e(f"{ENV_PREFIX}ENCRYPTION_KEY", "")
        c.output_dir = _e(f"{ENV_PREFIX}OUTPUT_DIR", c.output_dir)
        c.report_format = _e(f"{ENV_PREFIX}REPORT_FORMAT", c.report_format)
        return c

    def to_dict(self) -> Dict[str, Any]:
        return {
            k: "***REDACTED***"
            if any(s in k for s in ("key", "secret", "password", "encryption"))
            else v
            for k, v in self.__dict__.items()
        }
