"""
Load EVA-Bench scenarios from bundled JSON or Hugging Face JSONL files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
BUNDLED_SCENARIOS = DATA_DIR / "eva-scenarios.json"

DOMAIN_FILES = {
    "airline_csm": "data/eva_bench_csm_airline.jsonl",
    "healthcare_hrsd": "data/eva_bench_hr_medical.jsonl",
    "enterprise_itsm": "data/eva_bench_itsm.jsonl",
}

DOMAIN_LABELS = {
    "airline_csm": "Airline Customer Service",
    "healthcare_hrsd": "Healthcare HR",
    "enterprise_itsm": "Enterprise ITSM",
}


@dataclass(frozen=True)
class EvaScenario:
    """A VoiceIQ-compatible scenario derived from an EVA-Bench record."""

    eva_id: str
    domain: str
    domain_label: str
    scenario_name: str
    scenario_description: str
    caller_personality: str
    caller_goal: str
    difficulty_level: str
    hangup_triggers: list[str] = field(default_factory=list)
    behavior_rules: list[str] = field(default_factory=list)
    persona_prompt: str = ""
    must_have_criteria: list[str] = field(default_factory=list)
    starting_utterance: str = ""
    tool_density: str = "medium"
    agent_context: str = ""


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    return payload.get("scenarios", [])


def _record_to_scenario(record: dict[str, Any]) -> EvaScenario:
    """Load from pre-mapped bundled JSON or raw EVA-Bench record."""
    from voiceiq_eva.mapper import eva_record_to_scenario

    if "persona_prompt" in record and "eva_id" in record:
        return EvaScenario(
            eva_id=str(record["eva_id"]),
            domain=str(record.get("domain", "airline_csm")),
            domain_label=str(record.get("domain_label", record.get("domain", ""))),
            scenario_name=str(record.get("scenario_name", record["eva_id"])),
            scenario_description=str(record.get("scenario_description", "")),
            caller_personality=str(record.get("caller_personality", "enterprise")),
            caller_goal=str(record.get("caller_goal", "")),
            difficulty_level=str(record.get("difficulty_level", "medium")),
            hangup_triggers=list(record.get("hangup_triggers", [])),
            behavior_rules=list(record.get("behavior_rules", [])),
            persona_prompt=str(record.get("persona_prompt", "")),
            must_have_criteria=list(record.get("must_have_criteria", [])),
            starting_utterance=str(record.get("starting_utterance", "")),
            tool_density=str(record.get("tool_density", "medium")),
            agent_context=str(record.get("agent_context", "")),
        )
    return eva_record_to_scenario(record)


def load_eva_scenarios(
    *,
    domain: str | None = None,
    limit: int | None = None,
    bundled_only: bool = True,
) -> list[EvaScenario]:
    """Load EVA scenarios from bundled JSON (default) or Hugging Face."""
    if bundled_only or not BUNDLED_SCENARIOS.exists():
        if not BUNDLED_SCENARIOS.exists():
            raise FileNotFoundError(
                f"Bundled scenarios not found at {BUNDLED_SCENARIOS}. "
                "Run: python scripts/sync_eva_scenarios.py"
            )
        records = _load_json(BUNDLED_SCENARIOS)
    else:
        records = _load_from_huggingface(domain=domain, limit=limit)

    scenarios = [_record_to_scenario(record) for record in records]
    if domain:
        scenarios = [s for s in scenarios if s.domain == domain]
    if limit is not None:
        scenarios = scenarios[:limit]
    return scenarios


def _load_from_huggingface(
    *,
    domain: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    from huggingface_hub import hf_hub_download

    domains = [domain] if domain else list(DOMAIN_FILES.keys())
    records: list[dict[str, Any]] = []

    for domain_key in domains:
        rel_path = DOMAIN_FILES[domain_key]
        local_path = hf_hub_download(
            "ServiceNow-AI/eva-bench",
            rel_path,
            repo_type="dataset",
        )
        with open(local_path, encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if limit is not None and index >= limit:
                    break
                row = json.loads(line)
                row.setdefault("domain", domain_key)
                records.append(row)

    return records
