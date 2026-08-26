"""Assemble the §29.5 artefact contract — PRAHARI's real public API.

Pure dict assembly (no I/O, no clock — run_id is passed in). The nightly job writes the result.
Applies the §29.6 payload budget: 4-decimal coords, 2-decimal floats, drop unknown properties
(we omit fields we don't yet compute rather than fake them).
"""
from __future__ import annotations

from typing import Sequence

from engine.aggregate import CellAssessment
from engine.grid import Grid

SCHEMA_VERSION = "2.0.0"


def cell_polygon(lat: float, lon: float, cell_step_deg: float) -> list[list[list[float]]]:
    """A closed square ring around a cell centre. GeoJSON order is [lon, lat]."""
    h = cell_step_deg / 2.0
    ring = [
        [round(lon - h, 4), round(lat - h, 4)],
        [round(lon + h, 4), round(lat - h, 4)],
        [round(lon + h, 4), round(lat + h, 4)],
        [round(lon - h, 4), round(lat + h, 4)],
        [round(lon - h, 4), round(lat - h, 4)],
    ]
    return [ring]


def build_feature_collection(
    *,
    grid: Grid,
    assessments: Sequence[CellAssessment],
    cell_step_deg: float,
    run_id: str,
    district_code: str,
    horizon: str,
    model_id: str,
    model_version: str,
    engine_git_sha: str,
    data_status: str,
    degradation: Sequence[str],
) -> dict:
    if len(assessments) != len(grid.cells):
        raise ValueError(f"{len(assessments)} assessments for {len(grid.cells)} cells")

    counts = {"safe": 0, "watch": 0, "act": 0}
    features = []
    for cell, a in zip(grid.cells, assessments):
        counts[a.band] += 1
        props = {
            "cell_id": cell.cell_id,
            "band": a.band,
            "risk": round(a.risk, 2),
            "physics_risk": round(a.physics_risk, 2),
            "ml_delta": round(a.ml_delta, 2),
            "dsv_today": a.dsv_today,
            "dsv_accum_7d": a.dsv_accum,
            "criterion_met": a.criterion_met,
            "wet_hours": a.wet_hours,
            "min_temp_c": round(a.min_temp_c, 2),
            "mean_wet_temp_c": round(a.mean_wet_temp_c, 2),  # 🔴 exposed: reveals silent-bug 2
        }
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": cell_polygon(cell.lat, cell.lon, cell_step_deg)},
            "properties": props,
        })

    return {
        "type": "FeatureCollection",
        "prahari": {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "district": district_code,
            "horizon": horizon,
            "model": {"id": model_id, "version": model_version, "engine_git_sha": engine_git_sha},
            "data_status": data_status,
            "degradation": list(degradation),
            "node_count": len(grid.nodes),
            "cell_count": len(grid.cells),
            "counts": counts,
        },
        "features": features,
    }
