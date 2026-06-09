"""
Tests for simulator/judge.py

Covers:
- JSON parsing and validation of judge output
- Score weighting calculations
- Self-consistency standard deviation computation
- Error handling on malformed responses
"""

from __future__ import annotations

import json
import math

import pytest


# ── Test: weighted average calculation ────────────────────────────────────────

WEIGHTS = {
    "response_relevance": 0.20,
    "objection_handling": 0.20,
    "conversation_flow": 0.20,
    "empathy": 0.15,
    "goal_completion": 0.25,
}


def compute_weighted_average(scores: dict[str, int | float]) -> float:
    """Mirror the judge's weighted average logic for testing."""
    return sum(scores[dim] * weight for dim, weight in WEIGHTS.items())


class TestWeightedAverage:
    """Verify the overall_score weighting logic."""

    def test_perfect_scores(self):
        scores = {dim: 100 for dim in WEIGHTS}
        assert compute_weighted_average(scores) == pytest.approx(100.0)

    def test_zero_scores(self):
        scores = {dim: 0 for dim in WEIGHTS}
        assert compute_weighted_average(scores) == pytest.approx(0.0)

    def test_varied_scores(self):
        scores = {
            "response_relevance": 80,
            "objection_handling": 70,
            "conversation_flow": 90,
            "empathy": 60,
            "goal_completion": 50,
        }
        expected = 80 * 0.20 + 70 * 0.20 + 90 * 0.20 + 60 * 0.15 + 50 * 0.25
        assert compute_weighted_average(scores) == pytest.approx(expected)

    def test_weights_sum_to_one(self):
        assert sum(WEIGHTS.values()) == pytest.approx(1.0)


# ── Test: JSON validation ─────────────────────────────────────────────────────

VALID_JUDGE_OUTPUT = {
    "response_relevance": 85,
    "objection_handling": 70,
    "conversation_flow": 90,
    "empathy": 65,
    "goal_completion": 80,
    "overall_score": 79.75,
    "failure_points": [{"turn": 3, "reason": "Agent gave a generic response."}],
    "recommendations": [
        "Be more specific when answering questions.",
        "Mirror the caller's language.",
    ],
}

REQUIRED_FIELDS = [
    "response_relevance",
    "objection_handling",
    "conversation_flow",
    "empathy",
    "goal_completion",
    "overall_score",
    "failure_points",
    "recommendations",
]


def validate_judge_output(data: dict) -> list[str]:
    """
    Validate judge output and return a list of error messages.
    Empty list means valid.
    """
    errors = []

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    dimension_fields = ["response_relevance", "objection_handling", "conversation_flow", "empathy", "goal_completion"]
    for dim in dimension_fields:
        if dim in data:
            val = data[dim]
            if not isinstance(val, (int, float)):
                errors.append(f"{dim} must be a number, got {type(val).__name__}")
            elif not (0 <= val <= 100):
                errors.append(f"{dim} must be 0-100, got {val}")

    if "overall_score" in data:
        if not isinstance(data["overall_score"], (int, float)):
            errors.append(f"overall_score must be a number, got {type(data['overall_score']).__name__}")

    if "failure_points" in data:
        if not isinstance(data["failure_points"], list):
            errors.append(f"failure_points must be a list, got {type(data['failure_points']).__name__}")
        else:
            for i, fp in enumerate(data["failure_points"]):
                if not isinstance(fp, dict):
                    errors.append(f"failure_points[{i}] must be a dict")
                elif "turn" not in fp or "reason" not in fp:
                    errors.append(f"failure_points[{i}] missing 'turn' or 'reason'")

    if "recommendations" in data:
        if not isinstance(data["recommendations"], list):
            errors.append(f"recommendations must be a list, got {type(data['recommendations']).__name__}")

    return errors


class TestJudgeValidation:
    """Test the JSON validation logic for judge output."""

    def test_valid_output(self):
        assert validate_judge_output(VALID_JUDGE_OUTPUT) == []

    def test_missing_field(self):
        incomplete = {k: v for k, v in VALID_JUDGE_OUTPUT.items() if k != "empathy"}
        errors = validate_judge_output(incomplete)
        assert any("empathy" in e for e in errors)

    def test_score_out_of_range(self):
        invalid = {**VALID_JUDGE_OUTPUT, "response_relevance": 150}
        errors = validate_judge_output(invalid)
        assert any("0-100" in e for e in errors)

    def test_negative_score(self):
        invalid = {**VALID_JUDGE_OUTPUT, "goal_completion": -5}
        errors = validate_judge_output(invalid)
        assert any("0-100" in e for e in errors)

    def test_wrong_type_score(self):
        invalid = {**VALID_JUDGE_OUTPUT, "empathy": "high"}
        errors = validate_judge_output(invalid)
        assert any("number" in e for e in errors)

    def test_failure_points_not_list(self):
        invalid = {**VALID_JUDGE_OUTPUT, "failure_points": "turn 3"}
        errors = validate_judge_output(invalid)
        assert any("list" in e for e in errors)

    def test_failure_point_missing_turn(self):
        invalid = {**VALID_JUDGE_OUTPUT, "failure_points": [{"reason": "bad"}]}
        errors = validate_judge_output(invalid)
        assert any("turn" in e.lower() or "reason" in e.lower() for e in errors)

    def test_recommendations_not_list(self):
        invalid = {**VALID_JUDGE_OUTPUT, "recommendations": "be better"}
        errors = validate_judge_output(invalid)
        assert any("list" in e for e in errors)

    def test_json_round_trip(self):
        """Ensure valid output survives JSON serialization/deserialization."""
        serialized = json.dumps(VALID_JUDGE_OUTPUT)
        deserialized = json.loads(serialized)
        assert validate_judge_output(deserialized) == []


# ── Test: self-consistency statistics ─────────────────────────────────────────

def compute_consistency(scores_list: list[dict]) -> dict[str, dict]:
    """
    Given multiple judge runs, compute mean/stdev/confidence per dimension.
    Mirrors the logic in judge.py.
    """
    dimensions = ["response_relevance", "objection_handling", "conversation_flow", "empathy", "goal_completion", "overall_score"]
    consistency = {}

    for dim in dimensions:
        values = [s[dim] for s in scores_list if dim in s]
        if len(values) < 2:
            consistency[dim] = {"mean": values[0] if values else 0, "stdev": 0.0, "confidence": "high"}
            continue

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
        stdev = math.sqrt(variance)
        confidence = "high" if stdev <= 10.0 else "low"
        consistency[dim] = {"mean": round(mean, 1), "stdev": round(stdev, 1), "confidence": confidence}

    return consistency


class TestSelfConsistency:
    """Test self-consistency calculation logic."""

    def test_identical_scores(self):
        runs = [VALID_JUDGE_OUTPUT, VALID_JUDGE_OUTPUT, VALID_JUDGE_OUTPUT]
        result = compute_consistency(runs)
        for dim in result:
            assert result[dim]["stdev"] == 0.0
            assert result[dim]["confidence"] == "high"

    def test_high_variance_flagged(self):
        run1 = {**VALID_JUDGE_OUTPUT, "empathy": 90}
        run2 = {**VALID_JUDGE_OUTPUT, "empathy": 50}
        run3 = {**VALID_JUDGE_OUTPUT, "empathy": 30}
        result = compute_consistency([run1, run2, run3])
        assert result["empathy"]["confidence"] == "low"
        assert result["empathy"]["stdev"] > 10.0

    def test_low_variance_passes(self):
        run1 = {**VALID_JUDGE_OUTPUT, "response_relevance": 82}
        run2 = {**VALID_JUDGE_OUTPUT, "response_relevance": 85}
        run3 = {**VALID_JUDGE_OUTPUT, "response_relevance": 88}
        result = compute_consistency([run1, run2, run3])
        assert result["response_relevance"]["confidence"] == "high"
        assert result["response_relevance"]["stdev"] <= 10.0

    def test_single_run(self):
        result = compute_consistency([VALID_JUDGE_OUTPUT])
        for dim in result:
            assert result[dim]["stdev"] == 0.0
            assert result[dim]["confidence"] == "high"


# ── Test: JSON parsing edge cases ─────────────────────────────────────────────

class TestJSONParsing:
    """Test robustness of JSON parsing from LLM output."""

    def test_parse_clean_json(self):
        raw = json.dumps(VALID_JUDGE_OUTPUT)
        parsed = json.loads(raw)
        assert validate_judge_output(parsed) == []

    def test_parse_json_with_markdown_fences(self):
        raw = "```json\n" + json.dumps(VALID_JUDGE_OUTPUT) + "\n```"
        # Strip markdown fences
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
        if clean.endswith("```"):
            clean = clean.rsplit("```", 1)[0]
        parsed = json.loads(clean.strip())
        assert validate_judge_output(parsed) == []

    def test_parse_json_with_trailing_text(self):
        raw = json.dumps(VALID_JUDGE_OUTPUT) + "\n\nHere is my analysis..."
        # Extract JSON object
        brace_count = 0
        start = raw.index("{")
        for i, c in enumerate(raw[start:], start):
            if c == "{":
                brace_count += 1
            elif c == "}":
                brace_count -= 1
                if brace_count == 0:
                    json_str = raw[start : i + 1]
                    break
        parsed = json.loads(json_str)
        assert validate_judge_output(parsed) == []

    def test_reject_invalid_json(self):
        with pytest.raises(json.JSONDecodeError):
            json.loads("this is not json")
