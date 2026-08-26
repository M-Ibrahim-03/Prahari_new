"""Render an engine spray-window (indices into the forecast) into a farmer's sentence.

Lives in the pipeline, not the engine: it reads a weekday off the ISO date string, which is a
calendar fact, not a wall-clock read — but it belongs with the impure conductor rather than the
pure engine all the same. The words (weekday names, part-of-day, numerals) come from
advisory_templates.yaml, so a new language needs no code here (§14.5).
"""
from __future__ import annotations

from datetime import date
from typing import Sequence


def render_window_phrase(
    times: Sequence[str],
    start_idx: int,
    end_idx: int,
    phrase_cfg: dict,
) -> str:
    """`times` are the cell's hourly ISO stamps; [start_idx, end_idx) is the window (end exclusive).

    A daylight window never crosses midnight (night breaks it), so the weekday of the first hour
    labels the whole window. Clock end is the last sprayable hour + 1 (a window over 06:00 and
    07:00 reads "6–8": you may spray from 6 up to 8).
    """
    start_iso = times[start_idx]
    day = phrase_cfg["weekdays"][date.fromisoformat(start_iso[:10]).weekday()]
    start_h = int(start_iso[11:13])
    end_h = int(times[end_idx - 1][11:13]) + 1

    parts = phrase_cfg["parts"]
    part = parts["morning"] if start_h < 12 else parts["midday"] if start_h < 17 else parts["evening"]

    digits = phrase_cfg["digits"]
    to_local = lambda n: "".join(digits[int(c)] for c in str(n))

    return phrase_cfg["template"].format(
        day=day, part=part, start=to_local(start_h), end=to_local(end_h)
    )
