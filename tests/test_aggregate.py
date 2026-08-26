"""Tests for per-cell assessment: daily stats and band logic. Pure."""
from engine.aggregate import assess_cell, daily_stats

PARAMS = {"rh_threshold": 90.0, "min_wet_hours": 6, "min_temp_c": 10.0, "consecutive_days": 2}
SEVERITY = {"spray_threshold_dsv": 18, "amber_threshold_dsv": 12}


def _day(date: str, wet_hours: int, temp_c: float, min_temp_c: float):
    """Build 24 hourly samples: `wet_hours` consecutive wet hours at temp_c, rest dry.

    Hour 0 is set to min_temp_c so the daily minimum is controlled.
    """
    times, temperature, rh, precip = [], [], [], []
    for h in range(24):
        times.append(f"{date}T{h:02d}:00")
        temperature.append(min_temp_c if h == 0 else temp_c)
        rh.append(95.0 if 1 <= h <= wet_hours else 60.0)
        precip.append(0.0)
    return times, temperature, rh, precip


def _concat(*days):
    times, temp, rh, precip = [], [], [], []
    for d in days:
        times += d[0]; temp += d[1]; rh += d[2]; precip += d[3]
    return times, temp, rh, precip


def test_two_consecutive_wet_warm_days_qualify():
    # 20 h wet at 18 C sits in Wallin's warm band and clears its breaks -> DSV accumulates.
    times, temp, rh, precip = _concat(
        _day("2026-01-10", wet_hours=20, temp_c=18.0, min_temp_c=11.0),
        _day("2026-01-11", wet_hours=20, temp_c=18.0, min_temp_c=11.0),
        _day("2026-01-12", wet_hours=0, temp_c=18.0, min_temp_c=11.0),  # dry
    )
    days = daily_stats(times, temp, rh, precip, PARAMS)
    assert [d.qualifies for d in days] == [True, True, False]
    assert days[0].mean_wet_temp_c == 18.0     # spell-mean, not daily-mean
    a = assess_cell(days, PARAMS, SEVERITY)
    assert a.criterion_met is True
    assert a.dsv_accum > 0
    assert a.band in {"watch", "act"}
    assert a.ml_delta == 0.0                    # physics only in Phase 1


def test_cold_days_do_not_qualify():
    times, temp, rh, precip = _concat(
        _day("2026-01-10", wet_hours=8, temp_c=6.0, min_temp_c=4.0),   # too cold
        _day("2026-01-11", wet_hours=8, temp_c=6.0, min_temp_c=4.0),
    )
    days = daily_stats(times, temp, rh, precip, PARAMS)
    assert all(d.qualifies is False for d in days)
    a = assess_cell(days, PARAMS, SEVERITY)
    assert a.criterion_met is False
    assert a.band == "safe"


def test_non_consecutive_qualifying_days_do_not_meet_criterion():
    times, temp, rh, precip = _concat(
        _day("2026-01-10", wet_hours=8, temp_c=14.0, min_temp_c=11.0),  # qualifies
        _day("2026-01-11", wet_hours=0, temp_c=14.0, min_temp_c=11.0),  # dry gap
        _day("2026-01-12", wet_hours=8, temp_c=14.0, min_temp_c=11.0),  # qualifies
    )
    days = daily_stats(times, temp, rh, precip, PARAMS)
    assert [d.qualifies for d in days] == [True, False, True]
    a = assess_cell(days, PARAMS, SEVERITY)
    assert a.criterion_met is False   # 🔴 consecutive, not total


def test_criterion_met_but_too_hot_is_safe_not_watch():
    # Monsoon-heat case from the live run: warm humid nights trip Hutton, but the wet-spell
    # temp (28 C) is above late blight's development ceiling (26.6 C), so DSV is 0 and the
    # severity-gated band is SAFE, not a false-alarm "watch".
    times, temp, rh, precip = _concat(
        _day("2026-08-24", wet_hours=18, temp_c=28.0, min_temp_c=25.0),
        _day("2026-08-25", wet_hours=18, temp_c=28.0, min_temp_c=25.0),
    )
    days = daily_stats(times, temp, rh, precip, PARAMS)
    assert all(d.qualifies for d in days)          # Hutton gate passes (warm + wet)
    a = assess_cell(days, PARAMS, SEVERITY)
    assert a.criterion_met is True                 # criterion IS met...
    assert a.dsv_accum == 0                         # ...but too hot for the pathogen
    assert a.band == "safe"                         # so no false alarm
