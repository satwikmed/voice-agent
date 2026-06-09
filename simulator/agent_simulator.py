"""
VoiceIQ Agent Simulator — Two-LLM conversation loop.

Runs a simulated conversation between a voice agent (LLM 1) and a caller
(LLM 2) driven by scenario definitions. The agent uses a configurable
system prompt while the caller follows the scenario's persona_prompt,
which encodes personality, goals, behaviour rules, and explicit hang-up
conditions.

Uses the ``openai`` Python library for all LLM calls.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from openai import AsyncOpenAI
from dotenv import load_dotenv

from simulator.scenarios import SCENARIOS, Scenario  # noqa: F401 – re-exported for convenience

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MAX_TURNS: int = 20
AGENT_TEMPERATURE: float = 0.7
CALLER_TEMPERATURE: float = 0.8

# Sentinel tokens the caller LLM emits to signal end-of-call events.
HANGUP_TOKEN: str = "[HANGUP]"
GOAL_ACHIEVED_TOKEN: str = "[GOAL_ACHIEVED]"

logger = logging.getLogger(__name__)

# Initialize OpenAI Client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def is_ollama_available() -> bool:
    """Always return true since we transitioned to OpenAI API."""
    return True


def _build_caller_system_prompt(persona_prompt: str) -> str:
    """Wrap the scenario's persona_prompt with explicit output instructions.

    The wrapper tells the caller LLM to emit ``[HANGUP]`` or
    ``[GOAL_ACHIEVED]`` tokens so that the loop can detect termination
    conditions reliably.
    """
    return (
        f"{persona_prompt}\n\n"
        "--- OUTPUT RULES ---\n"
        "You are roleplaying as a caller in a phone conversation. "
        "Respond naturally in character.\n"
        "When you decide to hang up the phone (for any reason — frustration, "
        "rudeness, or any of your hang-up triggers), output exactly "
        "'[HANGUP]' on its own line at the END of your message.\n"
        "When your goal has been fully achieved and you are satisfied, output "
        "exactly '[GOAL_ACHIEVED]' on its own line at the END of your message.\n"
        "Do NOT output both tokens in the same message. "
        "Do NOT output either token unless the condition truly applies.\n"
        "--- END OUTPUT RULES ---"
    )


def _detect_termination(caller_message: str) -> tuple[bool, bool]:
    """Parse a caller message for termination tokens.

    Returns:
        A tuple ``(goal_achieved, hung_up)``.
    """
    goal_achieved = GOAL_ACHIEVED_TOKEN in caller_message
    hung_up = HANGUP_TOKEN in caller_message
    return goal_achieved, hung_up


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------


async def run_simulation(
    agent_system_prompt: str,
    scenario: Scenario,
) -> dict[str, Any]:
    """Run a full agent ↔ caller simulation and return the results.

    Parameters
    ----------
    agent_system_prompt:
        The system prompt that configures the voice-agent LLM.
    scenario:
        A :class:`Scenario` instance describing the caller persona, goals,
        and hang-up conditions.

    Returns
    -------
    dict
        ``transcript``  – list of ``{role, content, turn}`` dicts.
        "total_turns" – number of conversational turns completed.
        "goal_completed" – whether the caller's goal was achieved.
    """
    logger.info(
        "Starting simulation for scenario '%s' (difficulty=%s) with model '%s'.",
        scenario.scenario_name,
        scenario.difficulty_level,
        OPENAI_MODEL,
    )

    caller_system_prompt = _build_caller_system_prompt(scenario.persona_prompt)

    # Conversation histories (each side keeps its own view).
    agent_messages: list[dict[str, str]] = [
        {"role": "system", "content": agent_system_prompt},
    ]
    caller_messages: list[dict[str, str]] = [
        {"role": "system", "content": caller_system_prompt},
    ]

    transcript: list[dict[str, Any]] = []
    goal_completed: bool = False
    turn: int = 0

    for turn in range(1, MAX_TURNS + 1):
        # --- Agent turn ---------------------------------------------------
        logger.debug("Turn %d – agent generating response…", turn)
        try:
            agent_response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=agent_messages,
                temperature=AGENT_TEMPERATURE
            )
        except Exception:
            logger.exception("OpenAI call failed on agent turn %d.", turn)
            raise

        agent_text: str = agent_response.choices[0].message.content or ""
        logger.debug("Turn %d – agent: %s", turn, agent_text[:120])

        transcript.append({"role": "agent", "content": agent_text, "turn": turn})

        # Feed agent's utterance into both histories.
        agent_messages.append({"role": "assistant", "content": agent_text})
        caller_messages.append({"role": "user", "content": agent_text})

        # --- Caller turn ---------------------------------------------------
        logger.debug("Turn %d – caller generating response…", turn)
        try:
            caller_response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=caller_messages,
                temperature=CALLER_TEMPERATURE
            )
        except Exception:
            logger.exception("OpenAI call failed on caller turn %d.", turn)
            raise

        caller_text: str = caller_response.choices[0].message.content or ""
        logger.debug("Turn %d – caller: %s", turn, caller_text[:120])

        transcript.append({"role": "caller", "content": caller_text, "turn": turn})

        # Feed caller's utterance into both histories.
        caller_messages.append({"role": "assistant", "content": caller_text})
        agent_messages.append({"role": "user", "content": caller_text})

        # --- Check termination ---------------------------------------------
        goal_achieved, hung_up = _detect_termination(caller_text)

        if goal_achieved:
            logger.info(
                "Scenario '%s' — caller goal achieved at turn %d.",
                scenario.scenario_name,
                turn,
            )
            goal_completed = True
            break

        if hung_up:
            logger.info(
                "Scenario '%s' — caller hung up at turn %d.",
                scenario.scenario_name,
                turn,
            )
            break

    else:
        logger.warning(
            "Scenario '%s' — max turns (%d) reached without resolution.",
            scenario.scenario_name,
            MAX_TURNS,
        )

    result: dict[str, Any] = {
        "transcript": transcript,
        "total_turns": turn,
        "goal_completed": goal_completed,
    }

    logger.info(
        "Simulation complete: %d turns, goal_completed=%s.",
        turn,
        goal_completed,
    )
    return result


# ---------------------------------------------------------------------------
# Sync wrapper
# ---------------------------------------------------------------------------


def run_simulation_sync(
    agent_system_prompt: str,
    scenario: Scenario,
) -> dict[str, Any]:
    """Synchronous wrapper around :func:`run_simulation`.

    Creates a new event loop if none is running, or uses
    ``asyncio.run`` for a clean lifecycle.
    """
    return asyncio.run(run_simulation(agent_system_prompt, scenario))

