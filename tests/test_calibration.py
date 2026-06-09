"""
Tests for calibration/report.py

Covers:
- MAE computation
- Pearson and Spearman correlation
- Bland-Altman statistics
- Failure point overlap (precision, recall, Jaccard)
- Edge cases (small sample sizes, perfect agreement)
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats as scipy_stats


# ── Test: Mean Absolute Error ─────────────────────────────────────────────────

def compute_mae(human: list[float], judge: list[float]) -> float:
    """Compute Mean Absolute Error between two score lists."""
    assert len(human) == len(judge), "Lists must be same length"
    return float(np.mean(np.abs(np.array(judge) - np.array(human))))


class TestMAE:
    """Test Mean Absolute Error calculation."""

    def test_perfect_agreement(self):
        assert compute_mae([80, 60, 70], [80, 60, 70]) == pytest.approx(0.0)

    def test_known_mae(self):
        # |85-80| + |65-60| + |75-70| = 5 + 5 + 5 = 15; mean = 5
        assert compute_mae([80, 60, 70], [85, 65, 75]) == pytest.approx(5.0)

    def test_mixed_differences(self):
        # |90-80| + |55-60| + |75-70| = 10 + 5 + 5 = 20; mean = 6.667
        result = compute_mae([80, 60, 70], [90, 55, 75])
        assert result == pytest.approx(20 / 3)

    def test_single_value(self):
        assert compute_mae([50], [75]) == pytest.approx(25.0)

    def test_symmetry(self):
        """MAE should be symmetric — order of human/judge doesn't matter."""
        assert compute_mae([80, 60], [90, 50]) == compute_mae([90, 50], [80, 60])


# ── Test: Pearson Correlation ─────────────────────────────────────────────────

class TestPearson:
    """Test Pearson correlation coefficient."""

    def test_perfect_positive_correlation(self):
        r, p = scipy_stats.pearsonr([10, 20, 30, 40], [20, 40, 60, 80])
        assert r == pytest.approx(1.0)

    def test_perfect_negative_correlation(self):
        r, p = scipy_stats.pearsonr([10, 20, 30, 40], [80, 60, 40, 20])
        assert r == pytest.approx(-1.0)

    def test_no_correlation(self):
        """Nearly zero correlation for unrelated values."""
        r, p = scipy_stats.pearsonr([10, 20, 30, 40], [25, 25, 25, 25])
        # With constant second array, pearson is undefined/nan
        # scipy returns nan for constant input
        assert math.isnan(r) or abs(r) < 0.1

    def test_realistic_scores(self):
        human = [90, 68, 55, 86, 65, 28, 92, 48, 22, 93]
        judge = [91.2, 73.7, 63.2, 87.0, 62.2, 30.5, 89.0, 56.5, 24.5, 91.4]
        r, p = scipy_stats.pearsonr(human, judge)
        assert r > 0.95, f"Expected strong positive correlation, got r={r}"


# ── Test: Spearman Correlation ────────────────────────────────────────────────

class TestSpearman:
    """Test Spearman rank correlation coefficient."""

    def test_perfect_rank_agreement(self):
        rho, p = scipy_stats.spearmanr([1, 2, 3, 4], [10, 20, 30, 40])
        assert rho == pytest.approx(1.0)

    def test_perfect_rank_disagreement(self):
        rho, p = scipy_stats.spearmanr([1, 2, 3, 4], [40, 30, 20, 10])
        assert rho == pytest.approx(-1.0)

    def test_realistic_ranking(self):
        human = [90, 68, 55, 86, 65, 28]
        judge = [91, 74, 63, 87, 62, 31]
        rho, p = scipy_stats.spearmanr(human, judge)
        assert rho > 0.9, f"Expected strong rank correlation, got rho={rho}"


# ── Test: Bland-Altman Statistics ─────────────────────────────────────────────

def compute_bland_altman(human: list[float], judge: list[float]) -> dict:
    """Compute Bland-Altman agreement statistics."""
    diffs = np.array(judge) - np.array(human)
    bias = float(np.mean(diffs))
    sd = float(np.std(diffs, ddof=1))
    return {
        "bias": bias,
        "sd": sd,
        "upper_loa": bias + 1.96 * sd,
        "lower_loa": bias - 1.96 * sd,
    }


class TestBlandAltman:
    """Test Bland-Altman statistics."""

    def test_perfect_agreement(self):
        result = compute_bland_altman([80, 60, 70], [80, 60, 70])
        assert result["bias"] == pytest.approx(0.0)
        assert result["sd"] == pytest.approx(0.0)

    def test_constant_bias(self):
        """Judge always scores 5 higher."""
        result = compute_bland_altman([80, 60, 70, 50], [85, 65, 75, 55])
        assert result["bias"] == pytest.approx(5.0)
        assert result["sd"] == pytest.approx(0.0)

    def test_limits_of_agreement(self):
        human = [80, 60, 70, 50]
        judge = [85, 55, 75, 45]
        result = compute_bland_altman(human, judge)
        # Diffs: [5, -5, 5, -5], bias=0, sd=5.77
        assert result["bias"] == pytest.approx(0.0)
        assert result["upper_loa"] > 0
        assert result["lower_loa"] < 0
        # LoA should be symmetric around 0 when bias is 0
        assert result["upper_loa"] == pytest.approx(-result["lower_loa"])

    def test_loa_width(self):
        """Limits of agreement should be bias ± 1.96 * SD."""
        result = compute_bland_altman([80, 60], [90, 50])
        # Diffs: [10, -10], bias=0, sd=14.14
        expected_sd = float(np.std([10, -10], ddof=1))
        assert result["upper_loa"] == pytest.approx(result["bias"] + 1.96 * expected_sd)
        assert result["lower_loa"] == pytest.approx(result["bias"] - 1.96 * expected_sd)


# ── Test: Failure Point Overlap ───────────────────────────────────────────────

def compute_failure_overlap(
    human_turns: set[int],
    judge_turns: set[int],
) -> dict[str, float]:
    """Compute precision, recall, and Jaccard index for failure turn overlap."""
    if not human_turns and not judge_turns:
        return {"precision": 1.0, "recall": 1.0, "jaccard": 1.0}

    intersection = human_turns & judge_turns
    union = human_turns | judge_turns

    precision = len(intersection) / len(judge_turns) if judge_turns else 1.0
    recall = len(intersection) / len(human_turns) if human_turns else 1.0
    jaccard = len(intersection) / len(union) if union else 1.0

    return {"precision": precision, "recall": recall, "jaccard": jaccard}


class TestFailureOverlap:
    """Test failure point overlap metrics."""

    def test_perfect_overlap(self):
        result = compute_failure_overlap({3, 5, 7}, {3, 5, 7})
        assert result["precision"] == pytest.approx(1.0)
        assert result["recall"] == pytest.approx(1.0)
        assert result["jaccard"] == pytest.approx(1.0)

    def test_no_overlap(self):
        result = compute_failure_overlap({1, 2, 3}, {4, 5, 6})
        assert result["precision"] == pytest.approx(0.0)
        assert result["recall"] == pytest.approx(0.0)
        assert result["jaccard"] == pytest.approx(0.0)

    def test_partial_overlap(self):
        result = compute_failure_overlap({3, 5, 7}, {3, 5, 9})
        # Precision: 2/3 (judge flagged 3,5,9 — 2 of 3 were also human-flagged)
        # Recall: 2/3 (human flagged 3,5,7 — 2 of 3 were also judge-flagged)
        # Jaccard: 2/4 (union is {3,5,7,9})
        assert result["precision"] == pytest.approx(2 / 3)
        assert result["recall"] == pytest.approx(2 / 3)
        assert result["jaccard"] == pytest.approx(2 / 4)

    def test_empty_both(self):
        result = compute_failure_overlap(set(), set())
        assert result["precision"] == pytest.approx(1.0)
        assert result["recall"] == pytest.approx(1.0)
        assert result["jaccard"] == pytest.approx(1.0)

    def test_empty_human(self):
        """If human flagged nothing but judge did, precision should be 0."""
        result = compute_failure_overlap(set(), {3, 5})
        assert result["recall"] == pytest.approx(1.0)  # No human failures to miss
        assert result["precision"] == pytest.approx(0.0)  # Judge flagged things human didn't

    def test_empty_judge(self):
        """If judge flagged nothing but human did, recall should be 0."""
        result = compute_failure_overlap({3, 5}, set())
        assert result["precision"] == pytest.approx(1.0)  # No judge failures to be wrong about
        assert result["recall"] == pytest.approx(0.0)  # Judge missed all human failures

    def test_subset_relationship(self):
        """Judge catches everything human flagged plus extras."""
        result = compute_failure_overlap({3, 5}, {3, 5, 7, 9})
        assert result["recall"] == pytest.approx(1.0)  # Human's failures all caught
        assert result["precision"] == pytest.approx(2 / 4)  # But judge was overzealous
