#!/usr/bin/env python3
"""RetellEVA CLI — run EVA-Bench scenarios against Retell-style agent prompts."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from retell_eva.runner import run_eva_benchmark_sync  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RetellEVA: pre-launch QA for Retell agents on EVA-Bench scenarios",
    )
    parser.add_argument(
        "--domain",
        choices=["airline_csm", "healthcare_hrsd", "enterprise_itsm"],
        help="Limit to one EVA domain",
    )
    parser.add_argument("--limit", type=int, help="Max scenarios to run")
    parser.add_argument("--agent-prompt-file", help="Custom agent system prompt file")
    parser.add_argument("--output", help="Write JSON results to this path")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    agent_prompt = None
    if args.agent_prompt_file:
        agent_prompt = Path(args.agent_prompt_file).read_text(encoding="utf-8")

    results = run_eva_benchmark_sync(
        domain=args.domain,
        limit=args.limit,
        agent_prompt=agent_prompt,
    )

    summary = results["summary"]
    print("\n=== RetellEVA Benchmark Summary ===")
    print(f"Scenarios: {summary['scenario_count']}")
    print(f"EVA-A pass@1: {summary['eva_a_pass_at_1']:.1%}")
    print(f"EVA-X pass@1: {summary['eva_x_pass_at_1']:.1%}")
    print(f"Composite pass@1: {summary['composite_pass_at_1']:.1%}")
    for domain, stats in summary.get("by_domain", {}).items():
        print(
            f"  {domain}: EVA-A={stats['avg_eva_a']:.2f} "
            f"EVA-X={stats['avg_eva_x']:.2f} "
            f"pass={stats['composite_pass_at_1']:.1%}"
        )

    if args.output:
        Path(args.output).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nResults written to {args.output}")


if __name__ == "__main__":
    main()
