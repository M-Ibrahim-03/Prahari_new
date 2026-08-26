"""🔴 The four silent-bug tests (PRD §8.6). These exist BEFORE the rules they test and
must never be deleted. Each one pins down a mistake that would otherwise pass review
silently and corrupt every downstream advisory.
"""
from engine.rules import criterion_met, hours_rh_at_or_above, longest_wet_spell_hours
from engine.wallin import wallin_dsv


def test_boundary_is_inclusive():
    # RH of exactly 90.0 is a wet hour; 89.9 is not.
    assert hours_rh_at_or_above([90.0, 90.0, 89.9]) == 2


def test_wallin_uses_spell_mean_not_daily_mean():
    # Same wet_hours, different wet-spell mean temperature -> different DSV.
    assert wallin_dsv(mean_wet_temp=20.0, wet_hours=12) == 1
    assert wallin_dsv(mean_wet_temp=11.0, wet_hours=12) == 0


def test_fragmented_spells_do_not_combine():
    rh = [95] * 4 + [70] * 4 + [95] * 4 + [70] * 12
    assert longest_wet_spell_hours(rh, 90.0) == 4


def test_consecutive_not_total():
    assert criterion_met([True, False, True]) is False   # 🔴 THE test
    assert criterion_met([True, True, False]) is True
