"""Tests for grid geometry and bilinear application. Pure."""
from engine.grid import build_grid, interp_at_cell


def _grid():
    # 0.2 deg half-span, 0.1 deg nodes -> 3x3=9 nodes; 0.1 deg cells -> 3x3=9 cells.
    return build_grid("demo", center_lat=27.4, center_lon=79.6,
                      half_span_deg=0.1, node_step_deg=0.1, cell_step_deg=0.1,
                      id_prefix="DMO")


def test_node_and_cell_counts():
    g = _grid()
    assert len(g.node_lats) == 3 and len(g.node_lons) == 3
    assert len(g.nodes) == 9
    assert len(g.cells) == 9


def test_cell_ids_are_formatted():
    g = _grid()
    assert g.cells[0].cell_id == "DMO-R000-C000"


def test_weights_sum_to_one():
    g = _grid()
    for cell in g.cells:
        assert abs(sum(cell.weights) - 1.0) < 1e-9


def test_interp_at_node_aligned_cell_returns_node_value():
    g = _grid()
    # Distinct value per node; a cell sitting exactly on a node must return that node's value.
    node_values = [float(i) for i in range(len(g.nodes))]
    corner = g.cells[0]  # at (lat0, lon0) == node 0
    assert abs(interp_at_cell(node_values, corner) - node_values[corner.node_idx[0]]) < 1e-9
