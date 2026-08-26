"""Confidence assessment: node agreement, data completeness, and model agreement. Pure.

🔴 Field confidence is the MINIMUM of the cell confidences it intersects (worst-case),
never the arithmetic mean (PRD §21.5 / §28.3).
"""
from __future__ import annotations

from typing import Sequence


def compute_cell_confidence(
    *,
    node_variances: Sequence[float],
    data_completeness: float = 1.0,
    model_agreement: float = 1.0,
) -> float:
    """Calculate confidence in [0.0, 1.0] for a single cell.

    Factors:
      - data_completeness: proportion of required hourly fields present (1.0 = full 240h).
      - node_variances: variance across the 4 bounding nodes (higher variance -> lower spatial confidence).
      - model_agreement: agreement ratio across NWP ensemble models (1.0 = identical).
    """
    completeness_score = max(0.0, min(1.0, data_completeness))

    # Average node variance penalty (e.g. rapid spatial gradient)
    avg_var = sum(node_variances) / len(node_variances) if node_variances else 0.0
    spatial_score = max(0.4, 1.0 - min(0.6, avg_var * 0.1))

    agreement_score = max(0.0, min(1.0, model_agreement))

    # Combined confidence: weighted multiplication
    confidence = completeness_score * spatial_score * agreement_score
    return round(max(0.1, min(1.0, confidence)), 2)


def compute_field_confidence(cell_confidences: Sequence[float]) -> float:
    """Field confidence is the MIN of its constituent cells (worst-case invariant)."""
    if not cell_confidences:
        return 0.5
    return min(cell_confidences)


def confidence_label(confidence: float, lang: str = "hi") -> str:
    """Categorical label for UI presentation."""
    if confidence >= 0.85:
        return "उच्च" if lang == "hi" else "High"
    if confidence >= 0.65:
        return "मध्यम" if lang == "hi" else "Moderate"
    return "कम" if lang == "hi" else "Low"
