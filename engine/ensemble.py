"""Multi-NWP ensemble agreement scoring. Pure.

Computes agreement across numerical weather prediction models (ECMWF, GFS, ICON)
without doing network I/O.
"""
from __future__ import annotations

from typing import Sequence


def compute_nwp_agreement(
    forecast_series: Sequence[Sequence[float]],
    threshold_std: float = 2.0,
) -> float:
    """Compute agreement ratio [0.0, 1.0] across multiple model forecast series.

    For each timestamp, calculates the standard deviation across models.
    Higher divergence -> lower agreement.
    """
    if not forecast_series or len(forecast_series) <= 1:
        # Single model available -> baseline default 0.85 (L6 degradation)
        return 0.85

    series_len = min(len(s) for s in forecast_series)
    if series_len == 0:
        return 0.85

    deviations = []
    num_models = len(forecast_series)

    for t in range(series_len):
        values = [forecast_series[m][t] for m in range(num_models)]
        mean_val = sum(values) / num_models
        variance = sum((v - mean_val) ** 2 for v in values) / num_models
        std = variance ** 0.5
        deviations.append(std)

    avg_std = sum(deviations) / len(deviations)
    agreement = max(0.2, 1.0 - (avg_std / threshold_std) * 0.5)
    return round(min(1.0, agreement), 2)
