"""Spatial interpolation and elevation correction. Pure.

Downscales the coarse weather-node lattice to the 1 km computational grid:
bilinear interpolation between nodes, then an elevation (lapse) correction per cell.

🔴 The load-bearing rule (PRD §8.3): NEVER lapse-correct relative humidity directly.
Lapse temperature and dewpoint to the cell's elevation, then RECOMPUTE RH from them via
the Magnus formula. RH is a ratio; moving it with a temperature lapse rate is wrong.
"""
from __future__ import annotations

import math

# Magnus coefficients (over water).
_MAGNUS_A = 17.625
_MAGNUS_B = 243.04

# Environmental (temperature) lapse rate. The same rate is applied to dewpoint here for
# simplicity; a distinct dewpoint lapse (~2 C/km) is a physically better refinement and
# is noted as a future improvement — it does not change the "recompute RH" rule.
DEFAULT_LAPSE_C_PER_KM = 6.5


def temp_with_lapse(
    node_temp_c: float,
    node_elev_m: float,
    cell_elev_m: float,
    lapse_c_per_km: float = DEFAULT_LAPSE_C_PER_KM,
) -> float:
    """Temperature at the cell's elevation. Higher cell than node -> colder."""
    return node_temp_c - lapse_c_per_km * (cell_elev_m - node_elev_m) / 1000.0


def rh_from_temp_and_dewpoint(temp_c: float, dewpoint_c: float) -> float:
    """Relative humidity (%) from temperature and dewpoint via the Magnus formula.

    Clamped to [0, 100]. When dewpoint == temp, RH is 100 (saturation).
    """
    num = math.exp(_MAGNUS_A * dewpoint_c / (_MAGNUS_B + dewpoint_c))
    den = math.exp(_MAGNUS_A * temp_c / (_MAGNUS_B + temp_c))
    return max(0.0, min(100.0, 100.0 * num / den))


def cell_rh_from_node(
    node_temp_c: float,
    node_dewpoint_c: float,
    node_elev_m: float,
    cell_elev_m: float,
    lapse_c_per_km: float = DEFAULT_LAPSE_C_PER_KM,
) -> float:
    """Cell RH done correctly: lapse temp AND dewpoint, then recompute RH via Magnus.

    🔴 Never carry or lapse the node's RH directly (PRD §8.3).
    """
    t = temp_with_lapse(node_temp_c, node_elev_m, cell_elev_m, lapse_c_per_km)
    td = temp_with_lapse(node_dewpoint_c, node_elev_m, cell_elev_m, lapse_c_per_km)
    return rh_from_temp_and_dewpoint(t, td)


def bilinear(
    x: float, y: float,
    x0: float, x1: float, y0: float, y1: float,
    q00: float, q01: float, q10: float, q11: float,
) -> float:
    """Bilinear interpolation of a value known at four lattice corners.

    ``qij`` is the value at ``(x_i, y_j)``. Degenerate axes (x0==x1 or y0==y1) fall back
    to averaging along the collapsed dimension, so a point on a node line is still valid.
    """
    tx = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
    ty = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
    return (
        q00 * (1 - tx) * (1 - ty)
        + q10 * tx * (1 - ty)
        + q01 * (1 - tx) * ty
        + q11 * tx * ty
    )
