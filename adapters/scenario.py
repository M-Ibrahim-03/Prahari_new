"""Synthetic weather for demo scenarios.

🔴 WHY THIS EXISTS, AND THE LINE IT MUST NOT CROSS.

Late blight needs cool, wet weather: Wallin's development range tops out at 26.6 C. Farrukhabad in
late August sits near 27 C in the wet hours, so every cell correctly comes back `safe` — the
physics is right and the product looks like it does nothing. Potato is a rabi crop there; the
season this model is built for is December-February, which a run in August cannot observe.

So this adapter synthesises the *inputs* for a named scenario and lets the REAL engine compute the
outputs. Nothing here decides a band, a DSV or a risk value — it only produces temperature,
humidity and rainfall series, exactly as a weather provider would. If the engine says `act`, that
is Hutton and Wallin agreeing on this weather, not a number someone typed in.

The line: a scenario artefact is written to its own district code, carries data_status
"scenario", and names the scenario in its degradation notes, so it surfaces in the UI as
synthetic. Real forecasts are never overwritten by a scenario run.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Sequence

from adapters.weather import NodeSeries

# Magnus coefficients, same constants the engine uses — dew point here is DERIVED from the
# temperature and RH we generate, so the pair we hand over is physically self-consistent.
# An RH series that disagrees with its dew point would be an input no real station could produce.
MAGNUS_A = 17.625
MAGNUS_B = 243.04


def dew_point_from_rh(temp_c: float, rh_pct: float) -> float:
    rh = min(max(rh_pct, 1.0), 100.0)
    gamma = math.log(rh / 100.0) + (MAGNUS_A * temp_c) / (MAGNUS_B + temp_c)
    return (MAGNUS_B * gamma) / (MAGNUS_A - gamma)


@dataclass(frozen=True)
class ScenarioSpec:
    """A day's weather shape, described the way an agronomist would describe it."""
    name: str
    description: str
    start_date: str            # ISO date the series begins
    days: int
    day_temp_c: float          # afternoon maximum
    night_temp_c: float        # pre-dawn minimum
    wet_hours: int             # consecutive hours at or above wet_rh per night
    wet_rh: float              # RH during the wet spell
    dry_rh: float              # RH outside it
    precip_mm: float           # daily rainfall, dropped into the wet window
    # Gentle spatial variation so downscaling has something to interpolate; without it every
    # cell is identical and the interpolation step is untested by the demo.
    lat_gradient_c: float = 0.0
    lon_gradient_rh: float = 0.0
    # Hours of leaf wetness gained per degree of longitude east. A humid air mass has an EDGE:
    # the canopy stays wet into the afternoon on one side of the district and dries by mid-morning
    # on the other. This is the gradient that matters most, because Wallin keys DSV off wet-spell
    # DURATION — so it is what makes neighbouring villages land in different bands from the same
    # weather system, which is the entire argument for downscaling below district level.
    wet_hours_gradient_h: float = 0.0


def _node_wet_hours(spec: ScenarioSpec, lon_delta: float) -> int:
    """Wet-spell length for one node. Clamped to a real day."""
    n = spec.wet_hours + round(lon_delta * spec.wet_hours_gradient_h)
    return max(0, min(24, n))



def _hourly_temp(spec: ScenarioSpec, hour: int) -> float:
    """Sinusoidal diurnal cycle: coldest at 05:00, warmest at 15:00."""
    mean = (spec.day_temp_c + spec.night_temp_c) / 2.0
    amp = (spec.day_temp_c - spec.night_temp_c) / 2.0
    return mean - amp * math.cos((hour - 5) / 24.0 * 2 * math.pi)


def _hourly_wind(hour: int) -> float:
    """Light diurnal breeze: calmest before dawn (~1 m/s at 04:00), freshest mid-afternoon
    (~3.5 m/s at 16:00). Depends on the hour only, never on the node, so a scenario with no
    gradients stays byte-identical across cells (the determinism the ledger hash relies on).
    The band sits inside the spray gates' [wind_min, wind_max], so daytime hours are sprayable
    unless rain or darkness rules them out — which is what makes the window demo show a window.
    """
    mean, amp = 2.25, 1.25
    return mean - amp * math.cos((hour - 4) / 24.0 * 2 * math.pi)



def _wet_window(hours: int) -> set[int]:
    """The wet spell straddles dawn — leaves are wettest overnight and dry off mid-morning.

    Placed as a CONTIGUOUS run of hours inside one calendar day. Splitting it across midnight
    would create two fragments the Hutton criterion must not combine (§8.6 silent bug 3), which
    is a case for the test suite, not for a demo fixture pretending to be normal weather.
    """
    n = max(0, min(hours, 24))
    start = max(0, 6 - n // 2)      # centred on 06:00, clamped inside the day
    return set(range(start, start + n))


def build_series(
    spec: ScenarioSpec,
    coords: Sequence[tuple[float, float]],
    center: tuple[float, float],
) -> list[NodeSeries]:
    """One NodeSeries per coordinate, in the order given — the provider contract."""
    times: list[str] = []
    d0 = date.fromisoformat(spec.start_date)
    for d in range(spec.days):
        day = d0 + timedelta(days=d)
        for h in range(24):
            times.append(datetime(day.year, day.month, day.day, h).strftime("%Y-%m-%dT%H:%M"))

    c_lat, c_lon = center
    out: list[NodeSeries] = []

    for (lat, lon) in coords:
        # Deterministic per-node offset: no randomness, so two runs of the same scenario produce
        # byte-identical artefacts and the ledger hash is reproducible.
        t_off = (lat - c_lat) * spec.lat_gradient_c
        rh_off = (lon - c_lon) * spec.lon_gradient_rh
        # Duration varies per node too, so the wet spell has an edge across the district.
        wet = _wet_window(_node_wet_hours(spec, lon - c_lon))
        # Rain falls only while the canopy is wet, so a node with no wet hours gets no rain —
        # dividing by a floor of 1 would sprinkle rain onto a dry node and desynchronise the two.
        precip_per_wet_hour = (spec.precip_mm / len(wet)) if wet else 0.0

        temp: list[float] = []
        rh: list[float] = []
        dew: list[float] = []
        precip: list[float] = []
        wind: list[float] = []
        for _ in range(spec.days):
            for h in range(24):
                t = round(_hourly_temp(spec, h) + t_off, 2)
                r = round(min(100.0, max(5.0, (spec.wet_rh if h in wet else spec.dry_rh) + rh_off)), 2)
                temp.append(t)
                rh.append(r)
                dew.append(round(dew_point_from_rh(t, r), 2))
                precip.append(round(precip_per_wet_hour, 2) if h in wet else 0.0)
                wind.append(round(_hourly_wind(h), 2))

        out.append(NodeSeries(
            lat=lat, lon=lon, times=tuple(times),
            variables={
                "temperature_2m": tuple(temp),
                "relative_humidity_2m": tuple(rh),
                "dew_point_2m": tuple(dew),
                "precipitation": tuple(precip),
                "wind_speed_10m": tuple(wind),
            },
        ))
    return out


class ScenarioProvider:
    """WeatherProvider implementation backed by a ScenarioSpec instead of a network call."""

    def __init__(self, spec: ScenarioSpec, center: tuple[float, float]) -> None:
        self.spec = spec
        self.center = center

    def fetch(self, coords, variables=None, forecast_days=8, past_days=2) -> list[NodeSeries]:
        # Signature matches OpenMeteoProvider so nightly.py can swap one for the other; the
        # scenario's own `days` governs length, since a fixed weather shape has no horizon.
        return build_series(self.spec, list(coords), self.center)


def spec_from_config(name: str, cfg: dict) -> ScenarioSpec:
    return ScenarioSpec(
        name=name,
        description=cfg["description"],
        start_date=cfg["start_date"],
        days=int(cfg["days"]),
        day_temp_c=float(cfg["day_temp_c"]),
        night_temp_c=float(cfg["night_temp_c"]),
        wet_hours=int(cfg["wet_hours"]),
        wet_rh=float(cfg["wet_rh"]),
        dry_rh=float(cfg["dry_rh"]),
        precip_mm=float(cfg["precip_mm"]),
        lat_gradient_c=float(cfg.get("lat_gradient_c", 0.0)),
        lon_gradient_rh=float(cfg.get("lon_gradient_rh", 0.0)),
        wet_hours_gradient_h=float(cfg.get("wet_hours_gradient_h", 0.0)),
    )
