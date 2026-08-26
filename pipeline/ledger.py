"""Tamper-evident alert ledger — IMPURE (writes files). PRD §18.2 / §36.

Append-only JSONL. Each entry chains to the previous via prev_hash; editing any past record
breaks every subsequent hash. compute_hash mirrors the client-side ChainVerifier (§36) so the
browser can independently recompute the whole chain and catch us if we ever lie.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

GENESIS_HASH = "sha256:" + "0" * 64
_PREFIX = "sha256:"


def compute_hash(record: dict) -> str:
    """sha256 over the canonical JSON of every field EXCEPT `hash` (prev_hash is included)."""
    body = {k: v for k, v in record.items() if k != "hash"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return _PREFIX + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def last_hash(path: str | Path) -> str:
    """The hash to chain the next entry from — the last line's hash, or GENESIS if empty."""
    p = Path(path)
    if not p.exists():
        return GENESIS_HASH
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return GENESIS_HASH
    return json.loads(lines[-1])["hash"]


def append_entry(path: str | Path, body: dict) -> dict:
    """Chain `body` (all fields except prev_hash/hash) onto the ledger and append one line."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    record = dict(body)
    record["prev_hash"] = last_hash(p)
    record["hash"] = compute_hash(record)
    line = json.dumps(record, sort_keys=True, separators=(",", ":"))
    with p.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return record


def verify_chain(path: str | Path) -> dict:
    """Recompute the whole chain. Returns {ok, count} or {ok: False, broken_at}."""
    p = Path(path)
    if not p.exists():
        return {"ok": True, "count": 0}
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    prev = GENESIS_HASH
    for i, line in enumerate(lines):
        rec = json.loads(line)
        if rec.get("prev_hash") != prev:
            return {"ok": False, "broken_at": i}
        if compute_hash(rec) != rec.get("hash"):
            return {"ok": False, "broken_at": i}
        prev = rec["hash"]
    return {"ok": True, "count": len(lines)}
