"""Elevation providers — IMPURE. Fetch-once-commit data (§29.4): elevation does not change,
so it is fetched once per district and committed, never fetched nightly.

Two implementations (§29.7): OpenMeteoElevation (live, keyless) + StaticElevation (committed).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, Sequence

import requests

OPEN_METEO_ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"


class ElevationProvider(Protocol):
    def elevations(self, coords: Sequence[tuple[float, float]]) -> list[float]:
        """Metres above sea level, one per coord, in the SAME ORDER as `coords`."""
        ...


class OpenMeteoElevation:
    """Live, keyless Open-Meteo elevation (SRTM-derived). Batches up to 100 coords per call."""

    def __init__(self, timeout_s: float = 30.0, batch: int = 100):
        self.timeout_s = timeout_s
        self.batch = batch

    def elevations(self, coords):
        out: list[float] = []
        for i in range(0, len(coords), self.batch):
            chunk = coords[i:i + self.batch]
            params = {
                "latitude": ",".join(f"{c[0]:.4f}" for c in chunk),
                "longitude": ",".join(f"{c[1]:.4f}" for c in chunk),
            }
            resp = requests.get(OPEN_METEO_ELEVATION_URL, params=params, timeout=self.timeout_s)
            resp.raise_for_status()
            out.extend(float(e) for e in resp.json()["elevation"])
        if len(out) != len(coords):
            raise ValueError(f"got {len(out)} elevations for {len(coords)} coords")
        return out


class StaticElevation:
    """Reads elevations from a committed JSON file: {"lat,lon": elevation_m}. This is the
    fetch-once-commit path — the nightly job uses this, never the live provider."""

    def __init__(self, table: dict[str, float]):
        self._table = table

    @classmethod
    def from_file(cls, path: str | Path) -> "StaticElevation":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    @staticmethod
    def _key(lat: float, lon: float) -> str:
        return f"{lat:.4f},{lon:.4f}"

    def elevations(self, coords):
        return [self._table[self._key(la, lo)] for (la, lo) in coords]


def fetch_and_commit(coords: Sequence[tuple[float, float]], path: str | Path) -> dict[str, float]:
    """Fetch elevations live and write the committable JSON table. Run ONCE per district."""
    live = OpenMeteoElevation()
    values = live.elevations(coords)
    table = {StaticElevation._key(la, lo): ev for (la, lo), ev in zip(coords, values)}
    Path(path).write_text(json.dumps(table, indent=2), encoding="utf-8")
    return table
