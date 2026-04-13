"""API client layer — rate-limited, circuit-breaker-protected HTTP clients."""

from aegis.api.base import APIClient, CircuitBreaker, RateLimiter
from aegis.api.clients import (
    USPTOClient,
    EPOClient,
    WIPOClient,
    ChainalysisClient,
    EllipticClient,
    BitqueryClient,
    EtherscanClient,
    OpenCorporatesClient,
    CourtListenerClient,
    NFTScanClient,
)
from aegis.api.manager import APIIntegrationManager

__all__ = [
    "APIClient",
    "CircuitBreaker",
    "RateLimiter",
    "USPTOClient",
    "EPOClient",
    "WIPOClient",
    "ChainalysisClient",
    "EllipticClient",
    "BitqueryClient",
    "EtherscanClient",
    "OpenCorporatesClient",
    "CourtListenerClient",
    "NFTScanClient",
    "APIIntegrationManager",
]
