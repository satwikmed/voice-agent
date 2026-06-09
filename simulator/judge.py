"""
VoiceIQ LLM Judge — Calibrated transcript evaluator.

Evaluates a simulated agent ↔ caller conversation transcript across five
quality dimensions and returns a structured JSON scorecard.  Supports
single-shot evaluation as well as a self-consistency mode that averages
three independent judgements to surface scoring variance.

Uses the ``openai`` Python library for all LLM calls.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import statistics
from typing import Any

from openai import AsyncOpenAI
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

JUDGE_TEMPERATURE: float = 0.1
MAX_RETRIES: int = 3
CONSISTENCY_RUNS: int = 3

# Initialize OpenAI Client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# Weights for the weighted-average ``overall_score``.
DIMENSION_WEIGHTS: dict[str, float] = {
    "response_relevance": 0.20,
    "objection_handling": 0.20,
    "conversation_flow": 0.20,
    "empathy": 0.15,
    "goal_completion": 0.25,
}

DIMENSIONS: list[str] = list(DIMENSION_WEIGHTS.keys())

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_JUDGE_SYSTEM_PROMPT: str = """\
You are a STRICT, CALIBRATED scoring judge for voice-agent conversations.

You will receive:
1. A scenario description that defines the caller's goal and personality.
2. A full conversation transcript (list of turns with role and content).

Score the AGENT's performance on each dimension below using an integer 0–100.

### Dimensions
- **response_relevance** (0-100): Did the agent's responses directly address \
the caller's questions and needs? Reference specific turns where the agent \
was on-topic or off-topic.
- **objection_handling** (0-100): How well did the agent handle pushback, \
complaints, or difficult questions? Cite turns where objections arose and \
how the agent responded.
- **conversation_flow** (0-100): Was the conversation natural and well-paced? \
Were there awkward pauses, repetitions, or non-sequiturs? Reference turns.
- **empathy** (0-100): Did the agent acknowledge the caller's emotions, \
frustrations, or concerns? Cite specific empathetic (or un-empathetic) \
moments by turn number.
- **goal_completion** (0-100): To what extent was the caller's stated goal \
achieved? 100 = fully achieved, 0 = not at all. Reference the turns that \
contributed to or blocked goal completion.

### Rules
- Every score MUST be justified by referencing specific turn numbers. \
No vibes-based scoring.
- Provide 2–4 actionable recommendations for the agent.
- Identify failure points: turns where the agent made a clear mistake.

### Output format — STRICT JSON, nothing else
Return ONLY a JSON object (no markdown fences, no commentary) with this \
exact schema:

{
  "response_relevance": <int 0-100>,
  "objection_handling": <int 0-100>,
  "conversation_flow": <int 0-100>,
  "empathy": <int 0-100>,
  "goal_completion": <int 0-100>,
  "overall_score": <float 0-100>,
  "failure_points": [{"turn": <int>, "reason": "<string>"}],
  "recommendations": ["<string>", ...]
}

overall_score is a weighted average:
  response_relevance × 0.20
  objection_handling × 0.20
  conversation_flow  × 0.20
  empathy            × 0.15
  goal_completion    × 0.25
"""


def _build_user_prompt(
    transcript: list[dict[str, Any]],
    scenario_description: str,
) -> str:
    """Format the transcript and scenario into the user message for the judge."""
    lines: list[str] = [
        "## Scenario Description",
        scenario_description,
        "",
        "## Conversation Transcript",
    ]
    for entry in transcript:
        role = entry.get("role", "unknown").upper()
        turn = entry.get("turn", "?")
        content = entry.get("content", "")
        lines.append(f"[Turn {turn}] {role}: {content}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class JudgeResponseError(Exception):
    """Raised when the judge LLM returns an unparseable or invalid response."""


def _validate_scores(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalise the parsed judge output.

    Raises :class:`JudgeResponseError` on any schema violation.
    """
    # --- dimension scores ---
    for dim in DIMENSIONS:
        if dim not in data:
            raise JudgeResponseError(f"Missing required dimension: '{dim}'.")
        val = data[dim]
        if not isinstance(val, (int, float)):
            raise JudgeResponseError(
                f"Dimension '{dim}' must be an integer, got {type(val).__name__}."
            )
        val = int(val)
        if not 0 <= val <= 100:
            raise JudgeResponseError(
                f"Dimension '{dim}' must be 0–100, got {val}."
            )
        data[dim] = val

    # --- overall_score ---
    if "overall_score" not in data:
        raise JudgeResponseError("Missing required field: 'overall_score'.")
    overall = data["overall_score"]
    if not isinstance(overall, (int, float)):
        raise JudgeResponseError(
            f"'overall_score' must be a number, got {type(overall).__name__}."
        )
    data["overall_score"] = round(float(overall), 2)

    # --- failure_points ---
    if "failure_points" not in data:
        raise JudgeResponseError("Missing required field: 'failure_points'.")
    fps = data["failure_points"]
    if not isinstance(fps, list):
        raise JudgeResponseError("'failure_points' must be a list.")
    for i, fp in enumerate(fps):
        if not isinstance(fp, dict):
            raise JudgeResponseError(
                f"failure_points[{i}] must be a dict."
            )
        if "turn" not in fp or "reason" not in fp:
            raise JudgeResponseError(
                f"failure_points[{i}] must have 'turn' and 'reason' keys."
            )
        if not isinstance(fp["turn"], (int, float)):
            raise JudgeResponseError(
                f"failure_points[{i}]['turn'] must be an integer."
            )
        fp["turn"] = int(fp["turn"])
        fp["reason"] = str(fp["reason"])

    # --- recommendations ---
    if "recommendations" not in data:
        raise JudgeResponseError("Missing required field: 'recommendations'.")
    recs = data["recommendations"]
    if not isinstance(recs, list):
        raise JudgeResponseError("'recommendations' must be a list.")
    for i, rec in enumerate(recs):
        if not isinstance(rec, str):
            raise JudgeResponseError(
                f"recommendations[{i}] must be a string."
            )

    return data


def _recompute_overall(data: dict[str, Any]) -> float:
    """Recompute the weighted overall score from the dimension scores."""
    return round(
        sum(data[dim] * weight for dim, weight in DIMENSION_WEIGHTS.items()),
        2,
    )


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------


async def evaluate_transcript(
    transcript: list[dict[str, Any]],
    scenario_description: str,
) -> dict[str, Any]:
    """Evaluate a single transcript and return a validated scorecard.

    Parameters
    ----------
    transcript:
        List of ``{role, content, turn}`` dicts produced by the simulator.
    scenario_description:
        Free-text description of the scenario being evaluated.

    Returns
    -------
    dict
        Validated scorecard matching the judge JSON schema.

    Raises
    ------
    JudgeResponseError
        After *MAX_RETRIES* failed attempts to obtain valid JSON from the LLM.
    """
    user_prompt = _build_user_prompt(transcript, scenario_description)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        logger.debug("Judge evaluation attempt %d/%d.", attempt, MAX_RETRIES)

        try:
            response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=JUDGE_TEMPERATURE,
                response_format={"type": "json_object"}
            )
        except Exception:
            logger.exception("OpenAI call failed on judge attempt %d.", attempt)
            raise

        raw_text: str = response.choices[0].message.content or ""
        logger.debug("Judge raw output (attempt %d): %s", attempt, raw_text[:200])

        # Attempt JSON extraction — the LLM may wrap the JSON in markdown
        # fences despite instructions.
        json_text = _extract_json(raw_text)

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            last_error = JudgeResponseError(
                f"Attempt {attempt}: JSON decode failed — {exc}"
            )
            logger.warning(str(last_error))
            continue

        try:
            data = _validate_scores(data)
        except JudgeResponseError as exc:
            last_error = exc
            logger.warning("Attempt %d validation failed: %s", attempt, exc)
            continue

        # Recompute overall_score to guarantee weight correctness.
        data["overall_score"] = _recompute_overall(data)

        logger.info(
            "Judge evaluation succeeded on attempt %d (overall=%.2f).",
            attempt,
            data["overall_score"],
        )
        return data

    raise JudgeResponseError(
        f"Judge failed to produce valid JSON after {MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )


def _extract_json(text: str) -> str:
    """Extract JSON from ``text``, stripping optional markdown fences."""
    stripped = text.strip()
    # Remove ```json ... ``` wrapper if present.
    if stripped.startswith("```"):
        # Find the end of the opening fence line.
        first_newline = stripped.index("\n")
        # Find the closing fence.
        closing = stripped.rfind("```")
        if closing > first_newline:
            stripped = stripped[first_newline + 1 : closing].strip()
    return stripped


# ---------------------------------------------------------------------------
# Self-consistency evaluation
# ---------------------------------------------------------------------------


async def evaluate_with_consistency(
    transcript: list[dict[str, Any]],
    scenario_description: str,
) -> dict[str, Any]:
    """Run the judge multiple times and return averaged scores with variance.

    Executes :func:`evaluate_transcript` ``CONSISTENCY_RUNS`` times (default
    3) on the *same* transcript, then computes the mean and standard deviation
    for each scoring dimension as well as ``overall_score``.

    Returns
    -------
    dict
        Mean scores for each dimension and ``overall_score``, plus a
        ``consistency`` mapping each dimension (and ``overall_score``) to
        ``{mean, stdev, confidence}`` where *confidence* is ``'high'`` if
        ``stdev <= 10.0``, else ``'low'``.
    """
    logger.info(
        "Starting self-consistency evaluation (%d runs).", CONSISTENCY_RUNS
    )

    results: list[dict[str, Any]] = []
    for run in range(1, CONSISTENCY_RUNS + 1):
        logger.info("Consistency run %d/%d…", run, CONSISTENCY_RUNS)
        result = await evaluate_transcript(transcript, scenario_description)
        results.append(result)

    # Aggregate scores across all dimensions + overall_score.
    scored_keys: list[str] = DIMENSIONS + ["overall_score"]
    consistency: dict[str, dict[str, Any]] = {}
    mean_scores: dict[str, Any] = {}

    for key in scored_keys:
        values = [r[key] for r in results]
        mean_val = round(statistics.mean(values), 2)
        stdev_val = round(statistics.stdev(values), 2) if len(values) > 1 else 0.0
        confidence = "high" if stdev_val <= 10.0 else "low"

        mean_scores[key] = mean_val
        consistency[key] = {
            "mean": mean_val,
            "stdev": stdev_val,
            "confidence": confidence,
        }

    # Carry forward non-numeric fields from the *first* run.
    mean_scores["failure_points"] = results[0]["failure_points"]
    mean_scores["recommendations"] = results[0]["recommendations"]
    mean_scores["consistency"] = consistency

    logger.info(
        "Self-consistency evaluation complete. Overall mean=%.2f, stdev=%.2f.",
        consistency["overall_score"]["mean"],
        consistency["overall_score"]["stdev"],
    )
    return mean_scores


# ---------------------------------------------------------------------------
# Sync wrappers
# ---------------------------------------------------------------------------


def evaluate_transcript_sync(
    transcript: list[dict[str, Any]],
    scenario_description: str,
) -> dict[str, Any]:
    """Synchronous wrapper around :func:`evaluate_transcript`."""
    return asyncio.run(evaluate_transcript(transcript, scenario_description))


def evaluate_with_consistency_sync(
    transcript: list[dict[str, Any]],
    scenario_description: str,
) -> dict[str, Any]:
    """Synchronous wrapper around :func:`evaluate_with_consistency`."""
    return asyncio.run(
        evaluate_with_consistency(transcript, scenario_description)
    )
