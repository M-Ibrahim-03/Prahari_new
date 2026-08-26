"""FAO-56 single-coefficient soil-water balance — the irrigation index (PRD §PS302, deck p.2).

🔴 PURE. No network, no clock, no filesystem, no randomness. Enforced by tests/test_purity.py.

This is the second of the deck's four indices. It answers "does this field need water, and how
many days until it does" from the SAME hourly weather the disease engine already consumes:
`precipitation` and `et0_fao_evapotranspiration` are both already in the Open-Meteo hourly pull,
so this index costs zero extra API calls and cannot fail independently of the weather fetch.

Method: FAO Irrigation & Drainage Paper 56, Allen et al. (1998), Ch. 8 — the daily root-zone
depletion recursion

    Dr_i = Dr_(i-1) - (P_i - RO_i) - I_i + ETc_i

with ETc = Kc * ETo, irrigation advised once depletion reaches Readily Available Water.

🔴 What this deliberately does NOT do: it does not know the farmer's soil texture, their actual
sowing date, or whether the canal ran last night. It reports a MODELLED depletion under stated
assumptions, and `WaterBalance.assumptions` carries them so the UI can show them. A farmer who
can see the canal is a better sensor than this function, and the advisory text says so.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Literal, Sequence

WaterBand = Literal["wet", "adequate", "deficit", "critical"]

# ── Crop and soil parameters ────────────────────────────────────────────────────────────────────
# 🔴 Potato, mid-season. Sourced from FAO-56 Table 12 (Kc) and Table 22 (Zr, p) so every number
# here is citable — this project does not invent agronomic constants (governing law 3's spirit).
KC_POTATO_MID = 1.15          # FAO-56 Table 12, potato mid-season
ROOT_DEPTH_M = 0.5            # FAO-56 Table 22, potato Zr mid-range
DEPLETION_FRACTION_P = 0.35   # FAO-56 Table 22, potato p

# Indo-Gangetic plain loam. θFC - θWP ≈ 0.15 m³/m³ (FAO-56 Table 19, loam midpoint).
AVAILABLE_WATER_CAPACITY = 0.15


@dataclass(frozen=True)
class WaterBalance:
    """Root-zone water status for one cell on one day."""

    depletion_mm: float          # Dr — current root-zone depletion
    taw_mm: float                # Total Available Water
    raw_mm: float                # Readily Available Water (p * TAW); irrigate at or beyond this
    stress_coefficient: float    # Ks, 1.0 = unstressed, <1.0 = transpiration reduced
    band: WaterBand
    days_until_irrigation: int | None   # None when already at/over the threshold
    rain_7d_mm: float
    etc_7d_mm: float
    assumptions: tuple[str, ...] = dc_field(default_factory=tuple)


def total_available_water(root_depth_m: float = ROOT_DEPTH_M) -> float:
    """TAW = 1000 * (θFC - θWP) * Zr  →  mm. FAO-56 eq. 82."""
    return 1000.0 * AVAILABLE_WATER_CAPACITY * root_depth_m


def _stress_coefficient(depletion_mm: float, taw_mm: float, raw_mm: float) -> float:
    """Ks — FAO-56 eq. 84. Linear decline once depletion passes RAW."""
    if depletion_mm <= raw_mm:
        return 1.0
    denominator = taw_mm - raw_mm
    if denominator <= 0:
        return 0.0
    ks = (taw_mm - depletion_mm) / denominator
    return max(0.0, min(1.0, ks))


def _band(depletion_mm: float, taw_mm: float, raw_mm: float) -> WaterBand:
    """
    🔴 Four bands, not three, and deliberately NOT the same vocabulary as the disease bands.
    A farmer must never confuse "deficit water" with "act on disease" — the disease bands are
    safe/watch/act and drive spraying; these drive irrigation and share no colour or word.
    """
    if depletion_mm <= 0.25 * raw_mm:
        return "wet"
    if depletion_mm < raw_mm:
        return "adequate"
    if depletion_mm < taw_mm:
        return "deficit"
    return "critical"


def compute_water_balance(
    precipitation_mm: Sequence[float],
    et0_mm: Sequence[float],
    *,
    kc: float = KC_POTATO_MID,
    root_depth_m: float = ROOT_DEPTH_M,
    depletion_fraction: float = DEPLETION_FRACTION_P,
    initial_depletion_mm: float | None = None,
) -> WaterBalance:
    """
    Run the FAO-56 depletion recursion over an hourly series and report the end state.

    `precipitation_mm` and `et0_mm` are HOURLY and must be the same length — they come from the
    same Open-Meteo response, so a length mismatch means the caller mixed two fetches and is a
    programming error, not a data condition.

    🔴 Starts the recursion at field capacity (Dr = 0) unless told otherwise. That is optimistic,
    and it is the honest choice: we have no soil-moisture observation for this field, so beginning
    "full" means the model can only ever UNDER-state depletion and thus under-advise irrigation.
    Advising too little water wastes nothing; advising too much wastes a farmer's diesel.
    """
    if len(precipitation_mm) != len(et0_mm):
        raise ValueError(
            f"hourly series length mismatch: precipitation={len(precipitation_mm)} et0={len(et0_mm)}"
        )
    if not precipitation_mm:
        raise ValueError("empty hourly series")

    taw = total_available_water(root_depth_m)
    raw = depletion_fraction * taw

    depletion = 0.0 if initial_depletion_mm is None else max(0.0, min(taw, initial_depletion_mm))

    rain_total = 0.0
    etc_total = 0.0
    for rain_h, et0_h in zip(precipitation_mm, et0_mm):
        rain = max(0.0, float(rain_h or 0.0))
        etc = max(0.0, float(et0_h or 0.0)) * kc
        rain_total += rain
        etc_total += etc
        # Depletion cannot go below field capacity (surplus is runoff/deep percolation, which this
        # single-layer model discards) nor above TAW (the root zone cannot lose water it lacks).
        depletion = max(0.0, min(taw, depletion - rain + etc))

    # Mean recent demand, used only to project forward. Guarded so a fully-wet window cannot
    # divide by zero.
    hours = len(et0_mm)
    mean_daily_etc = (etc_total / hours) * 24.0 if hours else 0.0

    days_until: int | None = None
    if depletion < raw and mean_daily_etc > 0.01:
        days_until = max(0, int((raw - depletion) / mean_daily_etc))

    return WaterBalance(
        depletion_mm=round(depletion, 1),
        taw_mm=round(taw, 1),
        raw_mm=round(raw, 1),
        stress_coefficient=round(_stress_coefficient(depletion, taw, raw), 2),
        band=_band(depletion, taw, raw),
        days_until_irrigation=days_until,
        rain_7d_mm=round(rain_total, 1),
        etc_7d_mm=round(etc_total, 1),
        assumptions=(
            f"kc={kc} (FAO-56 T12 potato mid-season)",
            f"root_depth_m={root_depth_m} (FAO-56 T22)",
            f"p={depletion_fraction} (FAO-56 T22)",
            f"awc={AVAILABLE_WATER_CAPACITY} m3/m3 (FAO-56 T19 loam)",
            "started at field capacity; no soil-moisture observation for this field",
        ),
    )
