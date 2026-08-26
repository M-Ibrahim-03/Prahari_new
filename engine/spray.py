"""Spray-window scoring — PURE (PRD §13.1/§13.2, FR-7.1/7.2).

Given a cell's hourly forecast, decide WHEN it is safe and useful to spray. This module writes no
band and no dose (§13.3, FR-7.10): it only ranks hours by whether a spray applied then would (a)
reach the leaf and (b) not wash off before it dries. Seven gates, each with a reason code the UI
and the artefact can show verbatim, so a farmer told "not this afternoon" also learns why.

🔴 PURE. No network, no filesystem, no clock, no randomness, no env. Hour-of-day is read off the
ISO timestamp string (`"...T06:00"[11:13]`), never from a wall clock — the caller (pipeline) owns
time. The parameters (thresholds, daylight span) come from models.yaml, never hard-coded here:
the agronomy lives in config (§8.4.3), this file only applies it.

The gates (PRD §13.2):
  RAIN_NOW    rain is falling this hour                     -> the spray is diluted / not applied
  RAIN_AFTER  rain falls within `rain_free_hours_after`     -> it washes off before it dries on
  WIND_HIGH   wind above `wind_max_ms`                       -> drift onto neighbours / off-target
  WIND_CALM   wind below `wind_min_ms`                       -> no mixing, uneven deposition, inversion
  TEMP_HIGH   temperature above `temp_max_c`                 -> evaporation / scorch, label breach
  DARK        outside [daylight_start_hour, daylight_end_hour)
  TOO_LATE    at or after infection onset (`risk_onset_idx`) -> the spray can no longer be preventive

A window is a maximal run of consecutive sprayable hours at least `min_window_hours` long. Windows
are returned best-first; `bounded_by` records why each one does not start earlier or run longer, so
the caller can explain the edges ("spray must finish before the afternoon rain").
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

# Reason codes — stable strings shown in the artefact (§29.5) and mapped to farmer copy in the UI.
RAIN_NOW = "RAIN_NOW"
RAIN_AFTER = "RAIN_AFTER"
WIND_HIGH = "WIND_HIGH"
WIND_CALM = "WIND_CALM"
TEMP_HIGH = "TEMP_HIGH"
DARK = "DARK"
TOO_LATE = "TOO_LATE"

# Fixed order so reason tuples are deterministic regardless of which gates fired (ledger-safe).
_ORDER = (RAIN_NOW, RAIN_AFTER, WIND_HIGH, WIND_CALM, TEMP_HIGH, DARK, TOO_LATE)


@dataclass(frozen=True)
class HourVerdict:
    """One hour: is it sprayable, and if not, every reason it is not."""
    sprayable: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class SprayWindow:
    """A contiguous run [start_idx, end_idx) of sprayable hours, as indices into the series."""
    start_idx: int      # inclusive
    end_idx: int        # exclusive
    length: int         # end_idx - start_idx, in hourly samples
    quality: float      # 0..1; higher is a longer, calmer window
    bounded_by: tuple[str, ...]   # why it does not extend earlier / later


@dataclass(frozen=True)
class SprayReport:
    windows: tuple[SprayWindow, ...]   # best-first
    blocked_by: tuple[str, ...]        # the best window's edges, or (if none) the day's obstacles


def _hour_of_day(iso: str) -> int:
    """Hour field of an ISO timestamp string. Pure — no datetime, no clock."""
    return int(iso[11:13])


def sprayability(
    times: Sequence[str],
    temp: Sequence[float],
    precip: Sequence[float],
    wind: Optional[Sequence[Optional[float]]],
    params: dict,
    risk_onset_idx: Optional[int] = None,
) -> list[HourVerdict]:
    """Evaluate every hour against the seven gates.

    `wind` may be None (provider gave no wind) or contain None entries (a corner was missing);
    where wind is unknown the two wind gates cannot fire — we do not invent a reason to block, we
    simply cannot vouch for it, which the caller reflects as lower confidence, not as a red hour.
    """
    n = len(times)
    rain_max = float(params["max_rain_mm_during"])
    look_ahead = int(round(float(params["rain_free_hours_after"])))
    wind_max = float(params["wind_max_ms"])
    wind_min = float(params["wind_min_ms"])
    temp_max = float(params["temp_max_c"])
    day_start = int(params["daylight_start_hour"])
    day_end = int(params["daylight_end_hour"])

    out: list[HourVerdict] = []
    for h in range(n):
        fired: set[str] = set()

        if precip[h] is not None and precip[h] > rain_max:
            fired.add(RAIN_NOW)
        # Rain within the drying window after application washes the spray off the leaf.
        for j in range(h + 1, min(n, h + 1 + look_ahead)):
            if precip[j] is not None and precip[j] > rain_max:
                fired.add(RAIN_AFTER)
                break

        w = wind[h] if wind is not None else None
        if w is not None:
            if w > wind_max:
                fired.add(WIND_HIGH)
            elif w < wind_min:
                fired.add(WIND_CALM)

        if temp[h] is not None and temp[h] > temp_max:
            fired.add(TEMP_HIGH)

        hod = _hour_of_day(times[h])
        if hod < day_start or hod >= day_end:
            fired.add(DARK)

        if risk_onset_idx is not None and h >= risk_onset_idx:
            fired.add(TOO_LATE)

        reasons = tuple(r for r in _ORDER if r in fired)
        out.append(HourVerdict(sprayable=not reasons, reasons=reasons))
    return out


def _quality(window_idx: range, wind: Optional[Sequence[Optional[float]]], params: dict) -> float:
    """0..1 for a candidate window: longer toward the ideal, and calmer air — a light legal
    breeze deposits spray better than a stiff wind. Wind unknown -> length only."""
    count = len(window_idx)
    ideal = float(params.get("ideal_window_hours", params["min_window_hours"]))
    length_factor = min(1.0, count / ideal) if ideal > 0 else 1.0

    winds = [wind[h] for h in window_idx] if wind is not None else []
    if winds and all(w is not None for w in winds):
        wind_min = float(params["wind_min_ms"])
        wind_max = float(params["wind_max_ms"])
        span = max(wind_max - wind_min, 1e-9)
        # Best near the calm end of the legal band, worst near the drift limit.
        wind_scores = [max(0.0, min(1.0, (wind_max - w) / span)) for w in winds]
        wind_factor = sum(wind_scores) / len(wind_scores)
        q = 0.5 * length_factor + 0.5 * wind_factor
    else:
        q = length_factor
    return round(max(0.0, min(1.0, q)), 3)


def spray_windows(
    times: Sequence[str],
    temp: Sequence[float],
    precip: Sequence[float],
    wind: Optional[Sequence[Optional[float]]],
    params: dict,
    risk_onset_idx: Optional[int] = None,
) -> SprayReport:
    """Rank the sprayable windows in the forecast, best-first.

    A window must be at least `min_window_hours` long. `bounded_by` on each window is the union of
    the reasons at the hour just before it and just after it — the obstacles that stop it growing.
    When no window exists, `blocked_by` on the report is the set of obstacles seen during daylight,
    so the caller can say why today offers no window at all rather than going silent.
    """
    verdicts = sprayability(times, temp, precip, wind, params, risk_onset_idx)
    n = len(verdicts)
    min_hours = float(params["min_window_hours"])
    ideal_hours = int(round(float(params.get("ideal_window_hours", min_hours))))
    min_len = int(round(min_hours))

    windows: list[SprayWindow] = []
    h = 0
    while h < n:
        if not verdicts[h].sprayable:
            h += 1
            continue
        start = h
        while h < n and verdicts[h].sprayable:
            h += 1
        end = h  # exclusive end of the maximal sprayable SPAN
        if end - start < min_hours:
            continue

        # The span's edges carry the obstacle reasons. The recommended window is a focused
        # best-conditions slice inside the span — "spray 6–9", never "spray the whole daylight".
        bounded: set[str] = set()
        if start - 1 >= 0:
            bounded.update(verdicts[start - 1].reasons)
        if end < n:
            bounded.update(verdicts[end].reasons)
        bounded_by = tuple(r for r in _ORDER if r in bounded)

        win_len = min(end - start, max(ideal_hours, min_len))
        # Slide the window across the span; take the highest-quality (calmest) slice, earliest
        # on a tie — an urgent 'act' spray should go on as soon as conditions are good.
        pick_start, pick_q = start, -1.0
        for s in range(start, end - win_len + 1):
            q = _quality(range(s, s + win_len), wind, params)
            if q > pick_q:
                pick_q, pick_start = q, s
        windows.append(SprayWindow(
            start_idx=pick_start, end_idx=pick_start + win_len, length=win_len,
            quality=pick_q, bounded_by=bounded_by,
        ))

    windows.sort(key=lambda wnd: (-wnd.quality, wnd.start_idx))

    if windows:
        blocked_by = windows[0].bounded_by
    else:
        # No window: report the daytime obstacles (ignore DARK — night is not an obstacle to
        # explain), falling back to every reason seen if the whole horizon was dark.
        day = {r for v in verdicts for r in v.reasons if not (len(v.reasons) == 1 and v.reasons[0] == DARK)}
        day.discard(DARK)
        if not day:
            day = {r for v in verdicts for r in v.reasons}
        blocked_by = tuple(r for r in _ORDER if r in day)

    return SprayReport(windows=tuple(windows), blocked_by=blocked_by)


def best_window(report: Optional[SprayReport]) -> Optional[SprayWindow]:
    """The single window to show a farmer: the highest-quality one, or None if there is none."""
    if report is None or not report.windows:
        return None
    return report.windows[0]
