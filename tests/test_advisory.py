"""Tests for the four-part advisory script (§14.5) and the honest 'too hot' explanation."""
from pathlib import Path

import yaml

from engine.advisory import audio_key, build_advisory, why_reason

TEMPLATES = yaml.safe_load(
    (Path(__file__).resolve().parent.parent / "pipeline" / "config" /
     "advisory_templates.yaml").read_text(encoding="utf-8")
)["languages"]

BASE = dict(
    templates=TEMPLATES, field_name="नहर वाला खेत", crop="potato",
    wet_hours=8, min_wet_hours=6,
)


def test_field_name_comes_first():
    # 🔴 §14.5: "which field" is the most important word in the message.
    a = build_advisory(lang="hi", band="act", criterion_met=True, dsv_accum=19,
                       mean_wet_temp_c=14.0, spray_window="मंगलवार सुबह छह से नौ बजे", **BASE)
    assert a["text"].startswith("आपके नहर वाला खेत में")
    assert a["which"] in a["text"]


def test_all_four_parts_present_and_ordered():
    a = build_advisory(lang="hi", band="act", criterion_met=True, dsv_accum=19,
                       mean_wet_temp_c=14.0, spray_window="मंगलवार सुबह", **BASE)
    text = a["text"]
    # which -> what -> why -> when, in that order.
    assert text.index(a["which"]) < text.index(a["what"]) < text.index(a["why"]) < text.index(a["when"])


def test_act_without_window_does_not_invent_one():
    a = build_advisory(lang="hi", band="act", criterion_met=True, dsv_accum=19,
                       mean_wet_temp_c=14.0, spray_window=None, **BASE)
    assert "{window}" not in a["text"]          # no unrendered placeholder
    assert a["when"] == TEMPLATES["hi"]["when_act_no_window"]


def test_too_hot_is_explained_not_hidden():
    # 🔴 The severity-gated case: criterion met, DSV 0, 27 C -> say why it is still safe.
    reason = why_reason(band="safe", criterion_met=True, dsv_accum=0, wet_hours=18,
                        mean_wet_temp_c=27.3, min_wet_hours=6)
    assert reason == "why_too_hot"
    a = build_advisory(lang="hi", band="safe", criterion_met=True, dsv_accum=0,
                       mean_wet_temp_c=27.3, **{**BASE, "wet_hours": 18})
    assert a["why"] == TEMPLATES["hi"]["why_too_hot"]
    assert a["band_label"] == "सुरक्षित"


def test_too_cold_is_its_own_reason():
    assert why_reason(band="safe", criterion_met=True, dsv_accum=0, wet_hours=18,
                      mean_wet_temp_c=3.0, min_wet_hours=6) == "why_too_cold"


def test_dry_weather_reason():
    assert why_reason(band="safe", criterion_met=False, dsv_accum=0, wet_hours=2,
                      mean_wet_temp_c=15.0, min_wet_hours=6) == "why_dry"


def test_english_renders_without_placeholders():
    a = build_advisory(lang="en", band="watch", criterion_met=True, dsv_accum=13,
                       mean_wet_temp_c=14.0, **{**BASE, "field_name": "Canal field"})
    assert "{" not in a["text"] and "}" not in a["text"]
    assert a["band_label"] == "Watch"


def test_audio_key_is_stable_and_content_addressed():
    # §14.2/§14.8: identical text -> identical key -> zero new TTS calls on night two.
    k1 = audio_key("act", "hi", "एक ही वाक्य")
    k2 = audio_key("act", "hi", "एक ही वाक्य")
    k3 = audio_key("act", "hi", "दूसरा वाक्य")
    assert k1 == k2 and k1 != k3
    assert k1.startswith("act_hi_") and len(k1.split("_")[-1]) == 4


def test_distinct_clip_count_collapses_across_fields():
    # Two fields with the SAME band and SAME conditions must share one audio clip.
    common = dict(lang="hi", band="safe", criterion_met=True, dsv_accum=0,
                  mean_wet_temp_c=27.3, templates=TEMPLATES, crop="potato",
                  wet_hours=18, min_wet_hours=6)
    a = build_advisory(field_name="खेत क", **common)
    b = build_advisory(field_name="खेत क", **common)
    assert a["audio_key"] == b["audio_key"]


def test_body_clip_is_shared_across_different_field_names():
    # 🔴 The economics of §14.2: the BODY clip must NOT depend on the field name, otherwise the
    # distinct-clip count grows with the number of farmers instead of the number of messages.
    common = dict(lang="hi", band="act", criterion_met=True, dsv_accum=19,
                  mean_wet_temp_c=14.0, templates=TEMPLATES, crop="potato",
                  wet_hours=8, min_wet_hours=6, spray_window="मंगलवार सुबह")
    a = build_advisory(field_name="नहर वाले खेत", **common)
    b = build_advisory(field_name="बड़े खेत", **common)
    assert a["body_audio_key"] == b["body_audio_key"]     # shared body
    assert a["name_audio_key"] != b["name_audio_key"]     # distinct names
    assert a["audio_key"] != b["audio_key"]               # whole-message keys differ, as expected

    # 100 farmers, 100 distinct field names, one situation -> 101 clips, not 200.
    names = [f"खेत {i}" for i in range(100)]
    segs = set()
    for n in names:
        segs.update(build_advisory(field_name=n, **common)["audio_segments"])
    assert len(segs) == 101


def test_name_segment_is_spoken_first():
    a = build_advisory(lang="hi", band="act", criterion_met=True, dsv_accum=19,
                       mean_wet_temp_c=14.0, spray_window="मंगलवार सुबह", **BASE)
    # Playback order must still deliver the field name first (§14.5).
    assert a["audio_segments"] == [a["name_audio_key"], a["body_audio_key"]]
    assert a["body_text"] == " ".join([a["what"], a["why"], a["when"]])
    assert a["which"] not in a["body_text"]
