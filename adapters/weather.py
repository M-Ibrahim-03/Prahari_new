"""Weather providers — IMPURE (all network I/O lives here, never in engine/).

PRD §29.7 requires every external system behind an interface with >=2 impls, so a
provider swap is a config edit. Here: OpenMeteoProvider (live) + ReplayProvider (fixtures).

🔴 The three Open-Meteo traps (§29.2), each handled explicitly below:
  1. Single coordinate -> OBJECT, multiple -> ARRAY. Normalise to a list.
  2. past_days SHIFTS THE ARRAY ORIGIN. Index 0 is NOT "today". Locate days by parsing time[].
  3. Returned coords are SNAPPED to the model grid. Assert closeness to the request or the
     lattice geometry silently drifts away from the precomputed interpolation weights.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

import requests

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# The eight hourly variables the engine consumes (§29.2). dew_point is required so RH can be
# RECOMPUTED after downscaling (§8.3) instead of being interpolated directly.
DEFAULT_VARIABLES = (
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "cloud_cover",
    "et0_fao_evapotranspiration",
)

# Open-Meteo snaps requests to its ~0.1 deg model grid; anything past this is a real mismatch.
SNAP_TOLERANCE_DEG = 0.15


@dataclass(frozen=True)
class NodeSeries:
    """Hourly series for one node. lat/lon are the REQUESTED coords (grid geometry), not the
    snapped ones — the interpolation weights were computed against the request."""
    lat: float
    lon: float
    times: tuple[str, ...]                       # ISO local times, e.g. "2026-01-14T00:00"
    variables: dict[str, tuple[float, ...]]      # variable name -> hourly values


class WeatherProvider(Protocol):
    def fetch(
        self,
        coords: Sequence[tuple[float, float]],
        variables: Sequence[str] = DEFAULT_VARIABLES,
        forecast_days: int = 8,
        past_days: int = 2,
    ) -> list[NodeSeries]:
        """One implementation per data source. Returns one NodeSeries per requested coord,
        in the SAME ORDER as `coords`."""
        ...


def align_from_date(series: NodeSeries, start_date: str) -> NodeSeries:
    """Trap #2: trim a series to start at the first hour whose date >= start_date.

    `start_date` is a "YYYY-MM-DD" string supplied by the impure caller (pipeline owns the
    clock). Pure string comparison — no datetime, so the trimmed series stays engine-safe.
    """
    start_idx = 0
    for i, t in enumerate(series.times):
        if t[:10] >= start_date:
            start_idx = i
            break
    else:
        start_idx = len(series.times)
    return NodeSeries(
        lat=series.lat,
        lon=series.lon,
        times=series.times[start_idx:],
        variables={k: v[start_idx:] for k, v in series.variables.items()},
    )


class OpenMeteoProvider:
    """Live, keyless Open-Meteo. timezone is pinned so day-bucketing aligns to the farmer's
    local day, not UTC."""

    def __init__(self, timezone: str = "Asia/Kolkata", timeout_s: float = 30.0):
        self.timezone = timezone
        self.timeout_s = timeout_s

    def fetch(self, coords, variables=DEFAULT_VARIABLES, forecast_days=8, past_days=2):
        lats = [c[0] for c in coords]
        lons = [c[1] for c in coords]
        params = {
            "latitude": ",".join(f"{v:.4f}" for v in lats),
            "longitude": ",".join(f"{v:.4f}" for v in lons),
            "hourly": ",".join(variables),
            "forecast_days": forecast_days,
            "past_days": past_days,
            "timezone": self.timezone,
        }
        resp = requests.get(OPEN_METEO_FORECAST_URL, params=params, timeout=self.timeout_s)
        resp.raise_for_status()
        data = resp.json()

        # Trap #1: single coord -> object; multiple -> array. Normalise.
        blocks = data if isinstance(data, list) else [data]
        if len(blocks) != len(coords):
            raise ValueError(f"Open-Meteo returned {len(blocks)} blocks for {len(coords)} coords")

        out: list[NodeSeries] = []
        for (req_lat, req_lon), block in zip(coords, blocks):
            # Trap #3: verify the snapped coords are near what we asked for.
            if abs(block["latitude"] - req_lat) >= SNAP_TOLERANCE_DEG:
                raise ValueError(f"lat snapped too far: got {block['latitude']} wanted {req_lat}")
            if abs(block["longitude"] - req_lon) >= SNAP_TOLERANCE_DEG:
                raise ValueError(f"lon snapped too far: got {block['longitude']} wanted {req_lon}")
            hourly = block["hourly"]
            out.append(NodeSeries(
                lat=req_lat, lon=req_lon,               # keep the REQUESTED coords
                times=tuple(hourly["time"]),
                variables={v: tuple(hourly[v]) for v in variables},
            ))
        return out


class ReplayProvider:
    """Deterministic fixture provider — no network. Used by tests and offline degraded runs
    (the '>=2 implementations' half of §29.7). Constructed from prebuilt NodeSeries."""

    def __init__(self, series: Sequence[NodeSeries]):
        self._series = list(series)

    def fetch(self, coords, variables=DEFAULT_VARIABLES, forecast_days=8, past_days=2):
        if len(self._series) != len(coords):
            raise ValueError(f"ReplayProvider has {len(self._series)} series for {len(coords)} coords")
        return list(self._series)
