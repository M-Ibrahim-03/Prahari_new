"""Node lattice + computational grid geometry, and bilinear application. Pure.

Downscaling lattice (PRD §8.1): a coarse regular lattice of weather nodes (~0.1 deg) is
interpolated to a fine cell grid (~1-2 km). Interpolation weights are precomputed here
once per district so the nightly job only does weighted sums.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Cell:
    cell_id: str
    row: int
    col: int
    lat: float
    lon: float
    node_idx: tuple[int, int, int, int]        # (n00, n10, n01, n11) into Grid.nodes
    weights: tuple[float, float, float, float]  # matching bilinear weights, sum ~= 1


@dataclass(frozen=True)
class Grid:
    district: str
    node_lats: tuple[float, ...]
    node_lons: tuple[float, ...]
    nodes: tuple[tuple[float, float], ...]      # (lat, lon), row-major: lat outer, lon inner
    cells: tuple[Cell, ...]


def _frange_inclusive(start: float, stop: float, step: float) -> list[float]:
    n = int(round((stop - start) / step))
    return [round(start + k * step, 6) for k in range(n + 1)]


def build_grid(
    district: str,
    center_lat: float,
    center_lon: float,
    half_span_deg: float,
    node_step_deg: float,
    cell_step_deg: float,
    id_prefix: str,
) -> Grid:
    """Build a regular node lattice and a finer cell grid, with bilinear weights per cell."""
    lat0, lat1 = center_lat - half_span_deg, center_lat + half_span_deg
    lon0, lon1 = center_lon - half_span_deg, center_lon + half_span_deg

    node_lats = _frange_inclusive(lat0, lat1, node_step_deg)
    node_lons = _frange_inclusive(lon0, lon1, node_step_deg)
    n_lon = len(node_lons)
    nodes = tuple((la, lo) for la in node_lats for lo in node_lons)  # lat outer, lon inner

    def node_index(i_lon: int, j_lat: int) -> int:
        return j_lat * n_lon + i_lon

    cells: list[Cell] = []
    for r, la in enumerate(_frange_inclusive(lat0, lat1, cell_step_deg)):
        j = min(max(int((la - lat0) // node_step_deg), 0), len(node_lats) - 2)
        dlat = node_lats[j + 1] - node_lats[j]
        ty = (la - node_lats[j]) / dlat if dlat else 0.0
        for c, lo in enumerate(_frange_inclusive(lon0, lon1, cell_step_deg)):
            i = min(max(int((lo - lon0) // node_step_deg), 0), len(node_lons) - 2)
            dlon = node_lons[i + 1] - node_lons[i]
            tx = (lo - node_lons[i]) / dlon if dlon else 0.0
            weights = ((1 - tx) * (1 - ty), tx * (1 - ty), (1 - tx) * ty, tx * ty)
            idx = (node_index(i, j), node_index(i + 1, j),
                   node_index(i, j + 1), node_index(i + 1, j + 1))
            cells.append(Cell(f"{id_prefix}-R{r:03d}-C{c:03d}", r, c, la, lo, idx, weights))

    return Grid(district, tuple(node_lats), tuple(node_lons), nodes, tuple(cells))


def interp_at_cell(node_values: Sequence[float], cell: Cell) -> float:
    """Bilinear-interpolate a per-node quantity to a cell using its precomputed weights."""
    (n00, n10, n01, n11) = cell.node_idx
    (w00, w10, w01, w11) = cell.weights
    return (node_values[n00] * w00 + node_values[n10] * w10
            + node_values[n01] * w01 + node_values[n11] * w11)
