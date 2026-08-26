"""Tests for TOMCAST DSV table lookup and Early Blight model (Phase B). Pure."""
import pytest

from engine.dsv import DEFAULT_TOMCAST_TABLE, compute_dsv


def test_tomcast_cold_temp_below_13c_yields_zero():
    # TOMCAST temperature ceiling/floor: < 13 °C is 0 DSV
    assert compute_dsv(12.5, 20, DEFAULT_TOMCAST_TABLE) == 0


def test_tomcast_warm_temp_above_29c_yields_zero():
    # > 29 °C is 0 DSV
    assert compute_dsv(30.0, 15, DEFAULT_TOMCAST_TABLE) == 0


def test_tomcast_optimal_temp_breakpoints():
    # 20.1 - 25.5 °C band
    # breaks: [[3, 0], [6, 1], [9, 2], [13, 3], [16, 4]]
    assert compute_dsv(22.0, 2, DEFAULT_TOMCAST_TABLE) == 0
    assert compute_dsv(22.0, 5, DEFAULT_TOMCAST_TABLE) == 0
    assert compute_dsv(22.0, 6, DEFAULT_TOMCAST_TABLE) == 1
    assert compute_dsv(22.0, 10, DEFAULT_TOMCAST_TABLE) == 2
    assert compute_dsv(22.0, 14, DEFAULT_TOMCAST_TABLE) == 3
    assert compute_dsv(22.0, 18, DEFAULT_TOMCAST_TABLE) == 4


def test_tomcast_moderate_temp_breakpoints():
    # 13.0 - 17.0 °C band
    # breaks: [[7, 0], [13, 1], [18, 2], [21, 3], [24, 4]]
    assert compute_dsv(15.0, 12, DEFAULT_TOMCAST_TABLE) == 0
    assert compute_dsv(15.0, 15, DEFAULT_TOMCAST_TABLE) == 1
    assert compute_dsv(15.0, 20, DEFAULT_TOMCAST_TABLE) == 2
    assert compute_dsv(15.0, 22, DEFAULT_TOMCAST_TABLE) == 3
    assert compute_dsv(15.0, 24, DEFAULT_TOMCAST_TABLE) == 4
