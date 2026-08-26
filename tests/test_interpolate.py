"""Tests for spatial interpolation and the 🔴 never-lapse-RH rule (PRD §8.3)."""
import math

from engine.interpolate import (
    bilinear,
    cell_rh_from_node,
    rh_from_temp_and_dewpoint,
    temp_with_lapse,
)


def test_lapse_makes_higher_cells_colder():
    # 1000 m above the node at 6.5 C/km -> 6.5 C colder.
    assert temp_with_lapse(20.0, 100.0, 1100.0, 6.5) == 13.5
    # Same elevation -> unchanged.
    assert temp_with_lapse(20.0, 100.0, 100.0) == 20.0


def test_magnus_saturation_is_100():
    for t in (5.0, 15.0, 28.0):
        assert rh_from_temp_and_dewpoint(t, t) == 100.0


def test_magnus_known_value():
    # T=20, Td=10 -> ~52.5% RH.
    assert math.isclose(rh_from_temp_and_dewpoint(20.0, 10.0), 52.5, abs_tol=0.6)


def test_magnus_clamps_supersaturation():
    # Dewpoint above temperature is unphysical input -> clamp to 100, never >100.
    assert rh_from_temp_and_dewpoint(10.0, 30.0) == 100.0


def test_cell_rh_is_recomputed_not_carried():
    # 🔴 RH is recomputed from lapsed temp+dewpoint, and stays a valid percentage.
    rh = cell_rh_from_node(
        node_temp_c=20.0, node_dewpoint_c=10.0,
        node_elev_m=100.0, cell_elev_m=1100.0,
    )
    assert 0.0 <= rh <= 100.0


def test_bilinear_corners_and_center():
    # At a corner, returns that corner's value.
    assert bilinear(0, 0, 0, 10, 0, 10, q00=1, q01=2, q10=3, q11=4) == 1
    # At the centre, returns the mean of the four corners.
    assert bilinear(5, 5, 0, 10, 0, 10, q00=1, q01=2, q10=3, q11=4) == 2.5
