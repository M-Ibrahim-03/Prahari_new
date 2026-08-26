"""ERA5 Historical Reanalysis Replay Adapter (PRD §35 / PRD Phase 6).

Fetches historical ERA5 reanalysis data from Open-Meteo Archive API (keyless, ₹0)
to replay historical seasons through the unmodified physics engine.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Sequence


class HindcastAdapter:
    """Replays ERA5 historical weather for validation without fabricating ground truth."""

    def __init__(self, base_url: str = "https://archive-api.open-meteo.com/v1/archive"):
        self.base_url = base_url

    def fetch_historical_series(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
    ) -> dict[str, list]:
        """Fetch hourly temperature_2m, relative_humidity_2m, precipitation for a point."""
        url = (
            f"{self.base_url}?latitude={lat:.4f}&longitude={lon:.4f}"
            f"&start_date={start_date}&end_date={end_date}"
            f"&hourly=temperature_2m,relative_humidity_2m,precipitation"
            f"&timezone=Asia%2FKolkata"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "PRAHARI-Hindcast/1.0"})
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        hourly = data.get("hourly", {})
        return {
            "time": hourly.get("time", []),
            "temperature": hourly.get("temperature_2m", []),
            "relative_humidity": hourly.get("relative_humidity_2m", []),
            "precipitation": hourly.get("precipitation", []),
        }


def compute_contingency_metrics(
    predictions: Sequence[bool],
    observations: Sequence[bool],
) -> dict[str, float]:
    """Compute standard 2x2 contingency table metrics.

    TP: Risk predicted & observed
    FP: Risk predicted & NOT observed (false alarm)
    FN: Risk NOT predicted & observed (missed outbreak - catastrophic)
    TN: Risk NOT predicted & NOT observed
    """
    tp = sum(1 for p, o in zip(predictions, observations) if p and o)
    fp = sum(1 for p, o in zip(predictions, observations) if p and not o)
    fn = sum(1 for p, o in zip(predictions, observations) if not p and o)
    tn = sum(1 for p, o in zip(predictions, observations) if not p and not o)

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 1.0
    far = fp / (tp + fp) if (tp + fp) > 0 else 0.0
    csi = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "sensitivity": round(sensitivity, 3),
        "specificity": round(specificity, 3),
        "false_alarm_ratio": round(far, 3),
        "critical_success_index": round(csi, 3),
    }
