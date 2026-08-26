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
from engine.dsv import DEFAULT_WALLIN_TABLE as DEFAULT_DSV_TABLE, compute_dsv


def wallin_dsv(
    mean_wet_temp: float,
    wet_hours: float,
    dsv_table: Sequence[dict] = DEFAULT_DSV_TABLE,
) -> int:
    """Daily Disease Severity Value (0-4) from wet-spell temperature and duration."""
    return compute_dsv(mean_wet_temp, wet_hours, dsv_table)

