"""Tests for field -> cell resolution and worst-first ordering. Pure."""
from engine.fields import resolve_cell, resolve_cell_index, sort_worst_first
from engine.grid import build_grid

STEP = 0.02


def _grid():
    return build_grid("farrukhabad", center_lat=27.40, center_lon=79.60,
                      half_span_deg=0.20, node_step_deg=0.10, cell_step_deg=STEP,
                      id_prefix="FRK")


def test_field_inside_grid_resolves_to_nearest_cell():
    g = _grid()
    cell = resolve_cell(g, 27.34, 79.52, STEP)
    assert cell is not None
    # The nearest centre must be within half a cell step of the field.
    assert abs(cell.lat - 27.34) <= STEP / 2 + 1e-9
    assert abs(cell.lon - 79.52) <= STEP / 2 + 1e-9


def test_field_at_exact_centre_resolves_to_that_cell():
    g = _grid()
    target = g.cells[137]
    cell = resolve_cell(g, target.lat, target.lon, STEP)
    assert cell is not None and cell.cell_id == target.cell_id


def test_field_outside_district_returns_none():
    # 🔴 Must NOT silently snap to an edge cell and report risk for the wrong place.
    g = _grid()
    assert resolve_cell(g, 30.0, 79.6, STEP) is None      # far north
    assert resolve_cell(g, 27.4, 90.0, STEP) is None      # far east
    assert resolve_cell_index(g, 0.0, 0.0, STEP) is None  # nowhere near


def test_sort_worst_first():
    items = [
        {"band": "safe",  "risk": 0.0},
        {"band": "act",   "risk": 0.9},
        {"band": "watch", "risk": 0.5},
        {"band": "act",   "risk": 0.95},
    ]
    out = sort_worst_first(items)
    assert [i["band"] for i in out] == ["act", "act", "watch", "safe"]
    assert out[0]["risk"] == 0.95   # worst act first
