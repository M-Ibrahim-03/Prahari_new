"""Assemble the farmer-facing field artefact.

🔴 Farmers fetch only THEIR OWN fields' advisories — a few KB (§29.6). The full district
GeoJSON is for the officer console. This module produces that small payload: one entry per
field, sorted worst-first (§21.1), each carrying its band, the numbers behind it, and the
four-part advisory in every configured language.

Pure dict assembly — no I/O, no clock. nightly.py writes the result.
"""
from __future__ import annotations

from typing import Optional, Sequence

from engine.advisory import build_advisory
from engine.aggregate import CellAssessment
from engine.confidence import compute_field_confidence
from engine.fields import resolve_cell_index, sort_worst_first
from engine.grid import Grid

SCHEMA_VERSION = "2.0.0"


def build_field_payload(
    *,
    grid: Grid,
    assessments: Sequence[CellAssessment],
    fields_cfg: Sequence[dict],
    templates: dict,
    cell_step_deg: float,
    min_wet_hours: int,
    run_id: str,
    district_code: str,
    model_id: str,
    model_version: str,
    engine_git_sha: str,
    data_status: str,
    degradation: Sequence[str],
    spray_windows: Optional[dict] = None,
    confidences: Optional[Sequence[float]] = None,
) -> dict:
    """One entry per field in `fields_cfg` belonging to `district_code`.

    A field that resolves to no cell is reported with band 'unknown' and no advisory rather
    than being silently dropped or snapped to a neighbouring cell — the farmer must not be
    shown a risk computed for someone else's land.
    """
    spray_windows = spray_windows or {}
    langs = list(templates.keys())
    entries: list[dict] = []

    for f in fields_cfg:
        if f.get("district") != district_code:
            continue
        idx = resolve_cell_index(grid, f["center"]["lat"], f["center"]["lon"], cell_step_deg)
        if idx is None:
            entries.append({
                "id": f["id"], "name_hi": f["name_hi"], "name_en": f["name_en"],
                "crop": f["crop"], "area_local": f.get("area_local"),
                "center": f["center"], "cell_id": None,
                "band": "unknown", "risk": 0.0,
                "note": "outside_district_grid",
            })
            continue

        a = assessments[idx]
        cell = grid.cells[idx]
        window = spray_windows.get(f["id"])

        advisory = {}
        for lang in langs:
            # The spoken sentence uses the inflected name where config provides one; the card
            # label keeps the plain form. Two surfaces, two forms of the same farmer's words.
            spoken_name = f.get(f"name_{lang}_spoken") or f.get(f"name_{lang}") or f["name_en"]
            advisory[lang] = build_advisory(
                lang=lang, templates=templates,
                field_name=spoken_name, crop=f["crop"], band=a.band,
                criterion_met=a.criterion_met, dsv_accum=a.dsv_accum,
                wet_hours=a.wet_hours, mean_wet_temp_c=a.mean_wet_temp_c,
                min_wet_hours=min_wet_hours,
                spray_window=(window["text"].get(lang) if window else None),
            )

        entry = {
            "id": f["id"],
            "name_hi": f["name_hi"],
            "name_en": f["name_en"],
            "crop": f["crop"],
            "area_local": f.get("area_local"),
            "center": f["center"],
            "cell_id": cell.cell_id,
            "band": a.band,
            "risk": round(a.risk, 2),
            "physics_risk": round(a.physics_risk, 2),
            "ml_delta": round(a.ml_delta, 2),
            "criterion_met": a.criterion_met,
            "dsv_today": a.dsv_today,
            "dsv_accum_7d": a.dsv_accum,
            "wet_hours": a.wet_hours,
            "min_temp_c": round(a.min_temp_c, 2),
            "mean_wet_temp_c": round(a.mean_wet_temp_c, 2),  # 🔴 exposed: reveals silent-bug 2
            "firing_model": a.firing_model,
            "firing_pathogen": a.firing_pathogen,
            "advisory": advisory,
        }
        # Field confidence is the MIN of its intersecting cells (§21.5, worst-case). A config field
        # resolves to one cell, so that cell's confidence stands; the helper keeps the invariant
        # explicit for the day a field spans several cells.
        if confidences is not None:
            entry["confidence"] = round(compute_field_confidence([confidences[idx]]), 2)

        # Spray-window fields (§29.5) only when a window exists — an 'act' field with no clean
        # window shows the general `when_act_no_window` phrasing instead, never a fabricated hour.
        if window:
            entry["spray_start_hour"] = window["start_hour"]
            entry["spray_end_hour"] = window["end_hour"]
            entry["spray_quality"] = window["quality"]
            entry["spray_blocked_by"] = window["blocked_by"]
        entries.append(entry)

    entries = sort_worst_first(entries)   # 🔴 worst first: the problem before anything else

    # Distinct clips = union of all segments (field-name clips + shared body clips). §14.8
    # requires this to scale with distinct messages, not with the number of farmers.
    clips: set[str] = set()
    bodies: set[str] = set()
    for e in entries:
        for a in e.get("advisory", {}).values():
            clips.update(a["audio_segments"])
            bodies.add(a["body_audio_key"])
    return {
        "prahari": {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "district": district_code,
            "model": {"id": model_id, "version": model_version, "engine_git_sha": engine_git_sha},
            "data_status": data_status,
            "degradation": list(degradation),
            "languages": langs,
            "field_count": len(entries),
            "distinct_audio_clips": len(clips),        # total clips to pre-generate
            "distinct_body_clips": len(bodies),        # the part that does NOT grow with users
        },
        "fields": entries,
    }


def build_clip_manifest(payload: dict) -> list[dict]:
    """The exact set of audio clips this payload needs, deduplicated by key.

    🔴 This is what makes §14.2's pre-generation law affordable. Keys are content-addressed, so
    two farmers whose fields are in the same situation share one body clip, and a re-run
    synthesises nothing that already exists on disk. The manifest is the contract between the
    advisory text and the TTS adapter — the adapter never re-derives text of its own, which is
    what would let the spoken words drift away from the written ones.

    Returned sorted by key so the output is deterministic and diffable.
    """
    seen: dict[str, dict] = {}
    for e in payload.get("fields", []):
        for lang, a in e.get("advisory", {}).items():
            for key, text in ((a["name_audio_key"], a["which"]), (a["body_audio_key"], a["body_text"])):
                if key in seen:
                    # Same key, different text would mean the hash no longer identifies the
                    # content — a silent mismatch between what is written and what is spoken.
                    if seen[key]["text"] != text:
                        raise ValueError(f"clip key collision: {key!r} maps to two different texts")
                    continue
                seen[key] = {"key": key, "lang": lang, "text": text}
    return [seen[k] for k in sorted(seen)]
