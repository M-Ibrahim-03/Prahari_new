"""Unit tests for engine/confidence.py and engine/ensemble.py. Pure."""
import pytest

from engine.confidence import compute_cell_confidence, compute_field_confidence, confidence_label
from engine.ensemble import compute_nwp_agreement


def test_field_confidence_takes_minimum_of_cells():
    # Min invariant: 0.90 and 0.65 -> 0.65 (worst-case)
    assert compute_field_confidence([0.90, 0.65, 0.88]) == 0.65


def test_confidence_drops_with_incomplete_data():
    full_conf = compute_cell_confidence(node_variances=[0.1, 0.1], data_completeness=1.0)
    partial_conf = compute_cell_confidence(node_variances=[0.1, 0.1], data_completeness=0.5)
    assert partial_conf < full_conf


def test_ensemble_agreement_high_when_models_agree():
    ecmwf = [20.0, 21.0, 22.0, 23.0]
    gfs = [20.2, 21.1, 21.9, 23.1]
    agreement = compute_nwp_agreement([ecmwf, gfs])
    assert agreement > 0.90


def test_ensemble_agreement_drops_when_models_diverge():
    ecmwf = [20.0, 20.0, 20.0, 20.0]
    gfs = [30.0, 32.0, 31.0, 33.0]
    agreement = compute_nwp_agreement([ecmwf, gfs])
    assert agreement < 0.60


def test_confidence_label():
    assert confidence_label(0.92, "en") == "High"
    assert confidence_label(0.70, "en") == "Moderate"
    assert confidence_label(0.40, "en") == "Low"
    assert confidence_label(0.92, "hi") == "उच्च"
