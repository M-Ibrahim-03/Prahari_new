"""Unit tests for hindcast validation and contingency table calculations (Phase H)."""
import pytest

from adapters.hindcast import compute_contingency_metrics


def test_contingency_metrics_perfect_scores():
    preds = [True, True, False, False]
    obs = [True, True, False, False]
    metrics = compute_contingency_metrics(preds, obs)
    assert metrics["tp"] == 2
    assert metrics["tn"] == 2
    assert metrics["fp"] == 0
    assert metrics["fn"] == 0
    assert metrics["sensitivity"] == 1.0
    assert metrics["false_alarm_ratio"] == 0.0
    assert metrics["critical_success_index"] == 1.0


def test_contingency_metrics_high_sensitivity_operating_point():
    # Operating point with high sensitivity (0 misses) and some false alarms (FAR ~ 0.2)
    preds = [True, True, True, True, False]
    obs = [True, True, True, False, False] # 1 false alarm, 0 missed
    metrics = compute_contingency_metrics(preds, obs)
    assert metrics["sensitivity"] == 1.0
    assert metrics["fn"] == 0
    assert metrics["fp"] == 1
    assert metrics["false_alarm_ratio"] == 0.25
