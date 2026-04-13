"""
Master orchestrator — wires every engine together and exposes
the CLI and programmatic API.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional, Set

from aegis.api.manager import APIIntegrationManager
from aegis.config import UnifiedConfiguration
from aegis.constants import EntityType, Jurisdiction
from aegis.engines.blockchain import BlockchainForensicsEngine
from aegis.engines.correlation import CrossDomainCorrelator, TemporalWindow, LCSDiffDetector
from aegis.engines.domain_investigation import DomainInvestigator
from aegis.engines.monitoring import BlockchainMonitor
from aegis.engines.network_graph import NetworkGraphAnalyzer
from aegis.engines.nft_tracker import NFTTracker
from aegis.engines.patent import PatentAnalysisEngine, FileWrapperAnalyzer
from aegis.engines.risk_scoring import RiskScorer
from aegis.engines.substance_tracing import SubstanceTracer
from aegis.engines.tokenized_ip import TokenizedIPEngine
from aegis.engines.wallet_community import WalletCommunityMapper
from aegis.models.core import (
    InvestigationResult,
    NetworkNode,
    Timestamp,
)
from aegis.reports.evidence import EvidenceChainBuilder
from aegis.reports.generator import ForensicReportGenerator
from aegis.utils import (
    SignalHandler,
    get_logger,
    performance_monitor,
)


class AEGISOrchestrator:
    """Top-level orchestrator for the AEGIS forensic platform.

    Usage::

        cfg = UnifiedConfiguration.from_environment()
        orch = AEGISOrchestrator(cfg)
        await orch.initialize()
        result = await orch.run_investigation("comprehensive", "0x...")
        orch.generate_report(result, "report.html", "html")
        await orch.shutdown()
    """

    def __init__(self, config: Optional[UnifiedConfiguration] = None) -> None:
        self.config = config or UnifiedConfiguration.from_environment()
        self._log = get_logger("AEGIS.Orchestrator")
        self._signal = SignalHandler()

        self.api_manager = APIIntegrationManager(self.config)
        self.blockchain = BlockchainForensicsEngine(self.api_manager, self.config)
        self.patent = PatentAnalysisEngine(self.api_manager, self.config)
        self.file_wrapper = FileWrapperAnalyzer()
        self.tokenized_ip = TokenizedIPEngine(self.api_manager, self.config)
        self.community_mapper = WalletCommunityMapper(self.api_manager, self.config)
        self.network = NetworkGraphAnalyzer(self.config)
        self.risk_scorer = RiskScorer(self.api_manager)
        self.nft_tracker = NFTTracker(self.api_manager)
        self.domain_investigator = DomainInvestigator(self.api_manager)
        self.substance_tracer = SubstanceTracer(self.api_manager)
        self.correlator = CrossDomainCorrelator()
        self.monitor = BlockchainMonitor(self.risk_scorer)
        self.evidence = EvidenceChainBuilder(
            key_dir=f"{self.config.output_dir}/evidence_keys"
        )
        self.report_gen = ForensicReportGenerator(self.config)

        self._initialized = False
        self._results: List[InvestigationResult] = []

    async def initialize(self) -> None:
        self._signal.setup()
        await self.api_manager.initialize()
        health = await self.api_manager.health_check_all()
        self._log.info("API health: %s", health)
        self._initialized = True
        self._log.info("AEGIS platform initialised")

    async def shutdown(self) -> None:
        await self.monitor.stop()
        await self.api_manager.close_all()
        self._log.info("AEGIS platform shut down")

    # -- investigation runners -----------------------------------------------

    async def run_investigation(
        self,
        investigation_type: str,
        target: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> InvestigationResult:
        if not self._initialized:
            raise RuntimeError("Call initialize() first")
        options = options or {}
        inv_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
        self._log.info("Starting %s investigation %s for %s", investigation_type, inv_id, target)
        t0 = time.perf_counter()

        dispatch = {
            "blockchain": self._inv_blockchain,
            "patent": self._inv_patent,
            "tokenized_ip": self._inv_tokenized_ip,
            "wallet_community": self._inv_wallet_community,
            "nft": self._inv_nft,
            "domain": self._inv_domain,
            "substance": self._inv_substance,
            "prosecution": self._inv_prosecution,
            "comprehensive": self._inv_comprehensive,
        }
        handler = dispatch.get(investigation_type)
        if not handler:
            raise ValueError(f"Unknown investigation type: {investigation_type}")

        result = await handler(target, options)
        elapsed = time.perf_counter() - t0
        self._log.info("Investigation %s completed in %.2fs", inv_id, elapsed)
        self._results.append(result)
        return result

    async def _inv_blockchain(self, target: str, opts: Dict) -> InvestigationResult:
        network = opts.get("network", "ethereum")
        depth = opts.get("max_depth", 10)
        analysis = await self.blockchain.analyze_address(target, network, depth)
        risk_detail = await self.risk_scorer.score_address(target, network)
        entities = [NetworkNode(
            node_id=target,
            entity_type=EntityType.CRYPTOCURRENCY_ADDRESS,
            name=f"Address {target[:12]}...",
            risk_score=risk_detail.get("risk_score", 0.0),
        )]
        return InvestigationResult(
            investigation_id=f"BLOCKCHAIN-{uuid.uuid4().hex[:8].upper()}",
            timestamp=Timestamp.now(),
            entities=entities,
            risk_assessment={
                "overall_risk": risk_detail["risk_level"].name,
                "risk_score": risk_detail["risk_score"],
                "factors": risk_detail.get("factors", []),
                "mixer_detected": analysis.get("mixer_analysis", {}).get("mixer_detected", False),
                "analysis": analysis,
            },
        )

    async def _inv_patent(self, target: str, opts: Dict) -> InvestigationResult:
        jur = Jurisdiction(opts["jurisdiction"]) if opts.get("jurisdiction") else None
        patents = await self.patent.search(target, jur, limit=100)
        family = await self.patent.analyze_family(target) if patents else {}
        entities = [
            NetworkNode(
                node_id=f"INV-{hash(i.get('name', '')) % 10 ** 6}",
                entity_type=EntityType.INDIVIDUAL,
                name=i.get("name", ""),
            )
            for p in patents
            for i in p.inventors
        ]
        return InvestigationResult(
            investigation_id=f"PATENT-{uuid.uuid4().hex[:8].upper()}",
            timestamp=Timestamp.now(),
            entities=entities,
            patents=patents,
            risk_assessment={
                "overall_risk": "HIGH" if any(p.h_flag_score > 0.7 for p in patents) else "MEDIUM",
                "high_risk_patents": len([p for p in patents if p.h_flag_score > 0.5]),
                "family": family,
            },
        )

    async def _inv_tokenized_ip(self, target: str, opts: Dict) -> InvestigationResult:
        network = opts.get("network", "ethereum")
        depth = opts.get("max_depth", 10)
        tip = await self.tokenized_ip.investigate(target, network, depth)
        return InvestigationResult(
            investigation_id=f"TOKEN-IP-{uuid.uuid4().hex[:8].upper()}",
            timestamp=Timestamp.now(),
            risk_assessment={
                "overall_risk": "HIGH" if tip.get("is_ip_ecosystem_participant") else "LOW",
                "tokenized_ip": tip,
            },
        )

    async def _inv_wallet_community(self, target: str, opts: Dict) -> InvestigationResult:
        network = opts.get("network", "ethereum")
        seeds = opts.get("seed_addresses", [target])
        tree = await self.community_mapper.map(seeds, network)
        return InvestigationResult(
            investigation_id=f"COMMUNITY-{uuid.uuid4().hex[:8].upper()}",
            timestamp=Timestamp.now(),
            risk_assessment={
                "overall_risk": "HIGH" if tree.get("statistics", {}).get("total_communities", 0) > 5 else "MEDIUM",
                "community_tree": tree,
            },
        )

    async def _inv_nft(self, target: str, opts: Dict) -> InvestigationResult:
        network = opts.get("network", "ethereum")
        token_id = opts.get("token_id", "0")
        nft = await self.nft_tracker.track(target, token_id, network)
        return InvestigationResult(
            investigation_id=f"NFT-{uuid.uuid4().hex[:8].upper()}",
            timestamp=Timestamp.now(),
            risk_assessment={
                "overall_risk": "HIGH" if nft.get("risk_score", 0) > 0.5 else "LOW",
                "wash_trading_score": nft.get("wash_trading_score", 0),
                "is_fractionalized": nft.get("is_fractionalized", False),
                "nft_analysis": nft,
            },
        )

    async def _inv_domain(self, target: str, opts: Dict) -> InvestigationResult:
        result = await self.domain_investigator.investigate(target)
        return InvestigationResult(
            investigation_id=f"DOMAIN-{uuid.uuid4().hex[:8].upper()}",
            timestamp=Timestamp.now(),
            risk_assessment={
                "overall_risk": "MEDIUM",
                "domain_investigation": result,
            },
        )

    async def _inv_substance(self, target: str, opts: Dict) -> InvestigationResult:
        chain_id = opts.get("chain_id", 1)
        token_result = await self.substance_tracer.trace_token(target, chain_id)
        patterns = await self.substance_tracer.detect_market_patterns(target, chain_id)
        risk = "HIGH" if token_result.get("risk_indicators") or patterns else "LOW"
        return InvestigationResult(
            investigation_id=f"SUBSTANCE-{uuid.uuid4().hex[:8].upper()}",
            timestamp=Timestamp.now(),
            risk_assessment={
                "overall_risk": risk,
                "token_trace": token_result,
                "market_patterns": patterns,
            },
        )

    async def _inv_prosecution(self, target: str, opts: Dict) -> InvestigationResult:
        h_flags = await self.file_wrapper.detect_h_flags(self.api_manager, target)
        timeline = await self.file_wrapper.analyze_prosecution_timeline(self.api_manager, target)
        risk = "HIGH" if h_flags.get("has_h_flag") or timeline.get("anomalies") else "LOW"
        return InvestigationResult(
            investigation_id=f"PROSECUTION-{uuid.uuid4().hex[:8].upper()}",
            timestamp=Timestamp.now(),
            risk_assessment={
                "overall_risk": risk,
                "h_flag_analysis": h_flags,
                "prosecution_timeline": timeline,
            },
        )

    async def _inv_comprehensive(self, target: str, opts: Dict) -> InvestigationResult:
        bc = await self._inv_blockchain(target, opts)
        pat = await self._inv_patent(target, opts)
        tip = await self._inv_tokenized_ip(target, opts)
        wc = await self._inv_wallet_community(target, opts)
        nft = await self._inv_nft(target, opts)
        return InvestigationResult(
            investigation_id=f"COMP-{uuid.uuid4().hex[:8].upper()}",
            timestamp=Timestamp.now(),
            entities=bc.entities + pat.entities,
            transactions=bc.transactions,
            patents=pat.patents,
            risk_assessment={
                "overall_risk": "HIGH",
                "blockchain": bc.risk_assessment,
                "patent": pat.risk_assessment,
                "tokenized_ip": tip.risk_assessment,
                "wallet_community": wc.risk_assessment,
                "nft": nft.risk_assessment,
            },
        )

    async def batch_analyze(
        self, targets: List[Dict[str, str]], max_concurrent: int = 50,
    ) -> List[InvestigationResult]:
        """Run investigations concurrently for a batch of targets.

        Each entry in *targets* is ``{"type": ..., "target": ..., **opts}``.
        """
        sem = asyncio.Semaphore(max_concurrent)

        async def _one(entry: Dict[str, str]) -> InvestigationResult:
            async with sem:
                inv_type = entry.pop("type", "blockchain")
                tgt = entry.pop("target")
                return await self.run_investigation(inv_type, tgt, entry)

        return list(await asyncio.gather(
            *[_one(dict(e)) for e in targets], return_exceptions=False,
        ))

    # -- monitoring ----------------------------------------------------------

    async def start_monitoring(
        self, networks: List[str], addresses: Optional[Set[str]] = None
    ) -> None:
        if addresses:
            self.monitor.monitored.update(a.lower() for a in addresses)
        await self.monitor.start(networks)

    # -- report --------------------------------------------------------------

    def generate_report(
        self, result: InvestigationResult, path: str, fmt: str = "json"
    ) -> str:
        report = self.report_gen.generate(result, fmt)
        return self.report_gen.save(report, path, fmt)

    def performance_summary(self) -> Dict[str, Any]:
        return performance_monitor.get_summary()
