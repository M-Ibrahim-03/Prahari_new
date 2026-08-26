"""Unit tests for bounded ML residual correction (Phase I)."""
import pytest

from adapters.ml_delta import apply_residual_correction, clamp_delta


def test_delta_is_strictly_clamped_to_25_percent():
    assert clamp_delta(0.50) == 0.25
    assert clamp_delta(-0.80) == -0.25
    assert clamp_delta(0.12) == 0.12


def test_safe_band_cannot_be_flipped_to_act_by_ml_alone():
    # Physics is safe (risk 0.60), raw delta 0.25 would make it 0.85 (act).
    # Invariant: Must cap below 0.80 (cannot flip safe -> act).
    res = apply_residual_correction(physics_risk=0.60, raw_delta=0.25, physics_band="safe")
    assert res.corrected_risk < 0.80


def test_normal_bounded_correction():
    res = apply_residual_correction(physics_risk=0.40, raw_delta=0.10, physics_band="watch")
    assert res.delta == 0.10
    assert res.corrected_risk == 0.50
    assert not res.is_clamped
