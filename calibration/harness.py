"""
VoiceIQ Calibration Harness — CLI tool for human calibration of judge scores.

Presents test runs one-by-one, showing scenario context, transcript, and judge
scores, then collects a human score, failure-point annotations, and optional
notes.  Results are persisted to the ``judge_calibration`` table.

Usage::

    python -m calibration.harness           # grade up to 5 un-graded runs
    python -m calibration.harness -n 10     # grade up to 10 un-graded runs
    python -m calibration.harness --all     # include already-graded runs
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import sys
from typing import Any

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

DATABASE_PATH: str = os.getenv("DATABASE_PATH", "voiceiq.db")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def _connect(db_path: str) -> sqlite3.Connection:
    """Return a connection to the SQLite database with row-factory enabled."""
    if not os.path.exists(db_path):
        logger.error("Database file not found: %s", db_path)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _fetch_pending_runs(
    conn: sqlite3.Connection,
    limit: int,
    include_all: bool,
) -> list[sqlite3.Row]:
    """Fetch test runs that need human grading.

    Parameters
    ----------
    conn:
        Active database connection.
    limit:
        Maximum number of rows to return.
    include_all:
        If ``True``, include runs that already have a ``judge_calibration``
        entry (allows re-grading).
    """
    if include_all:
        query = """
            SELECT tr.id            AS run_id,
                   tr.scenario_id,
                   tr.conversation_transcript,
                   tr.total_turns,
                   tr.overall_score,
                   tr.scores_breakdown,
                   tr.failure_points,
                   ts.scenario_name,
                   ts.scenario_description
              FROM test_runs   tr
              JOIN test_scenarios ts ON ts.id = tr.scenario_id
             ORDER BY tr.created_at DESC
             LIMIT ?;
        """
    else:
        query = """
            SELECT tr.id            AS run_id,
                   tr.scenario_id,
                   tr.conversation_transcript,
                   tr.total_turns,
                   tr.overall_score,
                   tr.scores_breakdown,
                   tr.failure_points,
                   ts.scenario_name,
                   ts.scenario_description
              FROM test_runs   tr
              JOIN test_scenarios ts ON ts.id = tr.scenario_id
             WHERE tr.id NOT IN (
                       SELECT test_run_id FROM judge_calibration
                   )
             ORDER BY tr.created_at DESC
             LIMIT ?;
        """
    return conn.execute(query, (limit,)).fetchall()


def _insert_calibration(
    conn: sqlite3.Connection,
    test_run_id: int,
    human_score: float,
    human_failure_points: list[int],
    judge_score: float,
    notes: str | None,
) -> None:
    """Insert (or replace) a calibration entry for a given test run."""
    # Delete any existing entry so re-grading is idempotent.
    conn.execute(
        "DELETE FROM judge_calibration WHERE test_run_id = ?;",
        (test_run_id,),
    )
    conn.execute(
        """
        INSERT INTO judge_calibration
            (test_run_id, human_score, human_failure_points, judge_score, notes)
        VALUES (?, ?, ?, ?, ?);
        """,
        (
            test_run_id,
            human_score,
            json.dumps(human_failure_points),
            judge_score,
            notes,
        ),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

_SEPARATOR = "=" * 72
_THIN_SEP = "-" * 72


def _display_transcript(transcript_json: str) -> None:
    """Pretty-print a conversation transcript stored as JSON."""
    try:
        turns: list[dict[str, Any]] = json.loads(transcript_json)
    except (json.JSONDecodeError, TypeError):
        print("  [Unable to parse transcript]")
        return

    for turn in turns:
        turn_num = turn.get("turn", "?")
        role = turn.get("role", "UNKNOWN").upper()
        content = turn.get("content", "")
        print(f"  Turn {turn_num} [{role}]: {content}")


def _display_scores(overall: float, breakdown_json: str) -> None:
    """Print the judge's scores for reference."""
    print(f"\n  Judge Overall Score: {overall:.1f} / 100")
    try:
        breakdown: dict[str, Any] = json.loads(breakdown_json)
        print("  Per-dimension scores:")
        for dimension, score in breakdown.items():
            label = dimension.replace("_", " ").title()
            print(f"    • {label}: {score}")
    except (json.JSONDecodeError, TypeError):
        print("  [Unable to parse scores breakdown]")


def _display_failure_points(failure_json: str) -> None:
    """Print the judge-identified failure points."""
    try:
        failures: list[dict[str, Any]] = json.loads(failure_json)
        if not failures:
            print("  Judge Failure Points: None")
            return
        print("  Judge Failure Points:")
        for fp in failures:
            turn = fp.get("turn", "?")
            reason = fp.get("reason", "N/A")
            print(f"    • Turn {turn}: {reason}")
    except (json.JSONDecodeError, TypeError):
        print("  [Unable to parse failure points]")


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------


def _prompt_score() -> float:
    """Prompt the human grader for an overall score in [0, 100]."""
    while True:
        raw = input("\n  Enter your overall score (0-100): ").strip()
        try:
            score = float(raw)
            if 0 <= score <= 100:
                return score
            print("  ⚠  Score must be between 0 and 100.")
        except ValueError:
            print("  ⚠  Please enter a valid number.")


def _prompt_failure_turns(total_turns: int) -> list[int]:
    """Prompt for failure turn numbers (comma-separated or 'none')."""
    while True:
        raw = input(
            "  Enter failure turn numbers (comma-separated, or 'none'): "
        ).strip()
        if raw.lower() == "none" or raw == "":
            return []
        try:
            turns = [int(t.strip()) for t in raw.split(",") if t.strip()]
            if all(1 <= t <= total_turns for t in turns):
                return sorted(set(turns))
            print(
                f"  ⚠  Turn numbers must be between 1 and {total_turns}."
            )
        except ValueError:
            print("  ⚠  Please enter valid integers separated by commas.")


def _prompt_notes() -> str | None:
    """Optionally collect free-text notes from the grader."""
    raw = input("  Notes (press Enter to skip): ").strip()
    return raw if raw else None


# ---------------------------------------------------------------------------
# Main grading loop
# ---------------------------------------------------------------------------


def grade_runs(db_path: str, limit: int, include_all: bool) -> None:
    """Main loop: present test runs and collect human calibration data.

    Parameters
    ----------
    db_path:
        Path to the SQLite database.
    limit:
        Maximum number of runs to grade.
    include_all:
        If ``True``, include runs that already have calibration entries.
    """
    conn = _connect(db_path)
    runs = _fetch_pending_runs(conn, limit, include_all)

    if not runs:
        print("\nNo test runs available for grading.")
        conn.close()
        return

    print(f"\n{_SEPARATOR}")
    print(f"  VoiceIQ Calibration Harness — {len(runs)} run(s) to grade")
    print(_SEPARATOR)

    graded_count = 0
    for idx, run in enumerate(runs, start=1):
        run_id: int = run["run_id"]
        scenario_name: str = run["scenario_name"]
        scenario_desc: str = run["scenario_description"]
        transcript_json: str = run["conversation_transcript"]
        total_turns: int = run["total_turns"]
        overall_score: float = run["overall_score"]
        breakdown_json: str = run["scores_breakdown"]
        failure_json: str = run["failure_points"]

        print(f"\n{_THIN_SEP}")
        print(f"  Run {idx}/{len(runs)}  (ID: {run_id})")
        print(_THIN_SEP)

        # Scenario context
        print(f"\n  Scenario: {scenario_name}")
        print(f"  Description: {scenario_desc}")

        # Transcript
        print(f"\n  Transcript ({total_turns} turns):")
        print(_THIN_SEP)
        _display_transcript(transcript_json)
        print(_THIN_SEP)

        # Judge scores
        _display_scores(overall_score, breakdown_json)
        _display_failure_points(failure_json)

        # Human grading
        print()
        try:
            human_score = _prompt_score()
            failure_turns = _prompt_failure_turns(total_turns)
            notes = _prompt_notes()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Grading session interrupted. Progress saved.")
            break

        _insert_calibration(
            conn,
            test_run_id=run_id,
            human_score=human_score,
            human_failure_points=failure_turns,
            judge_score=overall_score,
            notes=notes,
        )
        graded_count += 1
        logger.info(
            "Saved calibration for run %d (human_score=%.1f)",
            run_id,
            human_score,
        )

    conn.close()
    print(f"\n{_SEPARATOR}")
    print(f"  Done — {graded_count} run(s) graded.")
    print(f"{_SEPARATOR}\n")


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VoiceIQ Calibration Harness — human-grade judge scores.",
    )
    parser.add_argument(
        "-n",
        type=int,
        default=5,
        metavar="N",
        help="Number of test runs to grade (default: 5).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="include_all",
        help="Include runs that already have calibration entries.",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to the SQLite database (overrides DATABASE_PATH env var).",
    )
    return parser


def main() -> None:
    """Parse CLI arguments and run the grading loop."""
    parser = _build_parser()
    args = parser.parse_args()

    db_path = args.db if args.db else DATABASE_PATH
    logger.info("Using database: %s", db_path)

    grade_runs(db_path=db_path, limit=args.n, include_all=args.include_all)


if __name__ == "__main__":
    main()
