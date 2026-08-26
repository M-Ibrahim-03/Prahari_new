"""Field -> cell resolution. Pure.

A farmer never sees a cell (PRD §21.2: no grid, no cell boundaries, ever). Their field is a
named place; the cell is an implementation detail of the physics. This module is the only
bridge between the two: given a field's location, find the cell whose assessment applies.
"""
from __future__ import annotations

from typing import Optional, Sequence

from engine.grid import Cell, Grid


def resolve_cell_index(grid: Grid, lat: float, lon: float, cell_step_deg: float) -> Optional[int]:
    """Index of the cell whose centre is nearest (lat, lon), or None if outside the grid.

    The grid is regular, so "nearest centre" is exact containment. A field further than one
    cell-step from every centre is outside the district — return None rather than silently
    snapping it to an edge cell and reporting a risk for the wrong place.
    """
    if not grid.cells:
        return None
    best_i, best_d2 = 0, float("inf")
    for i, cell in enumerate(grid.cells):
        d2 = (cell.lat - lat) ** 2 + (cell.lon - lon) ** 2
        if d2 < best_d2:
            best_i, best_d2 = i, d2
    nearest = grid.cells[best_i]
    if abs(nearest.lat - lat) > cell_step_deg or abs(nearest.lon - lon) > cell_step_deg:
        return None
    return best_i


def resolve_cell(grid: Grid, lat: float, lon: float, cell_step_deg: float) -> Optional[Cell]:
    idx = resolve_cell_index(grid, lat, lon, cell_step_deg)
    return grid.cells[idx] if idx is not None else None


def sort_worst_first(items: Sequence[dict]) -> list[dict]:
    """Sort field advisories worst-band-first (PRD §21.1: Sunita sees the problem first).

    Ties broken by risk descending, then by accumulated severity, so ordering is stable and
    never depends on dict insertion order.
    """
    rank = {"act": 0, "watch": 1, "safe": 2}
    return sorted(
        items,
        key=lambda it: (rank.get(it["band"], 3), -it.get("risk", 0.0), -it.get("dsv_accum_7d", 0)),
    )
