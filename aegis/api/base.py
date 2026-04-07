"""
Base HTTP client with circuit-breaker and token-bucket rate limiter.
"""

from __future__ import annotations

import asyncio
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from aegis.constants import (
    APIStatus,
    CIRCUIT_BREAKER_THRESHOLD,
    CIRCUIT_BREAKER_TIMEOUT,
    DEFAULT_TIMEOUT,
    HTTPMethod,
)
from aegis.models.core import APIResponse, Timestamp
from aegis.utils import get_logger

try:
    import aiohttp
    from aiohttp import ClientSession, ClientTimeout, TCPConnector

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------


class CircuitBreaker:
    def __init__(
        self,
        threshold: int = CIRCUIT_BREAKER_THRESHOLD,
        timeout: int = CIRCUIT_BREAKER_TIMEOUT,
    ) -> None:
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        with self._lock:
            if self.state == "closed":
                return True
            if self.state == "open":
                if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                    self.state = "half-open"
                    self.failure_count = 0
                    return True
                return False
            return True

    def record_success(self) -> None:
        with self._lock:
            self.failure_count = 0
            self.state = "closed"

    def record_failure(self) -> None:
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.threshold:
                self.state = "open"


# ---------------------------------------------------------------------------
# Token-bucket rate limiter
# ---------------------------------------------------------------------------


class RateLimiter:
    def __init__(self, requests_per_minute: int) -> None:
        self.rate = requests_per_minute / 60.0
        self.tokens = self.rate
        self.capacity = self.rate
        self.last_update = time.time()
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        with self._lock:
            now = time.time()
            self.tokens = min(self.capacity, self.tokens + (now - self.last_update) * self.rate)
            self.last_update = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    async def wait_and_acquire(self) -> None:
        while not self.acquire():
            await asyncio.sleep(0.1)


# ---------------------------------------------------------------------------
# Abstract API client
# ---------------------------------------------------------------------------


class APIClient(ABC):
    """Base class for every external-API client."""

    def __init__(
        self,
        api_name: str,
        base_url: str,
        api_key: str = "",
        rate_limit: int = 100,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_name = api_name
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limiter = RateLimiter(rate_limit)
        self.circuit_breaker = CircuitBreaker()
        self._session: Optional[ClientSession] = None
        self._logger = get_logger(f"API.{api_name}")

    # -- session management --------------------------------------------------

    async def _get_session(self) -> ClientSession:
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp is required for API calls")
        if self._session is None or self._session.closed:
            connector = TCPConnector(limit=100, limit_per_host=20)
            self._session = ClientSession(
                connector=connector,
                timeout=ClientTimeout(total=self.timeout),
            )
        return self._session

    # -- core request --------------------------------------------------------

    async def _make_request(
        self,
        method: HTTPMethod,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        if not AIOHTTP_AVAILABLE:
            return APIResponse(success=False, error="aiohttp not installed", status_code=503)

        if not self.circuit_breaker.can_execute():
            return APIResponse(success=False, error="Circuit breaker open", status_code=503)

        await self.rate_limiter.wait_and_acquire()

        url = f"{self.base_url}{endpoint}" if endpoint else self.base_url
        req_headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "AEGIS-Platform/16.0",
        }
        if self.api_key:
            req_headers.setdefault("Authorization", f"Bearer {self.api_key}")
        if headers:
            req_headers.update(headers)

        t0 = time.perf_counter()
        try:
            session = await self._get_session()
            async with session.request(
                method.value, url, params=params, json=data, headers=req_headers
            ) as resp:
                latency = (time.perf_counter() - t0) * 1000
                if resp.status == 429:
                    self.circuit_breaker.record_failure()
                    return APIResponse(success=False, error="Rate limited", status_code=429, latency_ms=latency)
                resp.raise_for_status()
                self.circuit_breaker.record_success()
                ct = resp.headers.get("Content-Type", "")
                body = await resp.json() if "application/json" in ct else await resp.text()
                return APIResponse(
                    success=True,
                    data=body,
                    status_code=resp.status,
                    latency_ms=latency,
                    rate_limit_remaining=int(resp.headers.get("X-RateLimit-Remaining", 0)),
                )
        except Exception as exc:
            self.circuit_breaker.record_failure()
            latency = (time.perf_counter() - t0) * 1000
            self._logger.error("Request to %s failed: %s", url, exc)
            return APIResponse(success=False, error=str(exc), status_code=500, latency_ms=latency)

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    @abstractmethod
    async def health_check(self) -> APIStatus:
        ...
