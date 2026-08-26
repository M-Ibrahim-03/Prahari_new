"""Bounded ML Residual Correction (§26.5 / PRD Phase 6).

Learns systematic local microclimate bias between NWP downscaling and high-resolution observations.
🔴 Hard Invariants:
1. Hard cap: delta is strictly bounded to [-0.25, +0.25].
2. Band-flip rule: delta may NEVER move a cell from 'safe' directly to 'act' on its own.
   Only physics-driven criteria can cross into 'act'.
3. Graceful degradation: if model unavailable or confidence is low, delta = 0.0 (L2 degradation).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

DELTA_MAX = 0.25
DELTA_MIN = -0.25


@dataclass(frozen=True)
class MLCorrectionResult:
    delta: float
    corrected_risk: float
    is_clamped: bool
    degradation: Optional[str] = None


def clamp_delta(raw_delta: float) -> float:
    """Strictly cap delta to [-0.25, +0.25] (PRD §26.5 invariant)."""
    return max(DELTA_MIN, min(DELTA_MAX, raw_delta))


def apply_residual_correction(
    physics_risk: float,
    raw_delta: float,
    physics_band: str,
) -> MLCorrectionResult:
    """Apply bounded residual correction adhering to all safety rules."""
    delta = clamp_delta(raw_delta)
    is_clamped = (raw_delta != delta)

    raw_corrected = physics_risk + delta
    corrected_risk = max(0.0, min(1.0, raw_corrected))

    # Band-flip safety invariant:
    # If physics classified as 'safe' (physics_risk < 0.50), ML delta cannot push it to 'act' (>= 0.80)
    if physics_band == "safe" and corrected_risk >= 0.80:
        corrected_risk = 0.79 # Keep in watch or lower, never flip safe -> act purely via ML

    return MLCorrectionResult(
        delta=round(delta, 3),
        corrected_risk=round(corrected_risk, 3),
        is_clamped=is_clamped,
        degradation=None if delta != 0.0 else "no_ml",
    )
