"""Model-agnostic Disease Severity Value (DSV) table lookup. Pure.

Generalizes DSV calculation for any pathogen model specified in YAML
(e.g., Wallin 1962 for Late Blight, TOMCAST Pitblado 1992 for Early Blight).
"""
from __future__ import annotations

from typing import Sequence

# Default table fallback (Wallin 1962 late blight) for pure offline tests
DEFAULT_WALLIN_TABLE: tuple[dict, ...] = (
    {"t_min": 7.2,  "t_max": 11.6, "breaks": ((15, 0), (18, 1), (21, 2), (24, 3))},
    {"t_min": 11.7, "t_max": 15.0, "breaks": ((12, 0), (15, 1), (18, 2), (21, 3), (24, 4))},
    {"t_min": 15.1, "t_max": 26.6, "breaks": ((9, 0), (12, 1), (15, 2), (18, 3), (24, 4))},
)

# Standard TOMCAST table (Pitblado 1992 / Madden et al. 1978 for early blight)
DEFAULT_TOMCAST_TABLE: tuple[dict, ...] = (
    {"t_min": 13.0, "t_max": 17.0, "breaks": ((7, 0), (13, 1), (18, 2), (21, 3), (24, 4))},
    {"t_min": 17.1, "t_max": 20.0, "breaks": ((4, 0), (9, 1), (14, 2), (18, 3), (24, 4))},
    {"t_min": 20.1, "t_max": 25.5, "breaks": ((3, 0), (6, 1), (9, 2), (13, 3), (16, 4))},
    {"t_min": 25.6, "t_max": 29.0, "breaks": ((4, 0), (9, 1), (14, 2), (18, 3), (24, 4))},
)


def compute_dsv(
    mean_wet_temp: float,
    wet_hours: float,
    dsv_table: Sequence[dict] = DEFAULT_WALLIN_TABLE,
) -> int:
    """Calculate daily DSV (0-4) from wet-spell temperature and duration.

    Bands are sorted by t_min. If mean_wet_temp is below the lowest t_min or
    above the highest t_max, returns 0.
    Within the valid range, temperature falls into the matching band and returns
    the highest breakpoint reached by wet_hours.
    """
    bands = sorted(dsv_table, key=lambda b: b["t_min"])
    if not bands:
        return 0
    if mean_wet_temp < bands[0]["t_min"] or mean_wet_temp > bands[-1]["t_max"]:
        return 0

    band = next((b for b in bands if mean_wet_temp <= b["t_max"]), bands[-1])
    dsv = 0
    for hours, value in band["breaks"]:
        if wet_hours >= hours:
            dsv = value
        else:
            break
    return dsv
