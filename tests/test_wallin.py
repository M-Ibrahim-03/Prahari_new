"""Tests for the Wallin (1962) DSV table lookup. Pure — no I/O.

The published table is the model's severity core, so these tests pin its exact values as well
as the boundary behaviour that the published table leaves implicit.
"""
import pytest

from engine.wallin import DEFAULT_DSV_TABLE, wallin_dsv


# ── published values, band by band ────────────────────────────────────────────
# DSV is the value of the highest hour-breakpoint the wet spell REACHES, so a spell one hour
# short of a break keeps the lower value. These are the numbers a reviewer can check against
# the publication; if a refactor changes any of them it is a change to the model, not a tidy-up.

@pytest.mark.parametrize("temp,hours,expected", [
    # 7.2-11.6 C: 15h->0, 18h->1, 21h->2, 24h->3   (no DSV 4 in the cold band)
    (9.0, 14, 0), (9.0, 15, 0), (9.0, 18, 1), (9.0, 20, 1),
    (9.0, 21, 2), (9.0, 23, 2), (9.0, 24, 3),
    # 11.7-15.0 C: 12h->0, 15h->1, 18h->2, 21h->3, 24h->4
    (13.0, 11, 0), (13.0, 12, 0), (13.0, 15, 1), (13.0, 17, 1),
    (13.0, 18, 2), (13.0, 21, 3), (13.0, 24, 4),
    # 15.1-26.6 C: 9h->0, 12h->1, 15h->2, 18h->3, 24h->4  (warmest band accrues fastest)
    (20.0, 8, 0), (20.0, 9, 0), (20.0, 12, 1), (20.0, 15, 2),
    (20.0, 18, 3), (20.0, 23, 3), (20.0, 24, 4),
])
def test_published_table_values(temp, hours, expected):
    assert wallin_dsv(temp, hours) == expected


def test_outside_development_range_is_zero():
    """Below 7.2 C or above 26.6 C the pathogen does not develop, however wet the leaves are.

    The upper bound is what makes an Indian monsoon run report safe: 24 h of 96 % RH at 28 C is
    genuinely no infection pressure for late blight, and reporting otherwise would alarm a
    farmer about a disease their crop cannot get.
    """
    assert wallin_dsv(7.1, 24) == 0
    assert wallin_dsv(26.7, 24) == 0
    assert wallin_dsv(28.0, 24) == 0
    assert wallin_dsv(-5.0, 24) == 0
    # ...but exactly on the published bounds it does develop.
    assert wallin_dsv(7.2, 24) == 3
    assert wallin_dsv(26.6, 24) == 4


def test_zero_wet_hours_is_zero_at_every_temperature():
    for t in (8.0, 13.0, 20.0, 26.0):
        assert wallin_dsv(t, 0) == 0


# ── regression: the gap between bands ─────────────────────────────────────────

@pytest.mark.parametrize("temp", [11.61, 11.65, 11.69, 15.01, 15.05, 15.09])
def test_temperature_between_bands_is_not_silently_zero(temp):
    """🔴 REGRESSION. The published bands are 7.2-11.6, 11.7-15.0, 15.1-26.6. Matching each as a
    closed interval left dead zones at 11.61-11.69 and 15.01-15.09 where no band applied and the
    lookup fell through to "no infection pressure".

    This was found in a demo scenario: a cell with a 24 h wet spell at 15.05 C — the most
    blight-favourable cell in the district — was reported safe. Interpolated temperatures are
    continuous, so the live pipeline hits these zones too. A false negative in the middle of the
    pathogen's ideal range is the worst failure this model can have.
    """
    assert wallin_dsv(temp, 24) == 4
    assert wallin_dsv(temp, 18) >= 2


def test_between_band_temperature_uses_the_warmer_band():
    """15.05 C is above the 15.0 C top of the middle band, so it belongs to the warmer one.

    At 15 wet hours the two bands disagree (middle -> 1, warm -> 2), which makes this
    observable rather than a distinction without a difference.
    """
    assert wallin_dsv(15.00, 15) == 1     # middle band, published
    assert wallin_dsv(15.05, 15) == 2     # snapped up to the warm band
    assert wallin_dsv(15.10, 15) == 2     # warm band, published
    # Same story at the lower seam: 11.65 is above the cold band's 11.6 top.
    assert wallin_dsv(11.60, 15) == 0     # cold band, published
    assert wallin_dsv(11.65, 15) == 1     # snapped up to the middle band
    assert wallin_dsv(11.70, 15) == 1     # middle band, published


def test_no_temperature_in_range_returns_zero_for_a_full_day_of_wetness():
    """Sweep the whole development range: a 24 h wet spell must never score 0 inside it.

    This is the property the band-gap bug violated, stated independently of where the seams
    happen to be — so moving a band boundary cannot reintroduce the bug undetected.
    """
    t = 7.2
    while t <= 26.6:
        assert wallin_dsv(round(t, 2), 24) > 0, f"{t} C scored 0 with 24 h of leaf wetness"
        t += 0.01


# ── table plumbing ────────────────────────────────────────────────────────────

def test_caller_supplied_table_is_used_not_the_default():
    """The pipeline passes the yaml table in; the default must not shadow it."""
    custom = ({"t_min": 0.0, "t_max": 50.0, "breaks": ((1, 4),)},)
    assert wallin_dsv(40.0, 1, custom) == 4      # outside the default's range entirely
    assert wallin_dsv(40.0, 1) == 0              # default still says no development


def test_bands_given_out_of_order_are_handled():
    reversed_table = tuple(reversed(DEFAULT_DSV_TABLE))
    assert wallin_dsv(20.0, 24, reversed_table) == 4
    assert wallin_dsv(9.0, 24, reversed_table) == 3
    assert wallin_dsv(15.05, 24, reversed_table) == 4


def test_empty_table_is_zero_not_an_error():
    assert wallin_dsv(15.0, 24, ()) == 0


def test_default_table_mirrors_models_yaml():
    """engine/wallin.py keeps a copy of the table so pure tests need no file I/O. A drift between
    the copy and the config the pipeline actually loads would make every test here meaningless.
    """
    import yaml
    from pathlib import Path

    cfg = yaml.safe_load(
        (Path(__file__).resolve().parent.parent / "pipeline" / "config" / "models.yaml")
        .read_text(encoding="utf-8")
    )
    yaml_table = cfg["models"]["potato_late_blight_hutton"]["severity"]["dsv_table"]
    assert len(yaml_table) == len(DEFAULT_DSV_TABLE)
    for got, want in zip(yaml_table, DEFAULT_DSV_TABLE):
        assert got["t_min"] == want["t_min"]
        assert got["t_max"] == want["t_max"]
        assert [tuple(b) for b in got["breaks"]] == [tuple(b) for b in want["breaks"]]
