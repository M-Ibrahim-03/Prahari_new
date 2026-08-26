"""Agro-meteorological rules: RH wet-hours, wet spells, and the Hutton consecutive-day
criterion. Pure — see engine/__init__.py and tests/test_purity.py.

References: Hutton criteria (2 consecutive days: Tmin >= 10 C and >= 6 h RH >= 90%);
Smith (1956); BLITECAST (Krause et al. 1975). Model params live in pipeline/config/models.yaml.
"""
from __future__ import annotations

from typing import Sequence


def hours_rh_at_or_above(rh_hourly: Sequence[float], threshold: float = 90.0) -> int:
    """Count hours whose RH is at or above ``threshold``.

    🔴 The boundary is INCLUSIVE (``>=``). RH of exactly 90.0 counts as a wet hour.
    Getting this wrong (using ``>``) is silent bug 1 (PRD §8.6).
    """
    return sum(1 for rh in rh_hourly if rh >= threshold)


def longest_wet_spell_hours(rh_hourly: Sequence[float], threshold: float = 90.0) -> int:
    """Longest run of CONSECUTIVE hours at/above ``threshold``.

    🔴 Fragmented wet hours do not combine: four separate wet hours are not one
    four-hour spell only if they are contiguous. Two blocks of 4 give a spell of 4,
    never 8 (silent bug 3, PRD §8.6).
    """
    longest = 0
    current = 0
    for rh in rh_hourly:
        if rh >= threshold:
            current += 1
            if current > longest:
                longest = current
        else:
            current = 0
    return longest


def criterion_met(daily_qualified: Sequence[bool], consecutive_days: int = 2) -> bool:
    """True when ``consecutive_days`` qualifying days occur CONSECUTIVELY.

    🔴 THE test (silent bug 4, PRD §8.6): ``[True, False, True]`` is False — two
    qualifying days in total but never back-to-back. ``[True, True, False]`` is True.
    Hutton requires consecutive qualifying days, not a running total.
    """
    run = 0
    for qualified in daily_qualified:
        if qualified:
            run += 1
            if run >= consecutive_days:
                return True
        else:
            run = 0
    return False
