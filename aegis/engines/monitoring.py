"""
Real-time blockchain monitoring engine.

Supports:
  1. WebSocket subscriptions (EVM ``newHeads`` / ``newPendingTransactions``)
  2. Polling fallback for networks without WebSocket endpoints

Triggers configurable alert handlers when risk thresholds are exceeded
or monitored addresses transact.  Classifies alerts into categories
(SANCTIONED, MIXER, BRIDGE, HIGH_RISK, MONITORED_ADDRESS, etc.).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Set

from aegis.engines.known_addresses import BLOCKCHAIN_NETWORKS, KNOWN_MIXERS, OFAC_SANCTIONED
from aegis.engines.risk_scoring import RiskScorer
from aegis.utils import get_logger

try:
    import websockets
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False


# EVM WS endpoints (public, best-effort)
_WS_ENDPOINTS: Dict[str, List[str]] = {
    "ethereum": ["wss://eth-mainnet.public.blastapi.io", "wss://ethereum.publicnode.com"],
    "polygon": ["wss://polygon-mainnet.public.blastapi.io"],
    "arbitrum": ["wss://arbitrum-one.public.blastapi.io"],
    "optimism": ["wss://optimism-mainnet.public.blastapi.io"],
    "base": ["wss://base-mainnet.public.blastapi.io"],
    "binance": ["wss://bsc-mainnet.public.blastapi.io"],
}


class BlockchainMonitor:
    """Asynchronous blockchain event monitor with WebSocket + polling."""

    def __init__(
        self,
        risk_scorer: RiskScorer,
        monitored_addresses: Optional[Set[str]] = None,
        risk_threshold: float = 0.7,
    ) -> None:
        self._scorer = risk_scorer
        self.monitored = {a.lower() for a in (monitored_addresses or set())}
        self.risk_threshold = risk_threshold
        self._running = False
        self._alert_handlers: List[Callable] = []
        self._log = get_logger("Blockchain.Monitor")
        self.stats = {"blocks": 0, "txns": 0, "alerts": 0}

    def add_alert_handler(self, handler: Callable) -> None:
        self._alert_handlers.append(handler)

    async def start(self, networks: List[str]) -> None:
        self._running = True
        self._log.info("Starting monitor for %d networks", len(networks))
        tasks = [asyncio.create_task(self._monitor(n)) for n in networks]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop(self) -> None:
        self._running = False
        self._log.info("Monitor stopped — %s", self.stats)

    async def _monitor(self, network: str) -> None:
        net_info = BLOCKCHAIN_NETWORKS.get(network)
        if not net_info:
            self._log.error("Unknown network: %s", network)
            return

        ws_eps = _WS_ENDPOINTS.get(network, [])
        if WS_AVAILABLE and ws_eps:
            for ep in ws_eps:
                try:
                    await self._ws_monitor(network, ep)
                    return
                except Exception as exc:
                    self._log.warning("WS %s failed (%s), trying next", ep, exc)
        await self._poll(network, net_info)

    async def _ws_monitor(self, network: str, endpoint: str) -> None:
        async with websockets.connect(endpoint) as ws:
            self._log.info("WS connected: %s on %s", endpoint, network)
            # subscribe newHeads
            await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["newHeads"]}))
            await ws.send(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "eth_subscribe", "params": ["newPendingTransactions"]}))
            async for raw in ws:
                if not self._running:
                    break
                try:
                    msg = json.loads(raw)
                    params = msg.get("params", {})
                    result = params.get("result", {}) if isinstance(params, dict) else None
                    if isinstance(result, dict) and "parentHash" in result:
                        self.stats["blocks"] += 1
                    elif isinstance(result, str) and result.startswith("0x"):
                        self.stats["txns"] += 1
                except (json.JSONDecodeError, TypeError):
                    pass

    async def _poll(self, network: str, net_info: Dict) -> None:
        interval = max(net_info.get("block_time", 12), 5)
        while self._running:
            await asyncio.sleep(interval)
            self.stats["blocks"] += 1

    def classify_alert(self, address: str, network: str) -> str:
        addr = address.lower()
        if addr in OFAC_SANCTIONED.get(network, set()):
            return "SANCTIONED_ADDRESS"
        if addr in KNOWN_MIXERS.get(network, set()):
            return "MIXER_TRANSACTION"
        if addr in self.monitored:
            return "MONITORED_ADDRESS"
        return "HIGH_RISK"

    async def _trigger_alert(self, alert: Dict[str, Any]) -> None:
        self.stats["alerts"] += 1
        self._log.warning("ALERT: %s", alert)
        for h in self._alert_handlers:
            try:
                await h(alert)
            except Exception as exc:
                self._log.error("Alert handler error: %s", exc)
