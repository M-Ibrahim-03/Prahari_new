"""Tests for multi-model combination and worst-band-wins rule (Phase B). Pure."""
import pytest

from engine.aggregate import CellAssessment, combine_cell_assessments


def test_worst_band_wins_act_over_watch_and_safe():
    late_blight = CellAssessment(
        band="safe", risk=0.1, physics_risk=0.1, ml_delta=0.0,
        criterion_met=False, dsv_today=0, dsv_accum=2,
        wet_hours=3, min_temp_c=18.0, mean_wet_temp_c=22.0,
        firing_model="potato_late_blight_hutton", firing_pathogen="Phytophthora infestans",
    )
    early_blight = CellAssessment(
        band="act", risk=0.85, physics_risk=0.85, ml_delta=0.0,
        criterion_met=True, dsv_today=4, dsv_accum=22,
        wet_hours=8, min_temp_c=18.0, mean_wet_temp_c=22.0,
        firing_model="potato_early_blight_tomcast", firing_pathogen="Alternaria solani",
    )

    combined = combine_cell_assessments([late_blight, early_blight])
    assert combined.band == "act"
    assert combined.firing_model == "potato_early_blight_tomcast"
    assert combined.firing_pathogen == "Alternaria solani"
    assert combined.risk == 0.85


def test_worst_band_wins_watch_over_safe():
    late_blight = CellAssessment(
        band="safe", risk=0.0, physics_risk=0.0, ml_delta=0.0,
        criterion_met=False, dsv_today=0, dsv_accum=0,
        wet_hours=0, min_temp_c=20.0, mean_wet_temp_c=0.0,
        firing_model="potato_late_blight_hutton", firing_pathogen="Phytophthora infestans",
    )
    early_blight = CellAssessment(
        band="watch", risk=0.55, physics_risk=0.55, ml_delta=0.0,
        criterion_met=True, dsv_today=3, dsv_accum=16,
        wet_hours=6, min_temp_c=20.0, mean_wet_temp_c=21.0,
        firing_model="potato_early_blight_tomcast", firing_pathogen="Alternaria solani",
    )

    combined = combine_cell_assessments([late_blight, early_blight])
    assert combined.band == "watch"
    assert combined.firing_model == "potato_early_blight_tomcast"


def test_worst_band_wins_ties_break_by_highest_risk():
    model_a = CellAssessment(
        band="act", risk=0.80, physics_risk=0.80, ml_delta=0.0,
        criterion_met=True, dsv_today=3, dsv_accum=20,
        wet_hours=6, min_temp_c=15.0, mean_wet_temp_c=16.0,
        firing_model="model_a", firing_pathogen="pathogen_a",
    )
    model_b = CellAssessment(
        band="act", risk=0.95, physics_risk=0.95, ml_delta=0.0,
        criterion_met=True, dsv_today=4, dsv_accum=24,
        wet_hours=8, min_temp_c=15.0, mean_wet_temp_c=16.0,
        firing_model="model_b", firing_pathogen="pathogen_b",
    )

    combined = combine_cell_assessments([model_a, model_b])
    assert combined.band == "act"
    assert combined.firing_model == "model_b"
    assert combined.risk == 0.95
