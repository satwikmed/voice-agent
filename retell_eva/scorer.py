"""
EVA-A (Accuracy) and EVA-X (Experience) scoring for RetellEVA runs.

Aligned with ServiceNow EVA-Bench composite metrics, adapted for text-mode
pre-launch evaluation of Retell agent prompts (Phase 1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVA_A_PASS_THRESHOLD = 0.70
EVA_X_PASS_THRESHOLD = 0.70


@dataclass(frozen=True)
class EvaScores:
    eva_a: float
    eva_x: float
    eva_a_pass: bool
    eva_x_pass: bool
    eva_a_breakdown: dict[str, float]
    eva_x_breakdown: dict[str, float]
    composite_pass: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "eva_a": round(self.eva_a, 3),
            "eva_x": round(self.eva_x, 3),
            "eva_a_pass": self.eva_a_pass,
            "eva_x_pass": self.eva_x_pass,
            "eva_a_breakdown": {k: round(v, 3) for k, v in self.eva_a_breakdown.items()},
            "eva_x_breakdown": {k: round(v, 3) for k, v in self.eva_x_breakdown.items()},
            "composite_pass": self.composite_pass,
        }


def score_eva_run(
    *,
    goal_completed: bool,
    judge_scores: dict[str, float],
) -> EvaScores:
    """
    Compute EVA-A and EVA-X from simulation outcome and VoiceIQ judge scores.

    EVA-A (Accuracy): task completion + goal achievement signal
    EVA-X (Experience): conversation flow, conciseness proxy, empathy for voice
    """
    goal_completion = judge_scores.get("goal_completion", 0.0) / 100.0
    response_relevance = judge_scores.get("response_relevance", 0.0) / 100.0
    conversation_flow = judge_scores.get("conversation_flow", 0.0) / 100.0
    empathy = judge_scores.get("empathy", 0.0) / 100.0
    objection_handling = judge_scores.get("objection_handling", 0.0) / 100.0

    # EVA-A: weighted toward task completion; boost if caller signaled goal achieved
    goal_signal = 1.0 if goal_completed else 0.0
    eva_a = (
        goal_completion * 0.45
        + goal_signal * 0.35
        + response_relevance * 0.20
    )
    eva_a_breakdown = {
        "task_completion": goal_completion,
        "goal_achieved_signal": goal_signal,
        "faithfulness_proxy": response_relevance,
    }

    # EVA-X: spoken interaction quality
    eva_x = (
        conversation_flow * 0.40
        + response_relevance * 0.30
        + empathy * 0.20
        + objection_handling * 0.10
    )
    eva_x_breakdown = {
        "conversation_progression": conversation_flow,
        "spoken_conciseness_proxy": response_relevance,
        "empathy": empathy,
        "turn_taking_proxy": objection_handling,
    }

    eva_a_pass = eva_a >= EVA_A_PASS_THRESHOLD
    eva_x_pass = eva_x >= EVA_X_PASS_THRESHOLD

    return EvaScores(
        eva_a=eva_a,
        eva_x=eva_x,
        eva_a_pass=eva_a_pass,
        eva_x_pass=eva_x_pass,
        eva_a_breakdown=eva_a_breakdown,
        eva_x_breakdown=eva_x_breakdown,
        composite_pass=eva_a_pass and eva_x_pass,
    )


def aggregate_benchmark(
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate per-scenario runs into domain and overall benchmark summary."""
    if not runs:
        return {
            "scenario_count": 0,
            "eva_a_pass_at_1": 0.0,
            "eva_x_pass_at_1": 0.0,
            "composite_pass_at_1": 0.0,
            "by_domain": {},
        }

    by_domain: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        by_domain.setdefault(run["domain"], []).append(run)

    def _pass_rate(items: list[dict[str, Any]], key: str) -> float:
        if not items:
            return 0.0
        return sum(1 for item in items if item.get(key)) / len(items)

    domain_stats = {}
    for domain, items in by_domain.items():
        domain_stats[domain] = {
            "scenario_count": len(items),
            "eva_a_pass_at_1": round(_pass_rate(items, "eva_a_pass"), 3),
            "eva_x_pass_at_1": round(_pass_rate(items, "eva_x_pass"), 3),
            "composite_pass_at_1": round(_pass_rate(items, "composite_pass"), 3),
            "avg_eva_a": round(sum(item["eva_a"] for item in items) / len(items), 3),
            "avg_eva_x": round(sum(item["eva_x"] for item in items) / len(items), 3),
        }

    return {
        "scenario_count": len(runs),
        "eva_a_pass_at_1": round(_pass_rate(runs, "eva_a_pass"), 3),
        "eva_x_pass_at_1": round(_pass_rate(runs, "eva_x_pass"), 3),
        "composite_pass_at_1": round(_pass_rate(runs, "composite_pass"), 3),
        "avg_eva_a": round(sum(r["eva_a"] for r in runs) / len(runs), 3),
        "avg_eva_x": round(sum(r["eva_x"] for r in runs) / len(runs), 3),
        "by_domain": domain_stats,
    }
