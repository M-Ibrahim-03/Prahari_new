"""Tests for the tamper-evident ledger (§18.2 / §36) — hash chaining and tamper detection."""
from pipeline.ledger import GENESIS_HASH, append_entry, compute_hash, verify_chain


def _body(seq, cell_id, band="act"):
    return {"seq": seq, "cell_id": cell_id, "model": "m@1", "band": band,
            "inputs_digest": "sha256:abc"}


def test_empty_ledger_verifies(tmp_path):
    assert verify_chain(tmp_path / "ledger.jsonl") == {"ok": True, "count": 0}


def test_chain_links_and_verifies(tmp_path):
    p = tmp_path / "ledger.jsonl"
    r0 = append_entry(p, _body(0, "FRK-R000-C000"))
    r1 = append_entry(p, _body(1, "FRK-R000-C001"))
    assert r0["prev_hash"] == GENESIS_HASH
    assert r1["prev_hash"] == r0["hash"]              # chained
    assert verify_chain(p) == {"ok": True, "count": 2}


def test_tampering_breaks_the_chain(tmp_path):
    p = tmp_path / "ledger.jsonl"
    append_entry(p, _body(0, "FRK-R000-C000"))
    append_entry(p, _body(1, "FRK-R000-C001"))
    # Silently edit the first record's band act->safe, leaving its stored hash intact.
    lines = p.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace('"band":"act"', '"band":"safe"')
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = verify_chain(p)
    assert result["ok"] is False
    assert result["broken_at"] == 0                  # caught at the edited record


def test_compute_hash_excludes_only_hash_field():
    rec = {"seq": 1, "prev_hash": GENESIS_HASH, "hash": "ignored"}
    h1 = compute_hash(rec)
    h2 = compute_hash({"seq": 1, "prev_hash": GENESIS_HASH, "hash": "different"})
    assert h1 == h2                                  # hash field itself is not part of the digest
    assert h1.startswith("sha256:")
