"""Wallin (1962) Disease Severity Value (DSV) table lookup. Pure.

🔴 [VERIFY] item 1 — the highest-priority verification item in the project. The band
boundaries and hour breakpoints below mirror pipeline/config/models.yaml and MUST be
confirmed against Wallin (1962) (or an authoritative extension publication) before the
DSV output is presented as fact (PRD §8.4.3, §43, risk register #2).
"""
from __future__ import annotations

from typing import Sequence

# Mirror of models.yaml -> potato_late_blight_hutton.severity.dsv_table.
# The pipeline passes the yaml-loaded table in explicitly; this default exists so the
# pure unit tests and quick calls work without any file I/O (which the engine forbids).
DEFAULT_DSV_TABLE: tuple[dict, ...] = (
    {"t_min": 7.2,  "t_max": 11.6, "breaks": ((15, 0), (18, 1), (21, 2), (24, 3))},
    {"t_min": 11.7, "t_max": 15.0, "breaks": ((12, 0), (15, 1), (18, 2), (21, 3), (24, 4))},
    {"t_min": 15.1, "t_max": 26.6, "breaks": ((9, 0), (12, 1), (15, 2), (18, 3), (24, 4))},
)


def wallin_dsv(
    mean_wet_temp: float,
    wet_hours: float,
    dsv_table: Sequence[dict] = DEFAULT_DSV_TABLE,
) -> int:
    """Daily Disease Severity Value (0-4) from wet-spell temperature and duration.

    🔴 ``mean_wet_temp`` is the mean temperature DURING THE WET SPELL, not the daily
    mean. Using the daily mean is silent bug 2 (PRD §8.6) — which is why the pipeline
    exposes ``mean_wet_temp_c`` in the artefact so a reviewer can catch it.

    Within a temperature band, DSV is the value of the highest hour-breakpoint that
    ``wet_hours`` reaches. Temperatures below the coldest band or above the warmest
    yield DSV 0 (no infection pressure).

    🔴 THE BANDS ARE TREATED AS CONTIGUOUS, and that is a deliberate correction rather
    than sloppiness. As published, the bands read 7.2-11.6, 11.7-15.0, 15.1-26.6 — the
    0.1 C steps between them are an artefact of a table printed to one decimal place, not
    a claim that 15.05 C is unfavourable to the pathogen. Matching each band as a closed
    interval left two dead zones (11.61-11.69 and 15.01-15.09) where NO band applied and
    the function fell through to 0. Interpolated cell temperatures are continuous, so real
    cells land there: this was found on a cell reporting a 24 h wet spell at 15.05 C as
    DSV 0 — the single most blight-favourable cell in the district, silently marked safe.
    A false negative in the middle of the pathogen's ideal range is the worst possible
    failure for this model, so a temperature between two bands falls into the warmer of
    them. Every temperature that is inside a published band keeps its published value.
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
