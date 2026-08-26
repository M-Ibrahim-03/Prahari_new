"""Advisory text generation — the four-part script of PRD §14.5. Pure.

    1. WHICH FIELD   "आपके नहर वाले खेत में..."     ← 🔴 always first
    2. WHAT          "...आलू की झुलसा बीमारी का खतरा है।"
    3. WHY (brief)   "पिछली दो रातें आठ घंटे नमी रही।"
    4. WHEN TO ACT   "मंगलवार सुबह छह से नौ बजे छिड़कें।"

🔴 The field name comes first, always. For a farmer with three parcels, "which field" is the
most important word in the message (§14.5).

Templates live in pipeline/config/advisory_templates.yaml and are passed IN — adding a language
is a config edit, never a code change. audio_key is a content hash so the nightly job generates
each distinct clip exactly once (§14.2 pre-generation law), independent of user count.
"""
from __future__ import annotations

import hashlib
from typing import Optional

# Wallin's overall development range: outside it the pathogen does not progress, which is why a
# criterion-met-but-DSV-0 cell is honestly "safe" rather than a false alarm (see §37).
DEFAULT_VIABLE_TEMP_C = (7.2, 26.6)


def why_reason(
    *,
    band: str,
    criterion_met: bool,
    dsv_accum: int,
    wet_hours: int,
    mean_wet_temp_c: float,
    min_wet_hours: int,
    viable_temp_c: tuple[float, float] = DEFAULT_VIABLE_TEMP_C,
) -> str:
    """Pick the explanation key that is actually true for this cell.

    🔴 The 'too hot' / 'too cold' cases exist because the Hutton criterion can be met while
    Wallin severity stays 0 — humid enough, but outside the pathogen's viable temperature.
    Saying so plainly is what keeps a safe-but-humid day from reading as a hidden risk.
    """
    lo, hi = viable_temp_c
    if criterion_met and dsv_accum == 0:
        if mean_wet_temp_c > hi:
            return "why_too_hot"
        if mean_wet_temp_c < lo:
            return "why_too_cold"
    if band == "safe" and wet_hours < min_wet_hours:
        return "why_dry"
    if wet_hours >= min_wet_hours:
        return "why_wet"
    return "why_dry"


def audio_key(band: str, lang: str, text: str) -> str:
    """Content-addressed clip id, e.g. 'act_hi_7f3a'. Identical text -> identical key, so an
    unchanged advisory triggers zero new TTS work on the second night (§14.8)."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:4]
    return f"{band}_{lang}_{digest}"


def name_audio_key(lang: str, name: str) -> str:
    """Clip id for a field-name segment, e.g. 'name_hi_2b91'.

    🔴 Why audio is segmented into NAME + BODY: §14.5 requires the field name to be spoken
    first, but §14.2 requires the number of distinct clips to scale with messages, not users.
    Those two rules collide if the name is baked into one monolithic clip — 50,000 farmers
    would need 50,000 clips. Splitting them restores the economics: distinct clips become
    (distinct field names) + (bands x languages x windows), and field names repeat heavily
    in practice. Playback concatenates the two segments, so the farmer still hears their
    field name first.
    """
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:4]
    return f"name_{lang}_{digest}"


def build_advisory(
    *,
    lang: str,
    templates: dict,
    field_name: str,
    crop: str,
    band: str,
    criterion_met: bool,
    dsv_accum: int,
    wet_hours: int,
    mean_wet_temp_c: float,
    min_wet_hours: int,
    spray_window: Optional[str] = None,
    viable_temp_c: tuple[float, float] = DEFAULT_VIABLE_TEMP_C,
) -> dict:
    """Render the four-part advisory for one field in one language.

    `templates` is the per-language block from advisory_templates.yaml. `spray_window` is a
    prerendered human phrase; when absent we give honest general timing instead of inventing
    a window we have not computed.
    """
    t = templates[lang]
    crop_word = t["crops"].get(crop, crop)
    disease_word = t["disease"]

    which = t["which"].format(field=field_name)
    what = t[f"what_{band}"].format(crop=crop_word, disease=disease_word)
    why = t[why_reason(
        band=band, criterion_met=criterion_met, dsv_accum=dsv_accum, wet_hours=wet_hours,
        mean_wet_temp_c=mean_wet_temp_c, min_wet_hours=min_wet_hours, viable_temp_c=viable_temp_c,
    )].format(wet_hours=wet_hours)

    if band == "act":
        when = (t["when_act"].format(window=spray_window) if spray_window
                else t["when_act_no_window"])
    else:
        when = t[f"when_{band}"]

    text = " ".join(part.strip() for part in (which, what, why, when) if part.strip())
    # BODY is everything except the field name — shared across every field in the same
    # situation, which is what keeps the distinct-clip count independent of user count.
    body_text = " ".join(part.strip() for part in (what, why, when) if part.strip())
    n_key = name_audio_key(lang, which)
    b_key = audio_key(band, lang, body_text)
    return {
        "lang": lang,
        "which": which,
        "what": what,
        "why": why,
        "when": when,
        "text": text,
        "body_text": body_text,
        "action": t[f"action_{band}"],
        "band_label": t[f"band_{band}"],
        "audio_key": audio_key(band, lang, text),   # whole-message key (single-clip path)
        "name_audio_key": n_key,
        "body_audio_key": b_key,
        "audio_segments": [n_key, b_key],            # play in order: field name, then advice
    }
