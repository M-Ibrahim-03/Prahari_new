"""Indices 2 and 4 — the I/O shims that feed engine/water.py and engine/market.py.

🔴 This module is an ADAPTER, not engine: it reads YAML and reaches into the weather series, so it
must never contain scoring logic. All arithmetic lives in engine/water.py and engine/market.py,
which stay pure and unit-tested. Keeping the split means tests/test_purity.py can still prove the
engine has no I/O.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import yaml

from engine.market import PricePoint, build_market_signal
from engine.water import WaterBalance, compute_water_balance

CONFIG_DIR = Path(__file__).resolve().parent / "config"


def compute_district_water_balance(node_series: Sequence[Any]) -> dict | None:
    """
    District-mean FAO-56 balance from the weather nodes.

    🔴 Returns None rather than a guess when the fetch did not include ET0. A missing index must be
    ABSENT from the artefact so the UI can omit the card entirely — emitting zeros would render as
    "no water stress", which is a confident wrong answer.
    """
    precip_cols: list[tuple[float, ...]] = []
    et0_cols: list[tuple[float, ...]] = []

    for node in node_series or ():
        variables = getattr(node, "variables", None)
        if not variables:
            continue
        precip = variables.get("precipitation")
        et0 = variables.get("et0_fao_evapotranspiration")
        if not precip or not et0:
            continue
        precip_cols.append(tuple(float(v or 0.0) for v in precip))
        et0_cols.append(tuple(float(v or 0.0) for v in et0))

    if not precip_cols or not et0_cols:
        return None

    # Truncate to the shortest node so a partial series cannot silently pad with zeros.
    n = min(min(len(c) for c in precip_cols), min(len(c) for c in et0_cols))
    if n == 0:
        return None

    nodes = len(precip_cols)
    mean_precip = [sum(c[i] for c in precip_cols) / nodes for i in range(n)]
    mean_et0 = [sum(c[i] for c in et0_cols) / nodes for i in range(n)]

    wb: WaterBalance = compute_water_balance(mean_precip, mean_et0)

    return {
        "band": wb.band,
        "depletion_mm": wb.depletion_mm,
        "raw_mm": wb.raw_mm,
        "taw_mm": wb.taw_mm,
        "stress_coefficient": wb.stress_coefficient,
        "days_until_irrigation": wb.days_until_irrigation,
        "rain_mm": wb.rain_7d_mm,
        "etc_mm": wb.etc_7d_mm,
        "hours_scored": n,
        "resolution": "district_mean",
        "assumptions": list(wb.assumptions),
    }


def load_market_signal(district_code: str) -> dict | None:
    """
    Mandi price momentum + net-realisation ranking from the pinned snapshot.

    🔴 `observed_on` and `is_snapshot` ride on the payload so the UI cannot show a rupee figure
    without also being able to show its date.
    """
    path = CONFIG_DIR / "mandi_prices.yaml"
    if not path.exists():
        return None

    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    block = (cfg.get("districts") or {}).get(district_code)
    if not block:
        return None

    mandis = block.get("mandis") or []
    history = block.get("history") or []
    if not mandis:
        return None

    home = mandis[0].get("name_en", district_code)
    series = [
        PricePoint(date=str(h["date"]), mandi=home, modal_price=float(h["modal_price"]))
        for h in history
        if h.get("modal_price") is not None
    ]
    quotes = [
        (m["name_en"], float(m["modal_price"]), float(m["distance_km"]))
        for m in mandis
        if m.get("modal_price") is not None
    ]

    load_q = float(cfg.get("default_load_quintals", 20.0))
    rate = float(cfg.get("transport_inr_per_km", 18.0))

    signal = build_market_signal(
        series, quotes, load_quintals=load_q, transport_inr_per_km=rate,
        # 🔴 Always stale by construction: this is a pinned snapshot, never today's gate price.
        is_stale=True,
    )

    hi_by_en = {m["name_en"]: m.get("name_hi", m["name_en"]) for m in mandis}

    def opt(o) -> dict:
        return {
            "mandi": o.mandi,
            "mandi_hi": hi_by_en.get(o.mandi, o.mandi),
            "modal_price": o.modal_price,
            "distance_km": o.distance_km,
            "transport_cost_inr": o.transport_cost_inr,
            "net_price_per_quintal": o.net_price_per_quintal,
            "net_realisation_inr": o.net_realisation_inr,
            "gross_premium_inr": o.gross_premium_inr,
        }

    return {
        "momentum": signal.momentum,
        "change_pct": signal.change_pct,
        "latest_price": signal.latest_price,
        "mean_price": signal.mean_price,
        "advice_key": signal.advice_key,
        "best": opt(signal.best) if signal.best else None,
        "alternatives": [opt(a) for a in signal.alternatives],
        "load_quintals": load_q,
        "transport_inr_per_km": rate,
        "commodity": cfg.get("commodity", "potato"),
        "unit": cfg.get("unit", "inr_per_quintal"),
        "observed_on": str(cfg.get("observed_on", "")),
        "source": cfg.get("source", ""),
        "is_snapshot": True,
        "caveats": list(signal.caveats),
    }
