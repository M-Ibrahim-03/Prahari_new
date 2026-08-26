"""Text-to-speech synthesis for pre-generated advisory clips.

🔴 §14.2 pre-generation law: audio is synthesised in the nightly job and served as static files.
Never at request time. Two reasons, and only the second one is about money:

  1. A farmer on 2G taps "listen" and must hear speech immediately. A request-time synthesis
     round-trip is the difference between a usable feature and an abandoned one.
  2. Cost. Content-addressed keys mean a district of 50,000 farmers collapses to a few dozen
     distinct clips, and a re-run synthesises only what is new (§14.8).

Engine: `edge-tts`, which speaks through Microsoft Edge's read-aloud endpoint. Free, keyless,
no account, no quota to sign up for — chosen because the project budget is zero. It is an
undocumented endpoint, so it may change without notice; that is why `synthesise_manifest`
reports failures per clip instead of aborting, and why the app keeps a device-speech fallback.

This module is an ADAPTER: all network and filesystem work lives here. The text it speaks is
handed to it by pipeline.fields.build_clip_manifest — it never composes advisory wording itself.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Protocol, Sequence

# Indian-language neural voices. Female voices for both languages, kept deliberately consistent:
# the advisory voice should be recognisable, not vary clip to clip.
DEFAULT_VOICES = {
    "hi": "hi-IN-SwaraNeural",
    "en": "en-IN-NeerjaNeural",
}

# Slightly slow. A farmer hears this once, standing in a field, possibly with wind noise.
DEFAULT_RATE = "-10%"


@dataclass(frozen=True)
class ClipResult:
    key: str
    path: Optional[str]      # None when synthesis failed
    bytes_written: int
    skipped: bool            # True when the file already existed
    error: Optional[str]


class Synthesiser(Protocol):
    """Second implementation exists for tests (§29.7): see SilentSynthesiser."""

    def synth(self, text: str, voice: str, rate: str) -> bytes: ...


class EdgeSynthesiser:
    """Real synthesis via edge-tts. Imported lazily so tests never need the dependency."""

    def synth(self, text: str, voice: str, rate: str) -> bytes:
        import edge_tts  # local import: keeps `engine`/test runs free of this dependency

        async def _run() -> bytes:
            chunks: list[bytes] = []
            comm = edge_tts.Communicate(text, voice, rate=rate)
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            return b"".join(chunks)

        return asyncio.run(_run())


class SilentSynthesiser:
    """Deterministic stand-in: emits a fixed byte string. Used by tests and offline runs."""

    def __init__(self, payload: bytes = b"ID3-fake-mp3") -> None:
        self._payload = payload
        self.calls: list[tuple[str, str, str]] = []

    def synth(self, text: str, voice: str, rate: str) -> bytes:
        self.calls.append((text, voice, rate))
        return self._payload


def synthesise_manifest(
    manifest: Sequence[dict],
    out_dir: Path,
    *,
    synth: Optional[Synthesiser] = None,
    voices: Optional[dict] = None,
    rate: str = DEFAULT_RATE,
    force: bool = False,
) -> list[ClipResult]:
    """Write one MP3 per manifest entry into `out_dir`, skipping clips that already exist.

    🔴 Skipping existing files is the whole economics, not an optimisation: keys are content
    hashes, so an existing file with the same key already contains the same words. `force=True`
    is available for when the voice or rate changes and every clip must be re-cut.

    A clip that fails to synthesise is reported and the run continues. One dead clip must not
    cost the district its entire audio set — the app falls back to device speech for that one
    message and says so.
    """
    synth = synth or EdgeSynthesiser()
    voices = voices or DEFAULT_VOICES
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[ClipResult] = []
    for item in manifest:
        key, lang, text = item["key"], item["lang"], item["text"]
        path = out_dir / f"{key}.mp3"

        if path.exists() and path.stat().st_size > 0 and not force:
            results.append(ClipResult(key, str(path), path.stat().st_size, True, None))
            continue

        voice = voices.get(lang)
        if voice is None:
            results.append(ClipResult(key, None, 0, False, f"no voice configured for lang {lang!r}"))
            continue

        try:
            data = synth.synth(text, voice, rate)
        except Exception as exc:  # noqa: BLE001 - one bad clip must not abort the district
            results.append(ClipResult(key, None, 0, False, f"{type(exc).__name__}: {exc}"))
            continue

        if not data:
            results.append(ClipResult(key, None, 0, False, "synthesiser returned no audio"))
            continue

        # Write to a temp file then replace, so a crash mid-write cannot leave a truncated clip
        # that later looks valid to the skip-if-exists check above.
        tmp = path.with_suffix(".mp3.part")
        tmp.write_bytes(data)
        tmp.replace(path)
        results.append(ClipResult(key, str(path), len(data), False, None))

    return results


def prune_unused(out_dir: Path, keep_keys: Iterable[str]) -> list[str]:
    """Delete clips whose key is no longer referenced. Returns the deleted keys.

    Kept separate from synthesis and never called automatically: an artefact directory shared by
    several districts would lose another district's clips if pruning ran on a partial key set.
    """
    keep = set(keep_keys)
    removed: list[str] = []
    if not out_dir.exists():
        return removed
    for f in sorted(out_dir.glob("*.mp3")):
        if f.stem not in keep:
            f.unlink()
            removed.append(f.stem)
    return removed
