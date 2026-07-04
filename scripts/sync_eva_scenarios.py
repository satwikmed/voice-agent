#!/usr/bin/env python3
"""
Sync a curated subset of EVA-Bench scenarios from Hugging Face into bundled JSON.

Usage:
    python scripts/sync_eva_scenarios.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from voiceiq_eva.loader import DOMAIN_FILES  # noqa: E402
from voiceiq_eva.mapper import eva_record_to_scenario  # noqa: E402
from voiceiq_eva.scenario_context import build_agent_context  # noqa: E402

PER_DOMAIN = 5
OUTPUT_PATHS = [
    PROJECT_ROOT / "voiceiq_eva" / "data" / "eva-scenarios.json",
    PROJECT_ROOT / "frontend" / "src" / "data" / "eva-scenarios.json",
]


def _parse_json(value: object) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return {}


def main() -> None:
    from huggingface_hub import hf_hub_download

    records: list[dict] = []

    for domain, rel_path in DOMAIN_FILES.items():
        local_path = hf_hub_download(
            "ServiceNow-AI/eva-bench",
            rel_path,
            repo_type="dataset",
        )
        with open(local_path, encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if index >= PER_DOMAIN:
                    break
                row = json.loads(line)
                row["domain"] = domain
                scenario = eva_record_to_scenario(row)
                user_goal = _parse_json(row.get("user_goal"))
                user_config = _parse_json(row.get("user_config"))
                scenario_context = _parse_json(row.get("scenario_context"))
                scenario_db = _parse_json(
                    row.get("initial_scenario_database") or row.get("initial_scenario_db")
                )
                ground_truth = _parse_json(row.get("ground_truth"))
                agent_context = build_agent_context(
                    domain=domain,
                    scenario_database=scenario_db,
                    ground_truth=ground_truth,
                    user_goal=user_goal,
                    user_config=user_config,
                    scenario_context=scenario_context,
                )
                records.append(
                    {
                        "eva_id": scenario.eva_id,
                        "domain": scenario.domain,
                        "domain_label": scenario.domain_label,
                        "scenario_name": scenario.scenario_name,
                        "scenario_description": scenario.scenario_description,
                        "caller_personality": scenario.caller_personality,
                        "caller_goal": scenario.caller_goal,
                        "difficulty_level": scenario.difficulty_level,
                        "hangup_triggers": scenario.hangup_triggers,
                        "behavior_rules": scenario.behavior_rules,
                        "persona_prompt": scenario.persona_prompt,
                        "must_have_criteria": scenario.must_have_criteria,
                        "starting_utterance": scenario.starting_utterance,
                        "tool_density": scenario.tool_density,
                        "agent_context": agent_context,
                    }
                )

    payload = {
        "source": "ServiceNow-AI/eva-bench",
        "license": "MIT",
        "scenario_count": len(records),
        "scenarios": records,
    }

    for path in OUTPUT_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"Wrote {len(records)} scenarios to {path}")


if __name__ == "__main__":
    main()
