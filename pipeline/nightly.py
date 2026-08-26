"""Nightly orchestrator — IMPURE conductor. Live weather -> pure engine -> artefact + ledger.

Pipeline (PRD §28.2): load config -> build grid -> fetch node weather (keyless Open-Meteo)
-> downscale to cells (interpolate T & dew point, then RECOMPUTE RH via Magnus, §8.3)
-> daily stats + assess (pure engine) -> write §29.5 artefact -> chain 'act' cells into the ledger.

Run:  python -m pipeline.nightly
"""
from __future__ import annotations

import hashlib
import gzip
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from adapters.scenario import ScenarioProvider, spec_from_config
from adapters.weather import DEFAULT_VARIABLES, OpenMeteoProvider, align_from_date
from engine.aggregate import assess_cell, daily_stats
from engine.grid import build_grid
from engine.interpolate import rh_from_temp_and_dewpoint
from pipeline.artefact import build_feature_collection
from adapters.tts import synthesise_manifest
from pipeline.fields import build_clip_manifest, build_field_payload
from pipeline.ledger import append_entry, verify_chain

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "pipeline" / "config"
ARTEFACT_DIR = ROOT / "artefacts"
LEDGER_PATH = ARTEFACT_DIR / "ledger.jsonl"
IST = timezone(timedelta(hours=5, minutes=30))
PAYLOAD_BUDGET_BYTES = 150_000


def now_ist() -> tuple[str, str]:
    """(run_id ISO with +05:30, today's YYYY-MM-DD in IST). The only clock in the run."""
    now = datetime.now(IST)
    return now.isoformat(timespec="seconds"), now.strftime("%Y-%m-%d")


def engine_source_sha() -> str:
    """Short integrity anchor for the engine. Prefer git; fall back to hashing engine/*.py."""
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL
        )
        return sha.decode().strip()
    except Exception:
        h = hashlib.sha256()
        for p in sorted((ROOT / "engine").rglob("*.py")):
            h.update(p.read_bytes())
        return h.hexdigest()[:7]


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def interpolate_cells(grid, node_series, today_date):
    """Downscale node hourly series to per-cell (times, temp, rh, precip).

    🔴 RH is recomputed from interpolated T and dew point via Magnus — never interpolated
    or lapse-corrected directly (§8.3). Elevation lapse is a no-op here (flat Ganga plain);
    the elevation adapter wires in later without changing this contract.
    """
    aligned = [align_from_date(s, today_date) for s in node_series]
    n_hours = min(len(s.times) for s in aligned)
    times = list(aligned[0].times[:n_hours])

    temp_by_node = [s.variables["temperature_2m"] for s in aligned]
    dew_by_node = [s.variables["dew_point_2m"] for s in aligned]
    precip_by_node = [s.variables["precipitation"] for s in aligned]

    per_cell = []
    for cell in grid.cells:
        idx, w = cell.node_idx, cell.weights
        c_times, c_temp, c_rh, c_precip = [], [], [], []
        for h in range(n_hours):
            t_corners = [temp_by_node[n][h] for n in idx]
            d_corners = [dew_by_node[n][h] for n in idx]
            if any(v is None for v in t_corners) or any(v is None for v in d_corners):
                continue  # skip hours with missing corner data rather than fabricate
            t_cell = sum(tv * wv for tv, wv in zip(t_corners, w))
            d_cell = sum(dv * wv for dv, wv in zip(d_corners, w))
            p_corners = [precip_by_node[n][h] or 0.0 for n in idx]
            c_times.append(times[h])
            c_temp.append(t_cell)
            c_rh.append(rh_from_temp_and_dewpoint(t_cell, d_cell))  # 🔴 recompute, don't carry
            c_precip.append(sum(pv * wv for pv, wv in zip(p_corners, w)))
        per_cell.append((c_times, c_temp, c_rh, c_precip))
    return per_cell


def run_district(dist: dict, model: dict, run_id: str, today_date: str, engine_sha: str,
                 fields_cfg=None, templates=None, with_audio: bool = False,
                 scenario=None) -> dict:
    params = model["params"]
    severity = model["severity"]
    dsv_table = severity["dsv_table"]

    grid = build_grid(
        district=dist["code"],
        center_lat=dist["center"]["lat"],
        center_lon=dist["center"]["lon"],
        half_span_deg=dist["half_span_deg"],
        node_step_deg=dist["node_step_deg"],
        cell_step_deg=dist["cell_step_deg"],
        id_prefix=dist["id_prefix"],
    )
    print(f"  grid: {len(grid.nodes)} nodes, {len(grid.cells)} cells")

    node_coords = list(grid.nodes)  # (lat, lon), node-index order

    if scenario is None:
        provider = OpenMeteoProvider()
        node_series = provider.fetch(node_coords, DEFAULT_VARIABLES, forecast_days=8, past_days=2)
        data_status, degradation = "fresh", []
        # Real run: "today" is today.
        window_date = today_date
        out_code = dist["code"]
    else:
        # 🔴 Synthetic INPUTS, real engine. The band below is computed by Hutton and Wallin from
        # this weather — nothing here writes a result. Marked as a scenario in the artefact and
        # written to its own district code so a forecast is never overwritten.
        provider = ScenarioProvider(scenario, (dist["center"]["lat"], dist["center"]["lon"]))
        node_series = provider.fetch(node_coords)
        data_status = "scenario"
        degradation = [f"scenario:{scenario.name} — synthetic weather, not a forecast"]
        # Evaluate inside the scenario's own dates, not today's; the series does not contain today.
        window_date = _scenario_window_date(scenario)
        out_code = f"{dist['code']}_{scenario.name}"
        print(f"  scenario: {scenario.name}  window={window_date}  ({scenario.days} days synthetic)")

    print(f"  fetched {len(node_series)} node series, {len(node_series[0].times)} hours each")

    per_cell = interpolate_cells(grid, node_series, window_date)

    assessments = []
    for (c_times, c_temp, c_rh, c_precip) in per_cell:
        days = daily_stats(c_times, c_temp, c_rh, c_precip, params, dsv_table)
        assessments.append(assess_cell(days, params, severity))

    fc = build_feature_collection(
        grid=grid,
        assessments=assessments,
        cell_step_deg=dist["cell_step_deg"],
        run_id=run_id,
        district_code=dist["code"],
        horizon="today",
        model_id=model["_id"],
        model_version=model["version"],
        engine_git_sha=engine_sha,
        data_status=data_status,
        degradation=degradation,
    )

    out_dir = ARTEFACT_DIR / out_code
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "today.geojson"
    payload = json.dumps(fc, separators=(",", ":"), ensure_ascii=False)
    out_path.write_text(payload, encoding="utf-8")

    raw = payload.encode("utf-8")
    gz = len(gzip.compress(raw, 9))  # transport is compressed; this is what farmers download
    counts = fc["prahari"]["counts"]
    flag = "OK" if len(raw) <= PAYLOAD_BUDGET_BYTES else "over pre-compression target"
    print(f"  artefact: {out_path.relative_to(ROOT)}  raw={len(raw)/1024:.1f} KB "
          f"gzip={gz/1024:.1f} KB [{flag}; brotli+dissolve shrink further]")
    print(f"  bands: safe={counts['safe']} watch={counts['watch']} act={counts['act']}")

    # ── Farmer-facing field payload (a few KB — §29.6) ────────────────────────
    if fields_cfg and templates:
        fp = build_field_payload(
            grid=grid, assessments=assessments, fields_cfg=fields_cfg, templates=templates,
            cell_step_deg=dist["cell_step_deg"], min_wet_hours=params["min_wet_hours"],
            run_id=run_id, district_code=dist["code"], model_id=model["_id"],
            model_version=model["version"], engine_git_sha=engine_sha,
            data_status=data_status, degradation=degradation,
        )
        f_path = out_dir / "fields.json"
        f_payload = json.dumps(fp, separators=(",", ":"), ensure_ascii=False)
        f_path.write_text(f_payload, encoding="utf-8")
        meta = fp["prahari"]
        print(f"  fields:   {f_path.relative_to(ROOT)}  "
              f"{len(f_payload.encode('utf-8'))/1024:.1f} KB  "
              f"{meta['field_count']} fields, {meta['distinct_audio_clips']} distinct clips")
        for e in fp["fields"]:
            print(f"            [{e['band']:>5}] {e['name_hi']}  ({e.get('cell_id')})")

        # ── Pre-generated advisory audio (§14.2) ──────────────────────────────
        # Skipped by default so `python -m pipeline.nightly` stays fast and offline-friendly;
        # the nightly workflow passes --audio. Clips are content-addressed, so re-runs
        # synthesise only genuinely new messages.
        if with_audio:
            manifest = build_clip_manifest(fp)
            results = synthesise_manifest(manifest, ARTEFACT_DIR / "audio")
            made = [r for r in results if r.path and not r.skipped]
            kept = [r for r in results if r.skipped]
            failed = [r for r in results if r.error]
            total_kb = sum(r.bytes_written for r in results if r.path) / 1024
            print(f"  audio: {len(manifest)} clips needed -> {len(made)} new, "
                  f"{len(kept)} already present, {len(failed)} failed ({total_kb:.1f} KB on disk)")
            for r in failed:
                # Loud, per clip. A missing clip silently falling back to robot speech is
                # exactly the degradation the app is supposed to make visible.
                print(f"         !! {r.key}: {r.error}")

    # Ledger: every 'act' cell is an alert -> one chained entry.
    # 🔴 A scenario keeps its OWN ledger. The ledger is the public accountability record — "we
    # said this, on this date, from these inputs". Chaining synthetic alerts into it would put
    # 145 invented warnings in the same tamper-evident sequence as real ones, and no verifier
    # downstream could tell them apart. Separate files; the hash chain of each stays intact.
    ledger_path = LEDGER_PATH if scenario is None else out_dir / "ledger.jsonl"
    seq_start = verify_chain(ledger_path).get("count", 0)
    n_alerts = 0
    for feat in fc["features"]:
        p = feat["properties"]
        if p["band"] != "act":
            continue
        digest_src = json.dumps(
            {k: p[k] for k in ("dsv_accum_7d", "wet_hours", "min_temp_c",
                               "mean_wet_temp_c", "criterion_met")},
            sort_keys=True, separators=(",", ":"))
        append_entry(ledger_path, {
            "seq": seq_start + n_alerts,
            "timestamp": run_id,
            "cell_id": p["cell_id"],
            "model": f"{model['_id']}@{model['version']}",
            "engine_sha": engine_sha,
            "band": "act",
            "inputs_digest": "sha256:" + hashlib.sha256(digest_src.encode()).hexdigest(),
        })
        n_alerts += 1
    print(f"  ledger: +{n_alerts} alert entries -> {ledger_path.relative_to(ROOT)}")
    return {"district": dist["code"], "counts": counts, "size": len(raw), "alerts": n_alerts,
            "ledger_path": ledger_path}


def _scenario_window_date(scenario) -> str:
    """The date a scenario is assessed on.

    Alignment keeps the days at or AFTER this date (the real pipeline aligns from today so that
    today plus the forecast remain and the two `past_days` are dropped). So a scenario aligns from
    its first date, leaving the whole synthetic block in the window — the consecutive-day test and
    the 7-day DSV accumulation both read forward from here. Aligning from the last date would
    leave exactly one day, and the two-consecutive-day criterion could never be satisfied.
    """
    return date.fromisoformat(scenario.start_date).isoformat()


def main() -> None:
    # Windows consoles default to cp1252, which cannot encode Devanagari. A cosmetic log line
    # must never crash the pipeline, so make stdout UTF-8 and lossy rather than fatal.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    run_id, today_date = now_ist()
    engine_sha = engine_source_sha()
    with_audio = "--audio" in sys.argv

    # --scenario NAME runs the engine on synthetic weather from scenarios.yaml instead of the
    # live forecast. Writes to its own district code; the real forecast is untouched.
    scenario = None
    if "--scenario" in sys.argv:
        i = sys.argv.index("--scenario")
        if i + 1 >= len(sys.argv):
            raise SystemExit("--scenario needs a name from pipeline/config/scenarios.yaml")
        name = sys.argv[i + 1]
        all_scenarios = load_yaml(CONFIG_DIR / "scenarios.yaml")["scenarios"]
        if name not in all_scenarios:
            raise SystemExit(f"unknown scenario {name!r}; available: {', '.join(sorted(all_scenarios))}")
        scenario = spec_from_config(name, all_scenarios[name])

    print(f"PRAHARI nightly  run_id={run_id}  engine_sha={engine_sha}"
          f"{'  audio=on' if with_audio else ''}"
          f"{f'  SCENARIO={scenario.name} (synthetic weather)' if scenario else ''}")

    districts_cfg = load_yaml(CONFIG_DIR / "districts.yaml")
    models_cfg = load_yaml(CONFIG_DIR / "models.yaml")["models"]
    fields_cfg = load_yaml(CONFIG_DIR / "fields.yaml")["fields"]
    templates = load_yaml(CONFIG_DIR / "advisory_templates.yaml")["languages"]

    ledgers: list[Path] = []
    for dist in districts_cfg["districts"]:
        if not dist.get("active"):
            continue
        model = dict(models_cfg[dist["model"]])
        model["_id"] = dist["model"]
        print(f"\ndistrict: {dist['code']} ({dist['name']}, {dist['state']})")
        res = run_district(dist, model, run_id, today_date, engine_sha, fields_cfg, templates,
                           with_audio, scenario)
        if res["ledger_path"] not in ledgers:
            ledgers.append(res["ledger_path"])

    for p in ledgers:
        print(f"\nledger chain verify [{p.relative_to(ROOT)}]: {verify_chain(p)}")


if __name__ == "__main__":
    main()
