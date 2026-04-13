"""
Shared utility functions: logging, hashing, validation, decorators.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import logging.handlers
import math
import os
import signal
import string
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from aegis.constants import ENV_PREFIX
from aegis.models.core import CryptoHash, Timestamp


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Configure the ``AEGIS`` logger hierarchy with console + optional file."""
    logger = logging.getLogger("AEGIS")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=100 * 1024 * 1024, backupCount=10
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


def get_logger(name: str = "AEGIS") -> logging.Logger:
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Evidence helpers
# ---------------------------------------------------------------------------


def generate_evidence_id() -> str:
    return f"EVD-{uuid.uuid4().hex[:16].upper()}"


def generate_case_number() -> str:
    now = datetime.now(timezone.utc)
    return f"CASE-{now.year}-{now.month:02d}-{uuid.uuid4().hex[:8].upper()}"


def hash_evidence(data: Any, algorithm: str = "sha3_256") -> CryptoHash:
    if isinstance(data, (dict, list)):
        data = json.dumps(data, sort_keys=True, default=str)
    return CryptoHash.compute(str(data), algorithm)


# ---------------------------------------------------------------------------
# Blockchain address validation
# ---------------------------------------------------------------------------


def validate_blockchain_address(address: str, network: str) -> bool:
    if not address or not network:
        return False
    net = network.lower()
    if net in ("ethereum", "eth", "polygon", "arbitrum", "optimism", "bsc", "avalanche", "base"):
        return address.startswith("0x") and len(address) == 42 and all(
            c in string.hexdigits for c in address[2:]
        )
    if net in ("bitcoin", "btc"):
        if address.startswith(("1", "3")):
            return 26 <= len(address) <= 35
        if address.startswith("bc1"):
            return 42 <= len(address) <= 62
        return False
    if net in ("solana", "sol"):
        return 32 <= len(address) <= 44
    return True


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_currency(value: Union[Decimal, float, str], currency: str = "USD") -> str:
    if isinstance(value, str):
        value = Decimal(value)
    elif isinstance(value, float):
        value = Decimal(str(value))
    if currency == "USD":
        return f"${value:,.2f}"
    if currency == "BTC":
        return f"\u20bf{value:.8f}"
    if currency == "ETH":
        return f"\u039e{value:.18f}"
    return f"{value:,.2f} {currency}"


def parse_timestamp(ts: Union[str, int, float, datetime]) -> Timestamp:
    if isinstance(ts, Timestamp):
        return ts
    if isinstance(ts, datetime):
        return Timestamp.from_datetime(ts)
    if isinstance(ts, (int, float)):
        if ts > 1e12:
            return Timestamp(int(ts), 0)
        return Timestamp(int(ts * 1e9), 0)
    if isinstance(ts, str):
        try:
            return Timestamp.from_iso(ts)
        except Exception:
            return Timestamp(int(float(ts) * 1e9), 0)
    raise ValueError(f"Cannot parse timestamp: {ts}")


def sanitize_filename(filename: str) -> str:
    for ch in '<>:"/\\|?*':
        filename = filename.replace(ch, "_")
    return filename[:255]


def chunk_list(items: list, chunk_size: int) -> List[list]:
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def retry_with_backoff(max_retries: int = 5, backoff_base: float = 2.0):
    """Exponential-backoff retry for both sync and async callables."""

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def _async(*args: Any, **kw: Any) -> Any:
                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kw)
                    except Exception as exc:
                        if attempt == max_retries - 1:
                            raise
                        wait = backoff_base * (2**attempt)
                        get_logger().warning(
                            "Attempt %d failed: %s — retrying in %.1fs",
                            attempt + 1,
                            exc,
                            wait,
                        )
                        await asyncio.sleep(wait)
                return None

            return _async
        else:

            @wraps(func)
            def _sync(*args: Any, **kw: Any) -> Any:
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kw)
                    except Exception as exc:
                        if attempt == max_retries - 1:
                            raise
                        wait = backoff_base * (2**attempt)
                        get_logger().warning(
                            "Attempt %d failed: %s — retrying in %.1fs",
                            attempt + 1,
                            exc,
                            wait,
                        )
                        time.sleep(wait)
                return None

            return _sync

    return decorator


def measure_execution_time(func: Callable) -> Callable:
    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def _a(*a: Any, **kw: Any) -> Any:
            t0 = time.perf_counter()
            try:
                return await func(*a, **kw)
            finally:
                get_logger().debug(
                    "%s executed in %.4fs", func.__name__, time.perf_counter() - t0
                )

        return _a

    @wraps(func)
    def _s(*a: Any, **kw: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return func(*a, **kw)
        finally:
            get_logger().debug(
                "%s executed in %.4fs", func.__name__, time.perf_counter() - t0
            )

    return _s


# ---------------------------------------------------------------------------
# Performance monitor (singleton-style)
# ---------------------------------------------------------------------------


class PerformanceMonitor:
    def __init__(self) -> None:
        self._metrics: Dict[str, List[Tuple[Timestamp, float]]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._start_times: Dict[str, float] = {}

    def start_timer(self, name: str) -> None:
        self._start_times[name] = time.perf_counter()

    def end_timer(self, name: str) -> float:
        if name not in self._start_times:
            return 0.0
        dur = time.perf_counter() - self._start_times.pop(name)
        self._metrics[name].append((Timestamp.now(), dur))
        return dur

    def increment_counter(self, name: str, value: int = 1) -> None:
        self._counters[name] += value

    def get_summary(self) -> Dict[str, Any]:
        return {
            "timers": {
                n: {
                    "count": len(v),
                    "avg": sum(x for _, x in v) / len(v) if v else 0,
                }
                for n, v in self._metrics.items()
            },
            "counters": dict(self._counters),
        }


performance_monitor = PerformanceMonitor()


# ---------------------------------------------------------------------------
# Signal handler for graceful shutdown
# ---------------------------------------------------------------------------


class SignalHandler:
    def __init__(self) -> None:
        self.shutdown_event = asyncio.Event()
        self._handlers: List[Callable] = []

    def register_handler(self, handler: Callable) -> None:
        self._handlers.append(handler)

    def setup(self) -> None:
        def _handle(signum: int, frame: Any) -> None:
            get_logger().info("Signal %d received — shutting down", signum)
            self.shutdown_event.set()
            for h in self._handlers:
                try:
                    h()
                except Exception:
                    pass

        signal.signal(signal.SIGINT, _handle)
        signal.signal(signal.SIGTERM, _handle)

    async def wait_for_shutdown(self) -> None:
        await self.shutdown_event.wait()
