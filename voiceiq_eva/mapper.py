"""
Map EVA-Bench JSONL records to VoiceIQ Scenario-compatible objects.
"""

from __future__ import annotations

import json
from typing import Any

from voiceiq_eva.caller_facts import build_caller_facts, format_caller_facts_block
from voiceiq_eva.loader import DOMAIN_LABELS, EvaScenario

DOMAIN_DIFFICULTY = {
    "airline_csm": "medium",
    "healthcare_hrsd": "hard",
    "enterprise_itsm": "hard",
}

DOMAIN_TOOL_DENSITY = {
    "airline_csm": "low",
    "healthcare_hrsd": "high",
    "enterprise_itsm": "high",
}


def _parse_json_field(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return {}


def _scenario_title(domain: str, eva_id: str, user_config: dict[str, Any]) -> str:
    name = user_config.get("name", "Caller")
    label = DOMAIN_LABELS.get(domain, domain)
    return f"{label} — {name} ({eva_id})"


def _build_persona_prompt(
    *,
    user_config: dict[str, Any],
    user_goal: dict[str, Any],
    scenario_context: dict[str, Any],
    must_have: list[str],
    negotiation: list[str],
    caller_facts: dict[str, str] | None = None,
) -> str:
    name = user_config.get("name", "the caller")
    gender = user_config.get("gender", "person")
    premise = scenario_context.get("premise", "")
    high_level = user_goal.get("high_level_user_goal", "")
    starting = user_goal.get("starting_utterance", "")
    resolution = user_goal.get("decision_tree", {}).get("resolution_condition", "")

    must_have_block = "\n".join(f"- {item}" for item in must_have) or "- Complete the stated goal."
    negotiation_block = "\n".join(f"- {item}" for item in negotiation[:6]) or "- Be cooperative but firm on must-haves."

    facts_block = format_caller_facts_block(caller_facts or {})
    facts_section = f"\n{facts_block}\n\n" if facts_block else ""

    return (
        f"You are {name}, a {gender} calling a phone support line.\n\n"
        f"SITUATION:\n{premise}\n\n"
        f"YOUR GOAL:\n{high_level}\n\n"
        f"MUST-HAVE CRITERIA (do not accept less):\n{must_have_block}\n\n"
        f"BEHAVIOR:\n{negotiation_block}\n\n"
        f"{facts_section}"
        f"OPENING LINE (use something like this on turn 1):\n\"{starting}\"\n\n"
        f"HANG-UP if the agent is rude, refuses to help, or loops without progress after 8 turns.\n\n"
        f"GOAL COMPLETION (output [GOAL_ACHIEVED] when):\n{resolution or high_level}\n"
        f"\nIMPORTANT: When your goal completion condition above is met — including when the agent "
        f"denies a bypass request but gives you the required explanation or confirmation — "
        f"output [GOAL_ACHIEVED] to end the call. Use [HANGUP] only if you give up without "
        f"reaching your goal.\n"
    )


def eva_record_to_scenario(record: dict[str, Any]) -> EvaScenario:
    """Convert a raw EVA-Bench record into an EvaScenario."""
    domain = str(record.get("domain", "airline_csm"))
    user_goal = _parse_json_field(record.get("user_goal"))
    user_config = _parse_json_field(record.get("user_config"))
    scenario_context = _parse_json_field(record.get("scenario_context"))
    decision_tree = user_goal.get("decision_tree", {})

    must_have = decision_tree.get("must_have_criteria", [])
    negotiation = decision_tree.get("negotiation_behavior", [])
    high_level = user_goal.get("high_level_user_goal", "Complete the support request.")

    hangup_triggers = [
        "Agent is rude or dismissive",
        "Agent loops on the same answer without progress",
        "Agent refuses to authenticate or proceed",
    ]
    behavior_rules = negotiation[:4] if negotiation else ["State your goal clearly", "Push back if must-haves are not met"]

    scenario_db = _parse_json_field(
        record.get("initial_scenario_database") or record.get("initial_scenario_db")
    )
    ground_truth = _parse_json_field(record.get("ground_truth"))
    caller_facts = build_caller_facts(
        domain=domain,
        scenario_database=scenario_db,
        ground_truth=ground_truth,
        user_config=user_config,
    )

    persona_prompt = _build_persona_prompt(
        user_config=user_config,
        user_goal=user_goal,
        scenario_context=scenario_context,
        must_have=must_have,
        negotiation=negotiation,
        caller_facts=caller_facts,
    )

    eva_id = str(record.get("id", record.get("eva_id", "unknown")))
    domain_label = DOMAIN_LABELS.get(domain, domain)

    description_parts = [
        f"EVA-Bench {domain_label} scenario ({eva_id}).",
        scenario_context.get("premise", ""),
        f"Caller goal: {high_level}",
    ]

    return EvaScenario(
        eva_id=eva_id,
        domain=domain,
        domain_label=domain_label,
        scenario_name=_scenario_title(domain, eva_id, user_config),
        scenario_description=" ".join(part for part in description_parts if part).strip(),
        caller_personality="enterprise",
        caller_goal=high_level,
        difficulty_level=DOMAIN_DIFFICULTY.get(domain, "medium"),
        hangup_triggers=hangup_triggers,
        behavior_rules=behavior_rules,
        persona_prompt=persona_prompt,
        must_have_criteria=list(must_have),
        starting_utterance=str(user_goal.get("starting_utterance", "")),
        tool_density=DOMAIN_TOOL_DENSITY.get(domain, "medium"),
    )
