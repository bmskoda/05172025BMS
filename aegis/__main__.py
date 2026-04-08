"""
CLI entry point for the AEGIS forensic platform.

Usage examples::

    python -m aegis investigate blockchain --target 0x742d...bEb --network ethereum
    python -m aegis investigate patent --target US10000000 --jurisdiction US
    python -m aegis investigate tokenized_ip --target 0xABC... --network ethereum
    python -m aegis investigate wallet_community --target 0xABC... --network ethereum
    python -m aegis investigate comprehensive --target 0xABC...
    python -m aegis status
    python -m aegis health
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from aegis import __version__
from aegis.config import UnifiedConfiguration
from aegis.orchestrator import AEGISOrchestrator
from aegis.utils import setup_logging, get_logger


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aegis",
        description="AEGIS Forensic Platform — enterprise IP & blockchain investigation",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--log-file", type=str, help="Path to log file")

    sub = parser.add_subparsers(dest="command")

    inv = sub.add_parser("investigate", help="Run an investigation")
    inv.add_argument(
        "investigation_type",
        choices=[
            "blockchain", "patent", "tokenized_ip",
            "wallet_community", "nft", "domain",
            "substance", "prosecution", "comprehensive",
        ],
    )
    inv.add_argument("--target", required=True)
    inv.add_argument("--network", default="ethereum")
    inv.add_argument("--jurisdiction", default=None)
    inv.add_argument("--max-depth", type=int, default=10)
    inv.add_argument("--token-id", default="0", help="NFT token ID (for nft investigations)")
    inv.add_argument("--output", default=None)
    inv.add_argument("--format", default="json", choices=["json", "html"])

    mon = sub.add_parser("monitor", help="Start real-time blockchain monitoring")
    mon.add_argument("--networks", nargs="+", default=["ethereum"])
    mon.add_argument("--addresses", nargs="*", default=[])

    sub.add_parser("status", help="Platform status")
    sub.add_parser("health", help="API health check")

    return parser


async def _main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    setup_logging(args.log_level, args.log_file)
    log = get_logger("AEGIS")

    log.info("AEGIS Forensic Platform v%s", __version__)

    config = UnifiedConfiguration.from_environment()
    orch = AEGISOrchestrator(config)

    try:
        await orch.initialize()

        if args.command == "investigate":
            opts = {"network": args.network, "max_depth": args.max_depth}
            if args.jurisdiction:
                opts["jurisdiction"] = args.jurisdiction
            if hasattr(args, "token_id"):
                opts["token_id"] = args.token_id
            result = await orch.run_investigation(args.investigation_type, args.target, opts)
            out = args.output or f"./output/investigation_{result.investigation_id}.{args.format}"
            path = orch.generate_report(result, out, args.format)
            print(f"\nInvestigation complete: {result.investigation_id}")
            print(f"Entities: {len(result.entities)}")
            print(f"Transactions: {len(result.transactions)}")
            print(f"Patents: {len(result.patents)}")
            print(f"Report: {path}")

        elif args.command == "status":
            print(f"Version:  {__version__}")
            print(f"Init:     {orch._initialized}")
            print(f"History:  {len(orch._results)} investigations")
            print(json.dumps(orch.performance_summary(), indent=2))

        elif args.command == "monitor":
            addrs = set(args.addresses) if args.addresses else None
            print(f"Monitoring {args.networks} ...")
            await orch.start_monitoring(args.networks, addrs)

        elif args.command == "health":
            health = await orch.api_manager.health_check_all()
            for api, status in health.items():
                print(f"  {api}: {status.name}")

        else:
            parser.print_help()

        await orch.shutdown()
        return 0

    except KeyboardInterrupt:
        log.info("Interrupted")
        await orch.shutdown()
        return 130
    except Exception as exc:
        log.error("Error: %s", exc, exc_info=True)
        await orch.shutdown()
        return 1


def main() -> int:
    try:
        return asyncio.run(_main())
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
