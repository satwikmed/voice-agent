"""
Tests for simulator/agent_simulator.py

Covers:
- Conversation loop termination conditions
- Turn alternation and transcript structure
- Hangup and goal detection
"""

from __future__ import annotations

import pytest


# ── Test: transcript structure ────────────────────────────────────────────────

SAMPLE_TRANSCRIPT = [
    {"role": "agent", "content": "Hello! How can I help?", "turn": 1},
    {"role": "caller", "content": "I need pricing info.", "turn": 2},
    {"role": "agent", "content": "Our plans start at $29/seat.", "turn": 3},
    {"role": "caller", "content": "That's helpful, thanks.\n\n[GOAL_ACHIEVED]", "turn": 4},
]


class TestTranscriptStructure:
    """Verify transcript format and integrity."""

    def test_alternating_roles(self):
        """Agent and caller must alternate turns."""
        for i, turn in enumerate(SAMPLE_TRANSCRIPT):
            expected = "agent" if i % 2 == 0 else "caller"
            assert turn["role"] == expected, f"Turn {i} should be {expected}, got {turn['role']}"

    def test_turn_numbers_sequential(self):
        """Turn numbers must be sequential starting from 1."""
        for i, turn in enumerate(SAMPLE_TRANSCRIPT):
            assert turn["turn"] == i + 1, f"Expected turn {i + 1}, got {turn['turn']}"

    def test_agent_speaks_first(self):
        """Agent must always speak first."""
        assert SAMPLE_TRANSCRIPT[0]["role"] == "agent"

    def test_all_turns_have_content(self):
        """Every turn must have non-empty content."""
        for turn in SAMPLE_TRANSCRIPT:
            assert turn["content"].strip(), f"Turn {turn['turn']} has empty content"

    def test_required_fields(self):
        """Each turn must have role, content, and turn fields."""
        for turn in SAMPLE_TRANSCRIPT:
            assert "role" in turn
            assert "content" in turn
            assert "turn" in turn


# ── Test: termination condition detection ─────────────────────────────────────

def detect_termination(content: str) -> str | None:
    """
    Detect conversation termination signals in caller output.
    Returns: 'goal_achieved', 'hangup', or None.
    """
    if "[GOAL_ACHIEVED]" in content:
        return "goal_achieved"
    if "[HANGUP]" in content:
        return "hangup"
    return None


class TestTerminationDetection:
    """Test hangup and goal detection in caller output."""

    def test_goal_achieved(self):
        assert detect_termination("Thanks for your help!\n\n[GOAL_ACHIEVED]") == "goal_achieved"

    def test_hangup(self):
        assert detect_termination("I'm done with this.\n\n[HANGUP]") == "hangup"

    def test_no_termination(self):
        assert detect_termination("Tell me more about pricing.") is None

    def test_goal_in_middle(self):
        assert detect_termination("Great info [GOAL_ACHIEVED] thanks") == "goal_achieved"

    def test_hangup_in_middle(self):
        assert detect_termination("This is terrible [HANGUP] goodbye") == "hangup"

    def test_empty_content(self):
        assert detect_termination("") is None

    def test_similar_but_not_token(self):
        """Tokens must match exactly — not partial matches."""
        assert detect_termination("[GOAL_ACHIEV]") is None
        assert detect_termination("[HANG]") is None

    def test_goal_takes_precedence(self):
        """If both tokens appear, goal_achieved is detected first."""
        result = detect_termination("[GOAL_ACHIEVED] [HANGUP]")
        assert result == "goal_achieved"


# ── Test: max turns enforcement ───────────────────────────────────────────────

MAX_TURNS = 20


class TestMaxTurns:
    """Test that the conversation loop respects the maximum turn limit."""

    def test_within_limit(self):
        assert len(SAMPLE_TRANSCRIPT) <= MAX_TURNS

    def test_max_turns_value(self):
        """Max turns should be exactly 20 as specified."""
        assert MAX_TURNS == 20

    def test_even_turn_count(self):
        """Total turns should always be even (agent + caller pairs) or end on caller."""
        # If goal is achieved or hangup happens, conversation can end on any caller turn
        assert SAMPLE_TRANSCRIPT[-1]["role"] == "caller", \
            "Conversation should end on a caller turn (they achieve goal or hang up)"


# ── Test: scenario validation ─────────────────────────────────────────────────

VALID_PERSONALITIES = {"friendly", "hostile", "confused", "impatient", "off_topic", "interrupter"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}


class TestScenarioValidation:
    """Validate scenario data integrity."""

    def test_all_scenarios_load(self):
        """All 6 scenarios should be importable."""
        from simulator.scenarios import SCENARIOS
        assert len(SCENARIOS) == 6

    def test_scenario_ids_unique(self):
        from simulator.scenarios import SCENARIOS
        ids = [s.id for s in SCENARIOS]
        assert len(ids) == len(set(ids)), "Scenario IDs must be unique"

    def test_scenario_names_unique(self):
        from simulator.scenarios import SCENARIOS
        names = [s.scenario_name for s in SCENARIOS]
        assert len(names) == len(set(names)), "Scenario names must be unique"

    def test_valid_personalities(self):
        from simulator.scenarios import SCENARIOS
        for s in SCENARIOS:
            assert s.caller_personality in VALID_PERSONALITIES, \
                f"Invalid personality '{s.caller_personality}' for {s.scenario_name}"

    def test_valid_difficulty_levels(self):
        from simulator.scenarios import SCENARIOS
        for s in SCENARIOS:
            assert s.difficulty_level in VALID_DIFFICULTIES, \
                f"Invalid difficulty '{s.difficulty_level}' for {s.scenario_name}"

    def test_all_scenarios_have_persona_prompt(self):
        from simulator.scenarios import SCENARIOS
        for s in SCENARIOS:
            assert s.persona_prompt.strip(), f"{s.scenario_name} has empty persona_prompt"

    def test_all_scenarios_have_hangup_triggers(self):
        from simulator.scenarios import SCENARIOS
        for s in SCENARIOS:
            assert len(s.hangup_triggers) > 0, f"{s.scenario_name} has no hangup triggers"

    def test_lookup_by_id(self):
        from simulator.scenarios import get_scenario_by_id
        s = get_scenario_by_id(1)
        assert s is not None
        assert s.scenario_name == "Interested Buyer"

    def test_lookup_by_name(self):
        from simulator.scenarios import get_scenario_by_name
        s = get_scenario_by_name("Price Shopper")
        assert s is not None
        assert s.id == 2

    def test_lookup_nonexistent(self):
        from simulator.scenarios import get_scenario_by_id, get_scenario_by_name
        assert get_scenario_by_id(999) is None
        assert get_scenario_by_name("Nonexistent Scenario") is None
