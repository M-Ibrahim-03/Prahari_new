"""Audio pre-generation: the manifest contract and the synthesis adapter.

Fully offline — every test uses SilentSynthesiser. Nothing here touches the network.
"""
from __future__ import annotations

import pytest

from adapters.tts import ClipResult, SilentSynthesiser, prune_unused, synthesise_manifest
from pipeline.fields import build_clip_manifest


def _payload(*advisories: dict) -> dict:
    """Minimal field payload carrying only what build_clip_manifest reads."""
    return {"fields": [{"advisory": {a["lang"]: a for a in advisories}}]}


def _adv(lang: str, name_key: str, which: str, body_key: str, body: str) -> dict:
    return {"lang": lang, "name_audio_key": name_key, "which": which,
            "body_audio_key": body_key, "body_text": body}


def test_manifest_deduplicates_the_shared_body_clip():
    # Two fields, different names, identical situation -> 3 clips, not 4.
    payload = {"fields": [
        {"advisory": {"hi": _adv("hi", "name_hi_aaaa", "आपके नहर वाले खेत में",
                                 "safe_hi_bbbb", "कोई खतरा नहीं है।")}},
        {"advisory": {"hi": _adv("hi", "name_hi_cccc", "आपके बड़े खेत में",
                                 "safe_hi_bbbb", "कोई खतरा नहीं है।")}},
    ]}
    manifest = build_clip_manifest(payload)
    assert len(manifest) == 3
    assert sorted(m["key"] for m in manifest) == ["name_hi_aaaa", "name_hi_cccc", "safe_hi_bbbb"]


def test_manifest_pairs_each_key_with_its_own_text():
    payload = _payload(_adv("hi", "name_hi_aaaa", "आपके खेत में", "safe_hi_bbbb", "कोई खतरा नहीं।"))
    by_key = {m["key"]: m["text"] for m in build_clip_manifest(payload)}
    # 🔴 The name clip must speak the name phrase and the body clip the body — swapping them
    # would still produce a valid-looking manifest but every farmer would hear nonsense.
    assert by_key["name_hi_aaaa"] == "आपके खेत में"
    assert by_key["safe_hi_bbbb"] == "कोई खतरा नहीं।"


def test_manifest_rejects_a_key_that_maps_to_two_texts():
    # A content-addressed key that no longer identifies its content is a silent
    # written-vs-spoken mismatch, so it must fail loudly.
    payload = {"fields": [
        {"advisory": {"hi": _adv("hi", "name_hi_aaaa", "आपके खेत में", "safe_hi_bbbb", "पहला")}},
        {"advisory": {"hi": _adv("hi", "name_hi_aaaa", "आपके खेत में", "safe_hi_bbbb", "दूसरा")}},
    ]}
    with pytest.raises(ValueError, match="collision"):
        build_clip_manifest(payload)


def test_manifest_is_sorted_for_deterministic_output():
    payload = _payload(
        _adv("hi", "name_hi_zzzz", "क", "safe_hi_aaaa", "ख"),
        _adv("en", "name_en_mmmm", "g", "safe_en_bbbb", "h"),
    )
    keys = [m["key"] for m in build_clip_manifest(payload)]
    assert keys == sorted(keys)


def test_synthesis_writes_one_mp3_per_clip(tmp_path):
    manifest = [{"key": "name_hi_aaaa", "lang": "hi", "text": "आपके खेत में"},
                {"key": "safe_hi_bbbb", "lang": "hi", "text": "कोई खतरा नहीं।"}]
    synth = SilentSynthesiser()
    results = synthesise_manifest(manifest, tmp_path, synth=synth)
    assert all(isinstance(r, ClipResult) and r.error is None for r in results)
    assert (tmp_path / "name_hi_aaaa.mp3").read_bytes() == b"ID3-fake-mp3"
    assert (tmp_path / "safe_hi_bbbb.mp3").read_bytes() == b"ID3-fake-mp3"
    assert len(synth.calls) == 2


def test_existing_clips_are_not_resynthesised(tmp_path):
    # 🔴 This is the economics of §14.8: the second nightly run costs almost nothing.
    manifest = [{"key": "safe_hi_bbbb", "lang": "hi", "text": "कोई खतरा नहीं।"}]
    first = SilentSynthesiser()
    synthesise_manifest(manifest, tmp_path, synth=first)
    second = SilentSynthesiser()
    results = synthesise_manifest(manifest, tmp_path, synth=second)
    assert second.calls == []
    assert results[0].skipped is True


def test_force_recuts_every_clip(tmp_path):
    manifest = [{"key": "safe_hi_bbbb", "lang": "hi", "text": "कोई खतरा नहीं।"}]
    synthesise_manifest(manifest, tmp_path, synth=SilentSynthesiser())
    again = SilentSynthesiser(b"ID3-new-voice")
    results = synthesise_manifest(manifest, tmp_path, synth=again, force=True)
    assert len(again.calls) == 1
    assert results[0].skipped is False
    assert (tmp_path / "safe_hi_bbbb.mp3").read_bytes() == b"ID3-new-voice"


def test_a_failing_clip_does_not_abort_the_others(tmp_path):
    class Flaky(SilentSynthesiser):
        def synth(self, text, voice, rate):
            if "bad" in text:
                raise RuntimeError("edge endpoint said no")
            return super().synth(text, voice, rate)

    manifest = [{"key": "k_good1", "lang": "hi", "text": "ठीक"},
                {"key": "k_bad", "lang": "hi", "text": "bad"},
                {"key": "k_good2", "lang": "hi", "text": "ठीक भी"}]
    results = synthesise_manifest(manifest, tmp_path, synth=Flaky())
    by_key = {r.key: r for r in results}
    assert by_key["k_bad"].path is None
    assert "edge endpoint said no" in by_key["k_bad"].error
    # The other two still exist: one dead clip must not cost the district its audio set.
    assert (tmp_path / "k_good1.mp3").exists()
    assert (tmp_path / "k_good2.mp3").exists()


def test_unconfigured_language_is_reported_not_guessed(tmp_path):
    manifest = [{"key": "k_ur", "lang": "ur", "text": "کھیت"}]
    results = synthesise_manifest(manifest, tmp_path, synth=SilentSynthesiser())
    assert results[0].path is None
    assert "no voice configured" in results[0].error
    assert not (tmp_path / "k_ur.mp3").exists()


def test_no_partial_file_is_left_behind(tmp_path):
    manifest = [{"key": "k1", "lang": "hi", "text": "ठीक"}]
    synthesise_manifest(manifest, tmp_path, synth=SilentSynthesiser())
    # A leftover .part would later satisfy the skip-if-exists check and serve truncated audio.
    assert list(tmp_path.glob("*.part")) == []


def test_empty_audio_is_treated_as_failure(tmp_path):
    manifest = [{"key": "k1", "lang": "hi", "text": "ठीक"}]
    results = synthesise_manifest(manifest, tmp_path, synth=SilentSynthesiser(b""))
    assert results[0].path is None
    # A zero-byte mp3 would pass a naive existence check and play as silence.
    assert not (tmp_path / "k1.mp3").exists()


def test_prune_removes_only_unreferenced_clips(tmp_path):
    manifest = [{"key": "keep_me", "lang": "hi", "text": "क"},
                {"key": "drop_me", "lang": "hi", "text": "ख"}]
    synthesise_manifest(manifest, tmp_path, synth=SilentSynthesiser())
    removed = prune_unused(tmp_path, ["keep_me"])
    assert removed == ["drop_me"]
    assert (tmp_path / "keep_me.mp3").exists()
