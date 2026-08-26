# PRAHARI (hackathon build)

Predictive crop-health intelligence for Indian smallholder farmers.
See [`PRAHARI-PRD.md`](PRAHARI-PRD.md) (the source of truth) and
[`PRAHARI-IMPLEMENTATION-PLAN.md`](PRAHARI-IMPLEMENTATION-PLAN.md) (this build's plan).

## Architecture boundary (do not cross)

| Layer | Rule |
|---|---|
| `engine/` | 🔴 **PURE** — no network, files, clock, randomness, or env. Enforced by `tests/test_purity.py`. |
| `adapters/` | All I/O (weather, satellite, elevation, DB, LLM, TTS). Secrets enter only here. |
| `pipeline/` | Orchestration + `config/*.yaml` (all science lives in data, not `if`-statements). |

## Setup

```bash
python -m pip install -r requirements.txt
cp .env.example .env      # then fill in your keys (never commit .env)
python -m pytest          # runs the four silent-bug tests + the purity test
```

## Secrets

🔴 Secrets live in `.env` (gitignored) locally, and in **GitHub Secrets** / **Vercel env** in deployment.
Only `MAPTILER_KEY` is ever exposed to the browser, and only when domain-restricted.
The Supabase **service** key bypasses RLS — server-side only.

## Status

Phase 1 (Provable Core) in progress — see the task list in the implementation plan / chat.
