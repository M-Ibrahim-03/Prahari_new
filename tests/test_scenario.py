"""Tests for the demo-scenario weather adapter. Offline — no network, no clock, no randomness.

What matters here is NOT that the numbers look plausible. It is that the scenario produces
physically self-consistent INPUTS and that the real engine, unmodified, derives the advertised
outcome from them. A scenario that reached `act` by any other route would be a lie told with a
straight face, so the last test in this file drives the actual pipeline stages.
"""
import pytest

from adapters.scenario import (
    ScenarioProvider,
    ScenarioSpec,
    _node_wet_hours,
    _wet_window,
    build_series,
    dew_point_from_rh,
    spec_from_config,
)
from engine.interpolate import rh_from_temp_and_dewpoint

CENTER = (27.40, 79.60)

SPEC = ScenarioSpec(
    name="unit", description="fixture", start_date="2026-12-18", days=3,
    day_temp_c=17.0, night_temp_c=12.5, wet_hours=16, wet_rh=97.0, dry_rh=70.0,
    precip_mm=2.4,
)


def _centre_series(spec=SPEC):
    return build_series(spec, [CENTER], CENTER)[0]


# ── shape and time axis ───────────────────────────────────────────────────────

def test_one_series_per_coordinate_in_the_order_given():
    coords = [(27.30, 79.50), CENTER, (27.50, 79.70)]
    out = build_series(SPEC, coords, CENTER)
    assert [(s.lat, s.lon) for s in out] == coords


def test_hourly_axis_is_contiguous_and_the_right_length():
    s = _centre_series()
    assert len(s.times) == SPEC.days * 24
    assert s.times[0] == "2026-12-18T00:00"
    assert s.times[23] == "2026-12-18T23:00"
    assert s.times[24] == "2026-12-19T00:00"
    assert s.times[-1] == "2026-12-20T23:00"
    for name, values in s.variables.items():
        assert len(values) == len(s.times), name


def test_deterministic_no_hidden_randomness():
    """Two runs of the same scenario must be byte-identical, or the ledger hash is not
    reproducible and the whole chained-alert argument collapses."""
    a = build_series(SPEC, [CENTER, (27.5, 79.7)], CENTER)
    b = build_series(SPEC, [CENTER, (27.5, 79.7)], CENTER)
    assert [x.variables for x in a] == [x.variables for x in b]


# ── physical self-consistency ─────────────────────────────────────────────────

def test_dew_point_and_rh_agree():
    """🔴 The engine RECOMPUTES RH from interpolated temperature and dew point (§8.3). If the
    generated pair disagreed, the scenario's stated RH would silently not be the RH the engine
    sees, and every band would be explained by a bug in the fixture.
    """
    s = _centre_series()
    for t, rh, td in zip(s.variables["temperature_2m"],
                         s.variables["relative_humidity_2m"],
                         s.variables["dew_point_2m"]):
        assert rh_from_temp_and_dewpoint(t, td) == pytest.approx(rh, abs=0.15)


def test_dew_point_equals_temperature_at_saturation():
    assert dew_point_from_rh(15.0, 100.0) == pytest.approx(15.0, abs=1e-6)


def test_dew_point_is_below_temperature_when_unsaturated():
    assert dew_point_from_rh(20.0, 60.0) < 20.0


def test_diurnal_cycle_spans_night_temp_to_day_temp():
    s = _centre_series()
    temps = s.variables["temperature_2m"]
    assert min(temps) == pytest.approx(SPEC.night_temp_c, abs=0.01)
    assert max(temps) == pytest.approx(SPEC.day_temp_c, abs=0.01)
    # Coldest before dawn, warmest mid-afternoon — not the other way round.
    day0 = list(temps[:24])
    assert day0.index(min(day0)) == 5
    assert day0.index(max(day0)) == 17


# ── the wet window ────────────────────────────────────────────────────────────

def test_wet_window_is_contiguous_and_inside_one_day():
    """§8.6 silent bug 3: two wet fragments must never be combined. A fixture that straddled
    midnight would exercise that bug by accident instead of testing it on purpose.
    """
    for hours in range(0, 25):
        w = _wet_window(hours)
        assert len(w) == hours
        if hours:
            assert w == set(range(min(w), max(w) + 1))   # contiguous
            assert 0 <= min(w) and max(w) <= 23          # inside the day


def test_wet_hours_in_the_series_match_the_spec():
    s = _centre_series()
    rh = s.variables["relative_humidity_2m"]
    for d in range(SPEC.days):
        wet = [v for v in rh[d * 24:(d + 1) * 24] if v >= 90.0]
        assert len(wet) == SPEC.wet_hours


def test_wet_hours_gradient_lengthens_the_spell_eastward():
    """The gradient is the mechanism that puts neighbouring villages in different bands from one
    weather system, which is the whole justification for computing below district level.
    """
    spec = ScenarioSpec(**{**SPEC.__dict__, "wet_hours": 17, "wet_hours_gradient_h": 35.0})
    west, centre, east = build_series(spec, [(27.4, 79.40), CENTER, (27.4, 79.80)], CENTER)

    def wet_count(s):
        return sum(1 for v in s.variables["relative_humidity_2m"][:24] if v >= 90.0)

    assert wet_count(west) == 10        # 17 + round(-0.20 * 35)
    assert wet_count(centre) == 17
    assert wet_count(east) == 24        # 17 + round(+0.20 * 35)
    assert wet_count(west) < wet_count(centre) < wet_count(east)


def test_wet_hours_clamped_to_a_real_day():
    assert _node_wet_hours(ScenarioSpec(**{**SPEC.__dict__, "wet_hours_gradient_h": 500.0}), 1.0) == 24
    assert _node_wet_hours(ScenarioSpec(**{**SPEC.__dict__, "wet_hours_gradient_h": 500.0}), -1.0) == 0


# ── rainfall ──────────────────────────────────────────────────────────────────

def test_rain_falls_only_while_the_canopy_is_wet_and_sums_to_the_spec():
    s = _centre_series()
    rh = s.variables["relative_humidity_2m"]
    pr = s.variables["precipitation"]
    for t, r, p in zip(s.times, rh, pr):
        if r < 90.0:
            assert p == 0.0, f"rain during a dry hour at {t}"
    for d in range(SPEC.days):
        assert sum(pr[d * 24:(d + 1) * 24]) == pytest.approx(SPEC.precip_mm, abs=0.2)


def test_a_node_with_no_wet_hours_gets_no_rain():
    """🔴 REGRESSION. Dividing the daily rainfall by `max(1, len(wet))` sprinkled rain onto a node
    whose wet window was empty — rain falling from a sky with no humidity, and rainfall
    desynchronised from leaf wetness for exactly the driest cells in the district.
    """
    spec = ScenarioSpec(**{**SPEC.__dict__, "wet_hours": 0, "precip_mm": 5.0})
    s = _centre_series(spec)
    assert sum(s.variables["precipitation"]) == 0.0
    assert all(v < 90.0 for v in s.variables["relative_humidity_2m"])


# ── config plumbing ───────────────────────────────────────────────────────────

def test_spec_from_config_reads_every_field():
    cfg = {
        "description": "d", "start_date": "2026-12-18", "days": 4,
        "day_temp_c": 17.0, "night_temp_c": 12.5, "wet_hours": 16,
        "wet_rh": 97.0, "dry_rh": 70.0, "precip_mm": 2.4,
        "lat_gradient_c": 5.0, "lon_gradient_rh": 4.0, "wet_hours_gradient_h": 35.0,
    }
    spec = spec_from_config("named", cfg)
    assert spec.name == "named"
    assert (spec.days, spec.wet_hours) == (4, 16)
    assert (spec.lat_gradient_c, spec.lon_gradient_rh, spec.wet_hours_gradient_h) == (5.0, 4.0, 35.0)


def test_gradients_default_to_zero_so_a_minimal_scenario_is_uniform():
    cfg = {
        "description": "d", "start_date": "2026-12-18", "days": 2,
        "day_temp_c": 17.0, "night_temp_c": 12.5, "wet_hours": 16,
        "wet_rh": 97.0, "dry_rh": 70.0, "precip_mm": 0.0,
    }
    spec = spec_from_config("flat", cfg)
    assert (spec.lat_gradient_c, spec.lon_gradient_rh, spec.wet_hours_gradient_h) == (0.0, 0.0, 0.0)
    a, b = build_series(spec, [(27.3, 79.5), (27.5, 79.7)], CENTER)
    assert a.variables == b.variables


def test_provider_matches_the_weather_provider_signature():
    """nightly.py swaps ScenarioProvider in for OpenMeteoProvider, so extra keyword arguments
    must be accepted and ignored rather than raising."""
    p = ScenarioProvider(SPEC, CENTER)
    out = p.fetch([CENTER], ["temperature_2m"], forecast_days=8, past_days=2)
    assert len(out) == 1 and len(out[0].times) == SPEC.days * 24


# ── the property that actually matters ────────────────────────────────────────

def test_configured_scenarios_produce_the_bands_they_advertise():
    """🔴 END-TO-END, THROUGH THE REAL ENGINE. The scenario adapter synthesises inputs only; if
    Hutton and Wallin do not agree that this weather is dangerous, the demo has no business
    showing a spray advisory.

    This test is the one that caught the original failure. The first blight_outbreak fixture used
    cold nights and a 14 h dew period and every cell came back safe — correctly, because Wallin
    keys DSV off wet-spell DURATION and 14 h at 13 C is below the 15 h breakpoint. Epidemics are
    built by prolonged overcast drizzle, not by cold dewy nights.
    """
    import yaml
    from pathlib import Path

    from engine.aggregate import assess_cell, daily_stats
    from engine.grid import build_grid
    from pipeline.nightly import interpolate_cells

    root = Path(__file__).resolve().parent.parent
    cfg_dir = root / "pipeline" / "config"
    load = lambda p: yaml.safe_load((cfg_dir / p).read_text(encoding="utf-8"))

    scenarios = load("scenarios.yaml")["scenarios"]
    dist = [d for d in load("districts.yaml")["districts"] if d.get("active")][0]
    model = load("models.yaml")["models"][dist["model"]]
    params, severity = model["params"], model["severity"]

    grid = build_grid(
        district=dist["code"], center_lat=dist["center"]["lat"], center_lon=dist["center"]["lon"],
        half_span_deg=dist["half_span_deg"], node_step_deg=dist["node_step_deg"],
        cell_step_deg=dist["cell_step_deg"], id_prefix=dist["id_prefix"],
    )
    centre = (dist["center"]["lat"], dist["center"]["lon"])

    def bands_for(name):
        spec = spec_from_config(name, scenarios[name])
        series = ScenarioProvider(spec, centre).fetch(list(grid.nodes))
        per_cell = interpolate_cells(grid, series, spec.start_date)
        out = []
        for (times, temp, rh, precip, _wind) in per_cell:
            days = daily_stats(times, temp, rh, precip, params, severity["dsv_table"])
            out.append(assess_cell(days, params, severity))
        return out

    # blight_outbreak: escalates to spray, and the wet-spell gradient spreads the district across
    # all three bands rather than painting it one colour.
    a = bands_for("blight_outbreak")
    counts = {b: sum(1 for x in a if x.band == b) for b in ("safe", "watch", "act")}
    assert counts["act"] > 0, "blight_outbreak must reach the spray threshold"
    assert counts["watch"] > 0 and counts["safe"] > 0, f"expected a spread, got {counts}"
    assert all(x.criterion_met for x in a), "both Hutton legs should hold district-wide"
    assert max(x.dsv_accum for x in a) >= severity["spray_threshold_dsv"]

    # borderline_watch: the criterion is met and severity accrues, but never enough to spray.
    b = bands_for("borderline_watch")
    assert all(x.band != "act" for x in b), "borderline_watch must not reach spray"
    assert any(x.band == "watch" for x in b)
    assert max(x.dsv_accum for x in b) < severity["spray_threshold_dsv"]

    # dry_spell: safe for the RIGHT reason — the wet-hours leg fails outright, DSV never starts.
    c = bands_for("dry_spell")
    assert all(x.band == "safe" for x in c)
    assert not any(x.criterion_met for x in c), "dry_spell must fail the Hutton wet-hours leg"
    assert all(x.dsv_accum == 0 for x in c)
