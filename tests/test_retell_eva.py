"""
Tests for RetellEVA — EVA-Bench mapping and scoring.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from retell_eva.loader import load_eva_scenarios
from retell_eva.mapper import eva_record_to_scenario
from retell_eva.scorer import aggregate_benchmark, score_eva_run


SAMPLE_EVA_RECORD = {
    "id": "1.1.2",
    "domain": "airline_csm",
    "user_goal": json.dumps(
        {
            "high_level_user_goal": "Rebook flight to March 25 under $120.",
            "starting_utterance": "Hi, I need to change my flight.",
            "decision_tree": {
                "must_have_criteria": ["Date is March 25", "Cost under $120"],
                "negotiation_behavior": ["Ask for total cost before confirming"],
                "resolution_condition": "Rebooking confirmed with window seat.",
            },
        }
    ),
    "user_config": json.dumps({"name": "Samantha Rodriguez", "gender": "woman"}),
    "scenario_context": json.dumps(
        {"premise": "Passenger needs to move AUS to LAX flight."}
    ),
}


class TestEvaMapper:
    def test_maps_eva_record_to_scenario(self):
        scenario = eva_record_to_scenario(SAMPLE_EVA_RECORD)
        assert scenario.eva_id == "1.1.2"
        assert scenario.domain == "airline_csm"
        assert "Samantha Rodriguez" in scenario.persona_prompt
        assert "[GOAL_ACHIEVED]" in scenario.persona_prompt or "GOAL COMPLETION" in scenario.persona_prompt
        assert len(scenario.must_have_criteria) == 2

    def test_injects_caller_verification_facts(self):
        from retell_eva.caller_facts import build_caller_facts

        record = {
            "id": "1.1",
            "domain": "healthcare_hrsd",
            "user_config": json.dumps({"name": "Priya Sharma", "gender": "woman"}),
            "user_goal": SAMPLE_EVA_RECORD["user_goal"],
            "scenario_context": json.dumps({"premise": "License extension."}),
            "initial_scenario_database": json.dumps(
                {
                    "providers": {
                        "3746317213": {
                            "npi": "3746317213",
                            "first_name": "Priya",
                            "last_name": "Sharma",
                            "facility_code": "KAFN-13R",
                            "pin": "4257",
                            "employee_id": "EMP126225",
                            "licenses": {
                                "FL-MD-30058838": {
                                    "state_license_number": "FL-MD-30058838",
                                    "state_code": "FL",
                                }
                            },
                        }
                    }
                }
            ),
            "ground_truth": json.dumps({"expected_scenario_db": {"providers": {}}}),
        }
        scenario = eva_record_to_scenario(record)
        assert "3746317213" in scenario.persona_prompt
        assert "4257" in scenario.persona_prompt
        facts = build_caller_facts(
            domain="healthcare_hrsd",
            scenario_database=json.loads(record["initial_scenario_database"]),
            ground_truth=json.loads(record["ground_truth"]),
            user_config={"name": "Priya Sharma"},
        )
        assert facts["NPI"] == "3746317213"
        assert facts["4-digit PIN"] == "4257"

    def test_domain_difficulty_mapping(self):
        airline = eva_record_to_scenario({**SAMPLE_EVA_RECORD, "domain": "airline_csm"})
        healthcare = eva_record_to_scenario(
            {**SAMPLE_EVA_RECORD, "domain": "healthcare_hrsd", "id": "2.1.1"}
        )
        assert airline.difficulty_level == "medium"
        assert healthcare.difficulty_level == "hard"


class TestEvaScorer:
    def test_high_scores_pass(self):
        result = score_eva_run(
            goal_completed=True,
            judge_scores={
                "goal_completion": 90,
                "response_relevance": 85,
                "conversation_flow": 88,
                "empathy": 80,
                "objection_handling": 75,
            },
        )
        assert result.eva_a_pass is True
        assert result.eva_x_pass is True
        assert result.composite_pass is True

    def test_low_task_completion_fails_eva_a(self):
        result = score_eva_run(
            goal_completed=False,
            judge_scores={
                "goal_completion": 30,
                "response_relevance": 70,
                "conversation_flow": 75,
                "empathy": 70,
                "objection_handling": 65,
            },
        )
        assert result.eva_a_pass is False

    def test_aggregate_benchmark(self):
        runs = [
            {"domain": "airline_csm", "eva_a": 0.8, "eva_x": 0.75, "eva_a_pass": True, "eva_x_pass": True, "composite_pass": True},
            {"domain": "healthcare_hrsd", "eva_a": 0.5, "eva_x": 0.7, "eva_a_pass": False, "eva_x_pass": True, "composite_pass": False},
        ]
        summary = aggregate_benchmark(runs)
        assert summary["scenario_count"] == 2
        assert summary["composite_pass_at_1"] == 0.5
        assert "airline_csm" in summary["by_domain"]


class TestBundledScenarios:
    def test_bundled_scenarios_load(self):
        path = Path(__file__).resolve().parent.parent / "retell_eva" / "data" / "eva-scenarios.json"
        assert path.exists(), "Run scripts/sync_eva_scenarios.py first"
        scenarios = load_eva_scenarios()
        assert len(scenarios) == 15
        domains = {s.domain for s in scenarios}
        assert domains == {"airline_csm", "healthcare_hrsd", "enterprise_itsm"}

    def test_all_scenarios_have_persona(self):
        for scenario in load_eva_scenarios():
            assert scenario.persona_prompt.strip()
            assert scenario.starting_utterance.strip()
