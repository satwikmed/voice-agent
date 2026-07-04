"""
RetellEVA benchmark runner — simulate + judge + score EVA-Bench scenarios.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass
from typing import Any

from retell_eva.agent_prompts import build_eva_agent_prompt
from retell_eva.loader import EvaScenario, load_eva_scenarios
from retell_eva.scorer import aggregate_benchmark, score_eva_run
from simulator.agent_simulator import run_simulation
from simulator.judge import evaluate_transcript
from simulator.scenarios import Scenario

logger = logging.getLogger(__name__)


def _eva_to_voiceiq_scenario(eva: EvaScenario, numeric_id: int) -> Scenario:
    return Scenario(
        id=numeric_id,
        scenario_name=eva.scenario_name,
        scenario_description=eva.scenario_description,
        caller_personality=eva.caller_personality,
        caller_goal=eva.caller_goal,
        difficulty_level=eva.difficulty_level,
        hangup_triggers=list(eva.hangup_triggers),
        behavior_rules=list(eva.behavior_rules),
        persona_prompt=eva.persona_prompt,
    )


@dataclass
class EvaRunResult:
    eva_id: str
    domain: str
    domain_label: str
    scenario_name: str
    goal_completed: bool
    total_turns: int
    overall_score: float
    eva_a: float
    eva_x: float
    eva_a_pass: bool
    eva_x_pass: bool
    composite_pass: bool
    scores_breakdown: dict[str, float]
    failure_points: list[dict[str, Any]]
    recommendations: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


async def run_eva_scenario(
    eva: EvaScenario,
    *,
    agent_prompt: str | None = None,
    numeric_id: int = 9000,
) -> EvaRunResult:
    """Run a single EVA scenario against a Retell-style agent prompt."""
    prompt = build_eva_agent_prompt(eva, agent_prompt)
    scenario = _eva_to_voiceiq_scenario(eva, numeric_id)

    sim = await run_simulation(
        prompt,
        scenario,
        caller_opener=eva.starting_utterance or None,
        agent_temperature=0.3,
        caller_temperature=0.5,
    )
    judge = await evaluate_transcript(sim["transcript"], eva.scenario_description)

    eva_scores = score_eva_run(
        goal_completed=bool(sim["goal_completed"]),
        judge_scores=judge,
    )

    return EvaRunResult(
        eva_id=eva.eva_id,
        domain=eva.domain,
        domain_label=eva.domain_label,
        scenario_name=eva.scenario_name,
        goal_completed=bool(sim["goal_completed"]),
        total_turns=int(sim["total_turns"]),
        overall_score=float(judge["overall_score"]),
        eva_a=eva_scores.eva_a,
        eva_x=eva_scores.eva_x,
        eva_a_pass=eva_scores.eva_a_pass,
        eva_x_pass=eva_scores.eva_x_pass,
        composite_pass=eva_scores.composite_pass,
        scores_breakdown={
            "response_relevance": judge["response_relevance"],
            "objection_handling": judge["objection_handling"],
            "conversation_flow": judge["conversation_flow"],
            "empathy": judge["empathy"],
            "goal_completion": judge["goal_completion"],
        },
        failure_points=judge.get("failure_points", []),
        recommendations=judge.get("recommendations", []),
    )


async def run_eva_benchmark(
    *,
    domain: str | None = None,
    limit: int | None = None,
    agent_prompt: str | None = None,
) -> dict[str, Any]:
    """Run a benchmark suite and return aggregated results."""
    scenarios = load_eva_scenarios(domain=domain, limit=limit)
    results: list[EvaRunResult] = []

    for index, eva in enumerate(scenarios):
        logger.info("Running EVA scenario %s (%d/%d)", eva.eva_id, index + 1, len(scenarios))
        result = await run_eva_scenario(eva, agent_prompt=agent_prompt, numeric_id=9000 + index)
        results.append(result)

    run_dicts = [r.as_dict() for r in results]
    summary = aggregate_benchmark(run_dicts)
    return {
        "summary": summary,
        "runs": run_dicts,
    }


def run_eva_benchmark_sync(**kwargs: Any) -> dict[str, Any]:
    return asyncio.run(run_eva_benchmark(**kwargs))
