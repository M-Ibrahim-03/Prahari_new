"""engine/spray.py — the seven spray-window gates (§13.2) and pipeline phrase rendering (§13.1).

Each gate gets its own test with the other six held clean, so a failure names the gate. The last
two tests cross into pipeline/spray_text.py: the window indices are useless to a farmer until they
read as "Tuesday morning, 6-9".
"""
import pytest

from engine.spray import (
    DARK, RAIN_AFTER, RAIN_NOW, TEMP_HIGH, TOO_LATE, WIND_CALM, WIND_HIGH,
    best_window, spray_windows, sprayability,
)
from pipeline.spray_text import render_window_phrase

PARAMS = {
    "rain_free_hours_after": 4.0, "max_rain_mm_during": 0.2,
    "wind_max_ms": 4.0, "wind_min_ms": 0.5, "temp_max_c": 33.0,
    "min_window_hours": 2.0, "ideal_window_hours": 3.0,
    "daylight_start_hour": 6, "daylight_end_hour": 18,
}
DAY = "2026-12-15"


def _day(temp=20.0, precip=0.0, wind=2.0):
    """A featureless 24 h day — every daylight hour sprayable until a test perturbs one."""
    times = [f"{DAY}T{h:02d}:00" for h in range(24)]
    return times, [temp] * 24, [precip] * 24, [wind] * 24


def _reasons(times, temp, precip, wind, hour, onset=None):
    return sprayability(times, temp, precip, wind, PARAMS, onset)[hour].reasons


# ── happy path ────────────────────────────────────────────────────────────────

def test_clean_day_yields_a_focused_morning_window():
    times, temp, precip, wind = _day()
    best = best_window(spray_windows(times, temp, precip, wind, PARAMS))
    assert best is not None
    assert int(times[best.start_idx][11:13]) == 6      # calmest slice is the early morning
    assert best.length == 3                             # focused to the ideal, not the whole span
    assert DARK in best.bounded_by                      # the span it sits in is bounded by night
    assert best.quality > 0


# ── one gate per test ───────────────────────────────────────────────────────────

def test_dark_blocks_night_hours():
    times, temp, precip, wind = _day()
    assert DARK in _reasons(times, temp, precip, wind, 3)
    assert DARK not in _reasons(times, temp, precip, wind, 10)


def test_rain_now_blocks_the_wet_hour():
    times, temp, precip, wind = _day()
    precip[10] = 1.0
    assert RAIN_NOW in _reasons(times, temp, precip, wind, 10)
    assert not sprayability(times, temp, precip, wind, PARAMS)[10].sprayable


def test_rain_after_bounds_a_window():
    times, temp, precip, wind = _day()
    precip[12] = 1.0                                    # rain at noon
    assert RAIN_AFTER in _reasons(times, temp, precip, wind, 9)   # 3 h before, within dry window
    r = spray_windows(times, temp, precip, wind, PARAMS)
    assert any(RAIN_AFTER in w.bounded_by for w in r.windows)     # the morning window ends on it


def test_wind_high_blocks():
    times, temp, precip, wind = _day()
    wind[10] = 6.0
    assert WIND_HIGH in _reasons(times, temp, precip, wind, 10)


def test_wind_calm_blocks():
    times, temp, precip, wind = _day()
    wind[10] = 0.1
    assert WIND_CALM in _reasons(times, temp, precip, wind, 10)


def test_temp_high_blocks():
    times, temp, precip, wind = _day()
    temp[10] = 34.0
    assert TEMP_HIGH in _reasons(times, temp, precip, wind, 10)


def test_too_late_excludes_windows_after_onset():
    times, temp, precip, wind = _day()
    assert TOO_LATE in _reasons(times, temp, precip, wind, 12, onset=9)
    r = spray_windows(times, temp, precip, wind, PARAMS, risk_onset_idx=9)
    assert all(w.end_idx <= 9 for w in r.windows)       # nothing survives past infection onset


def test_no_window_reports_the_obstacle():
    times, temp, precip, wind = _day(wind=6.0)          # too windy all day
    r = spray_windows(times, temp, precip, wind, PARAMS)
    assert best_window(r) is None
    assert WIND_HIGH in r.blocked_by


def test_missing_wind_cannot_fire_wind_gates():
    times, temp, precip, _ = _day()
    assert not (set(_reasons(times, temp, precip, None, 10)) & {WIND_HIGH, WIND_CALM})


# ── phrase rendering (pipeline/spray_text.py) ───────────────────────────────────

_HI = {
    "weekdays": ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"],
    "parts": {"morning": "सुबह", "midday": "दोपहर", "evening": "शाम"},
    "digits": "०१२३४५६७८९", "template": "{day} {part} {start}–{end} बजे",
}
_EN = {
    "weekdays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "parts": {"morning": "morning", "midday": "midday", "evening": "evening"},
    "digits": "0123456789", "template": "{day} {part}, {start}–{end}",
}


def test_phrase_hi_uses_devanagari_numerals():
    from datetime import date
    times, *_ = _day()
    wd = _HI["weekdays"][date.fromisoformat(DAY).weekday()]
    # window over 06:00, 07:00, 08:00 -> clock 6-9 (last sprayable hour + 1)
    assert render_window_phrase(times, 6, 9, _HI) == f"{wd} सुबह ६–९ बजे"


def test_phrase_en_afternoon_part():
    from datetime import date
    times, *_ = _day()
    wd = _EN["weekdays"][date.fromisoformat(DAY).weekday()]
    assert render_window_phrase(times, 13, 16, _EN) == f"{wd} midday, 13–16"
