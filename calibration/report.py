"""
VoiceIQ Calibration Report — agreement metrics between human and judge scores.

Computes MAE, Pearson *r*, Spearman *ρ*, Bland-Altman statistics, and
failure-point overlap (precision / recall / Jaccard) from the
``judge_calibration`` table.

Usage::

    python -m calibration.report          # print formatted report
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
import warnings
from typing import Any

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from scipy import stats

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

# Minimum data points required for meaningful correlation metrics.
_MIN_POINTS_FOR_CORRELATION: int = 3

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def _connect(db_path: str) -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    if not os.path.exists(db_path):
        logger.error("Database file not found: %s", db_path)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _resolve_db_path(db_path: str | None) -> str:
    """Return the effective database path."""
    return db_path if db_path else DATABASE_PATH


# ---------------------------------------------------------------------------
# Public data-access functions
# ---------------------------------------------------------------------------


def get_calibration_data(db_path: str | None = None) -> pd.DataFrame:
    """Return raw calibration data as a :class:`~pandas.DataFrame`.

    Joins ``judge_calibration`` with ``test_runs`` so that the judge's
    ``failure_points`` are available alongside the human annotations.

    Parameters
    ----------
    db_path:
        Path to the SQLite database.  Falls back to ``DATABASE_PATH``.

    Returns
    -------
    pd.DataFrame
        Columns: ``calibration_id``, ``test_run_id``, ``human_score``,
        ``judge_score``, ``human_failure_points``, ``judge_failure_points``,
        ``notes``, ``created_at``.
    """
    path = _resolve_db_path(db_path)
    conn = _connect(path)

    query = """
        SELECT jc.id              AS calibration_id,
               jc.test_run_id,
               jc.human_score,
               jc.judge_score,
               jc.human_failure_points,
               tr.failure_points  AS judge_failure_points,
               jc.notes,
               jc.created_at
          FROM judge_calibration jc
          JOIN test_runs tr ON tr.id = jc.test_run_id
         WHERE jc.human_score IS NOT NULL
         ORDER BY jc.created_at;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    logger.info("Loaded %d calibration entries from %s", len(df), path)
    return df


def get_bland_altman_data(db_path: str | None = None) -> pd.DataFrame:
    """Return a DataFrame suitable for Bland-Altman plotting.

    Parameters
    ----------
    db_path:
        Path to the SQLite database.

    Returns
    -------
    pd.DataFrame
        Columns: ``mean`` (average of human and judge scores),
        ``diff`` (judge − human).
    """
    df = get_calibration_data(db_path)
    if df.empty:
        return pd.DataFrame(columns=["mean", "diff"])

    ba = pd.DataFrame(
        {
            "mean": (df["human_score"] + df["judge_score"]) / 2.0,
            "diff": df["judge_score"] - df["human_score"],
        }
    )
    return ba


# ---------------------------------------------------------------------------
# Failure-point helpers
# ---------------------------------------------------------------------------


def _parse_failure_turns(raw: Any) -> set[int] | None:
    """Parse a JSON failure-points blob into a set of turn numbers.

    ``judge_calibration.human_failure_points`` is stored as a JSON list of
    ints, while ``test_runs.failure_points`` is a JSON list of dicts with a
    ``"turn"`` key.  This helper handles both shapes.

    Returns ``None`` when the input is null / unparseable / empty.
    """
    if raw is None:
        return None
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, list) or len(data) == 0:
        return None

    turns: set[int] = set()
    for item in data:
        if isinstance(item, int):
            turns.add(item)
        elif isinstance(item, dict) and "turn" in item:
            turns.add(int(item["turn"]))
    return turns if turns else None


def _compute_failure_overlap(
    df: pd.DataFrame,
) -> dict[str, float | None]:
    """Compute precision, recall, and Jaccard index for failure-point overlap.

    Only rows where **both** human and judge failure-point sets are non-null
    and non-empty are considered.

    Returns
    -------
    dict
        Keys: ``precision``, ``recall``, ``jaccard``, ``n_overlap_pairs``.
        Values are ``None`` when no eligible pairs exist.
    """
    precisions: list[float] = []
    recalls: list[float] = []
    jaccards: list[float] = []

    for _, row in df.iterrows():
        human_set = _parse_failure_turns(row["human_failure_points"])
        judge_set = _parse_failure_turns(row["judge_failure_points"])

        if human_set is None or judge_set is None:
            continue

        intersection = human_set & judge_set
        union = human_set | judge_set

        # Precision: fraction of judge-flagged turns also flagged by human
        if len(judge_set) > 0:
            precisions.append(len(intersection) / len(judge_set))

        # Recall: fraction of human-flagged turns also flagged by judge
        if len(human_set) > 0:
            recalls.append(len(intersection) / len(human_set))

        # Jaccard
        if len(union) > 0:
            jaccards.append(len(intersection) / len(union))

    n = len(jaccards)
    if n == 0:
        return {
            "precision": None,
            "recall": None,
            "jaccard": None,
            "n_overlap_pairs": 0,
        }

    return {
        "precision": float(np.mean(precisions)) if precisions else None,
        "recall": float(np.mean(recalls)) if recalls else None,
        "jaccard": float(np.mean(jaccards)) if jaccards else None,
        "n_overlap_pairs": n,
    }


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------


def compute_calibration_metrics(db_path: str | None = None) -> dict[str, Any]:
    """Compute all calibration agreement metrics.

    Parameters
    ----------
    db_path:
        Path to the SQLite database.

    Returns
    -------
    dict
        Top-level keys:

        * ``n`` — number of calibration data points
        * ``mae`` — mean absolute error
        * ``pearson_r``, ``pearson_p`` — Pearson correlation & *p*-value
        * ``spearman_rho``, ``spearman_p`` — Spearman correlation & *p*-value
        * ``bland_altman`` — dict with ``bias``, ``sd``, ``upper_loa``,
          ``lower_loa``
        * ``failure_overlap`` — dict with ``precision``, ``recall``,
          ``jaccard``, ``n_overlap_pairs``
    """
    df = get_calibration_data(db_path)
    n = len(df)

    if n == 0:
        logger.warning("No calibration data found.")
        return {"n": 0}

    human = df["human_score"].to_numpy(dtype=float)
    judge = df["judge_score"].to_numpy(dtype=float)
    diff = judge - human

    # MAE
    mae: float = float(np.mean(np.abs(diff)))

    # Correlations (need >= 3 points for meaningful results)
    pearson_r: float | None = None
    pearson_p: float | None = None
    spearman_rho: float | None = None
    spearman_p: float | None = None

    if n >= _MIN_POINTS_FOR_CORRELATION:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pr, pp = stats.pearsonr(human, judge)
            sr, sp = stats.spearmanr(human, judge)
        pearson_r = float(pr)
        pearson_p = float(pp)
        spearman_rho = float(sr)
        spearman_p = float(sp)
    else:
        logger.warning(
            "Only %d data point(s); correlation metrics require >= %d. "
            "Returning None for correlations.",
            n,
            _MIN_POINTS_FOR_CORRELATION,
        )

    # Bland-Altman
    bias: float = float(np.mean(diff))
    sd: float = float(np.std(diff, ddof=1)) if n > 1 else 0.0
    upper_loa: float = bias + 1.96 * sd
    lower_loa: float = bias - 1.96 * sd

    # Failure-point overlap
    failure_overlap = _compute_failure_overlap(df)

    return {
        "n": n,
        "mae": mae,
        "pearson_r": pearson_r,
        "pearson_p": pearson_p,
        "spearman_rho": spearman_rho,
        "spearman_p": spearman_p,
        "bland_altman": {
            "bias": bias,
            "sd": sd,
            "upper_loa": upper_loa,
            "lower_loa": lower_loa,
        },
        "failure_overlap": failure_overlap,
    }


# ---------------------------------------------------------------------------
# Pretty-printed report
# ---------------------------------------------------------------------------

_SEP = "=" * 60
_THIN = "-" * 60


def print_report(db_path: str | None = None) -> None:
    """Print a formatted calibration-agreement report to stdout.

    Parameters
    ----------
    db_path:
        Path to the SQLite database.
    """
    metrics = compute_calibration_metrics(db_path)
    n = metrics.get("n", 0)

    print(f"\n{_SEP}")
    print("  VoiceIQ — Judge / Human Calibration Report")
    print(_SEP)

    if n == 0:
        print("\n  No calibration data available.\n")
        return

    print(f"\n  Data points: {n}")

    # -- Score agreement ------------------------------------------------
    print(f"\n{_THIN}")
    print("  Score Agreement")
    print(_THIN)
    print(f"  Mean Absolute Error (MAE):      {metrics['mae']:.2f}")

    if metrics["pearson_r"] is not None:
        print(
            f"  Pearson r:                      {metrics['pearson_r']:.4f}  "
            f"(p = {metrics['pearson_p']:.4e})"
        )
        print(
            f"  Spearman ρ:                     {metrics['spearman_rho']:.4f}  "
            f"(p = {metrics['spearman_p']:.4e})"
        )
    else:
        print("  Pearson r:                      N/A  (< 3 data points)")
        print("  Spearman ρ:                     N/A  (< 3 data points)")

    # -- Bland-Altman ---------------------------------------------------
    ba = metrics["bland_altman"]
    print(f"\n{_THIN}")
    print("  Bland-Altman Analysis  (judge − human)")
    print(_THIN)
    print(f"  Bias (mean diff):               {ba['bias']:+.2f}")
    print(f"  SD of diff:                     {ba['sd']:.2f}")
    print(f"  Upper Limit of Agreement:       {ba['upper_loa']:+.2f}")
    print(f"  Lower Limit of Agreement:       {ba['lower_loa']:+.2f}")

    # -- Failure-point overlap ------------------------------------------
    fo = metrics["failure_overlap"]
    print(f"\n{_THIN}")
    print("  Failure-Point Overlap")
    print(_THIN)
    if fo["n_overlap_pairs"] == 0:
        print("  No entries with both human and judge failure points.\n")
    else:
        print(f"  Eligible pairs:                 {fo['n_overlap_pairs']}")
        _fmt = lambda v: f"{v:.4f}" if v is not None else "N/A"
        print(f"  Precision:                      {_fmt(fo['precision'])}")
        print(f"  Recall:                         {_fmt(fo['recall'])}")
        print(f"  Jaccard Index:                  {_fmt(fo['jaccard'])}")

    print(f"\n{_SEP}\n")


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------


def main() -> None:
    """Print the calibration report (CLI entry-point)."""
    import argparse

    parser = argparse.ArgumentParser(
        description="VoiceIQ — print judge/human calibration agreement report.",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to the SQLite database (overrides DATABASE_PATH env var).",
    )
    args = parser.parse_args()

    db_path = args.db if args.db else DATABASE_PATH
    print_report(db_path)


if __name__ == "__main__":
    main()
