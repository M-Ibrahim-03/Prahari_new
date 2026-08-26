"""Per-cell disease assessment: hourly weather -> daily stats -> risk band. Pure.

Ties the rules together (PRD §8.2 Step 3-4):
  * Hutton daily gate uses TOTAL wet hours in the day (hours_rh_at_or_above) and daily min temp.
  * The Hutton criterion needs those qualifying days to be CONSECUTIVE (criterion_met).
  * Wallin DSV uses the LONGEST wet SPELL and the mean temperature DURING that spell.
Bands come from accumulated DSV thresholds in models.yaml (spray -> act, amber -> watch).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from engine.rules import criterion_met, hours_rh_at_or_above
from engine.wallin import wallin_dsv


@dataclass(frozen=True)
class DayStats:
    date: str
    wet_hours: int          # total hours RH >= threshold (Hutton 6 h gate)
    spell_hours: int        # longest consecutive wet spell (drives DSV)
    min_temp_c: float
    mean_wet_temp_c: float  # mean temp DURING the longest wet spell
    precip_mm: float
    qualifies: bool         # Hutton daily gate: min_temp >= min_temp_c AND wet_hours >= min_wet_hours
    dsv: int


@dataclass(frozen=True)
class CellAssessment:
    band: str               # safe | watch | act
    risk: float
    physics_risk: float
    ml_delta: float         # 0.0 in Phase 1 (no ML correction yet)
    criterion_met: bool
    dsv_today: int
    dsv_accum: int
    wet_hours: int
    min_temp_c: float
    mean_wet_temp_c: float


def _daily_index_groups(times: Sequence[str]) -> list[tuple[str, list[int]]]:
    groups: dict[str, list[int]] = {}
    order: list[str] = []
    for idx, t in enumerate(times):
        day = t[:10]  # "YYYY-MM-DD" prefix — pure string work, no clock
        if day not in groups:
            groups[day] = []
            order.append(day)
        groups[day].append(idx)
    return [(day, groups[day]) for day in order]


def daily_stats(
    times: Sequence[str],
    temperature: Sequence[float],
    relative_humidity: Sequence[float],
    precipitation: Sequence[float],
    params: dict,
    dsv_table=None,
) -> list[DayStats]:
    rh_thr = params["rh_threshold"]
    min_wet = params["min_wet_hours"]
    min_t = params["min_temp_c"]

    out: list[DayStats] = []
    for day, idxs in _daily_index_groups(times):
        day_rh = [relative_humidity[i] for i in idxs]
        day_temp = [temperature[i] for i in idxs]

        wet_hours = hours_rh_at_or_above(day_rh, rh_thr)

        # Longest wet spell and the mean temperature during it.
        best_len, best_sum = 0, 0.0
        cur_len, cur_sum = 0, 0.0
        for rh, tp in zip(day_rh, day_temp):
            if rh >= rh_thr:
                cur_len += 1
                cur_sum += tp
                if cur_len > best_len:
                    best_len, best_sum = cur_len, cur_sum
            else:
                cur_len, cur_sum = 0, 0.0
        mean_wet_temp = (best_sum / best_len) if best_len else 0.0

        min_temp = min(day_temp) if day_temp else 0.0
        precip = sum(precipitation[i] for i in idxs)
        qualifies = (min_temp >= min_t) and (wet_hours >= min_wet)
        dsv = (wallin_dsv(mean_wet_temp, best_len) if dsv_table is None
               else wallin_dsv(mean_wet_temp, best_len, dsv_table))

        out.append(DayStats(day, wet_hours, best_len, round(min_temp, 2),
                            round(mean_wet_temp, 2), round(precip, 2), qualifies, dsv))
    return out


def assess_cell(days: Sequence[DayStats], params: dict, severity: dict) -> CellAssessment:
    """Combine daily stats into a risk band. ml_delta is 0 in Phase 1 (physics only)."""
    crit = criterion_met([d.qualifies for d in days], params["consecutive_days"])
    dsv_accum = sum(d.dsv for d in days)
    dsv_today = days[0].dsv if days else 0

    spray = severity["spray_threshold_dsv"]
    amber = severity["amber_threshold_dsv"]
    # Severity-gated bands: the Hutton criterion escalates to "watch" only when disease
    # severity is actually developing (dsv_accum > 0). When the criterion is met but DSV is 0
    # because the wet-spell temperature is outside the pathogen's viable range (e.g. > 26.6 C
    # in monsoon heat), the cell is "safe" for this disease — avoiding a district-wide false
    # alarm (PRD §37: false alarms are the worst outcome). mean_wet_temp_c is exposed in the
    # artefact so this reason is auditable.
    if dsv_accum >= spray:
        band = "act"
    elif dsv_accum >= amber or (crit and dsv_accum > 0):
        band = "watch"
    else:
        band = "safe"

    physics_risk = min(1.0, dsv_accum / spray) if spray else 0.0
    return CellAssessment(
        band=band,
        risk=round(physics_risk, 3),
        physics_risk=round(physics_risk, 3),
        ml_delta=0.0,
        criterion_met=crit,
        dsv_today=dsv_today,
        dsv_accum=dsv_accum,
        wet_hours=days[0].wet_hours if days else 0,
        min_temp_c=days[0].min_temp_c if days else 0.0,
        mean_wet_temp_c=days[0].mean_wet_temp_c if days else 0.0,
    )
