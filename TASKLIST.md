# PRAHARI — Build Task List

**Legend:** ✅ done & tested · 🔨 in progress · ⬜ not started · ⏸️ deferred/optional
**Last updated:** 2026-08-26 · **Tests green:** 108 passing · **First live artefact:** ✅ produced

---

## Phase 1 — Provable Core (h0–h8): *"the forecast exists and is honest"* — ✅ COMPLETE

### Foundation & secrets
- ✅ `.gitignore` (written before any secret)
- ✅ `.env` — your real API keys, gitignored, never committed
- ✅ `.env.example` — placeholder template for teammates/judges
- ✅ `adapters/settings.py` — loads keys, fails loud if missing
- ✅ `pyproject.toml`, `requirements.txt` — pytest config + deps
- ✅ `README.md` — architecture boundary + setup

### Pure engine (no network / no clock / no randomness — AST-enforced)
- ✅ `engine/rules.py` — Hutton wet-hours, wet-spell, consecutive-day criterion
- ✅ `engine/wallin.py` — Wallin (1962) DSV severity table + lookup
- ✅ `engine/interpolate.py` — lapse temp+dewpoint, **recompute RH via Magnus** (never lapse RH)
- ✅ `engine/grid.py` — node lattice → cell grid, bilinear weights precomputed
- ✅ `engine/aggregate.py` — hourly weather → daily stats → **severity-gated** risk band

### Engine tests (the safety net)
- ✅ `tests/test_rules.py` — the **4 silent-bug tests** from PRD §8.6
- ✅ `tests/test_purity.py` — AST walker; **verified it has teeth** (catches injected impurity)
- ✅ `tests/test_interpolate.py` — lapse + Magnus + bilinear (6 tests)
- ✅ `tests/test_grid.py` — counts, id format, weights sum to 1, node-aligned interp (4 tests)
- ✅ `tests/test_aggregate.py` — consecutive-qualify, cold-reject, non-consecutive, **monsoon-heat→safe** (4)

### I/O adapters + first real artefact
- ✅ `adapters/weather.py` — Open-Meteo (keyless), all 3 traps handled; OpenMeteo + Replay impls
- ✅ `tests/test_weather.py` — 3 traps offline (single-vs-array, past_days origin, snap check) (6)
- ✅ `adapters/elevation.py` — keyless Open-Meteo elevation, fetch-once-commit; live + static impls
- ✅ `pipeline/config/districts.yaml` — Farrukhabad (potato belt UP): 25 nodes, 441 cells
- ✅ `pipeline/artefact.py` — assembles §29.5 GeoJSON contract (drops unknown props, honest)
- ✅ `pipeline/ledger.py` — hash chain + verify (mirrors browser ChainVerifier §36)
- ✅ `tests/test_ledger.py` — chaining + **tamper detection** (4)
- ✅ `pipeline/nightly.py` — orchestrator: live weather → engine → artefact + ledger
- ✅ **MILESTONE: live artefact produced** → `artefacts/farrukhabad/today.geojson` (7.2 KB gzip)
- ✅ `.github/workflows/nightly.yml` — cron 02:00 IST, commits artefact (our "server")
- ✅ `.github/workflows/ci.yml` — push CI: tests + purity + ledger-chain verify

### Decisions locked
- ✅ **Band policy = severity-gated** (your call): criterion-met-but-DSV-0 (too hot/cold for the
  pathogen) → **safe**, not a false-alarm "watch". Verified live: Farrukhabad today = safe (27 °C
  is above late blight's 26.6 °C ceiling). `mean_wet_temp_c` exposed so the reason is auditable.

---

## Phase 2 — Farmer PWA (h8–h18): *"a farmer can see and hear the warning"* — ✅ COMPLETE (2 items moved)
- ✅ Vite + React PWA scaffold, MapTiler map (browser key, domain-restricted)
- ✅ Load committed artefact, render risk cells + district view
- ✅ Plain-language advisory panel (band → action) — 3 cards, worst-first, every card ends in an action
- ✅ Pre-generated hash-keyed TTS voice notes (edge-tts, free) — offline playback, device-speech fallback
- ✅ Degradation ladder L0–L7 surfaced honestly in UI — `DegradationNotice`; unknown rungs shown verbatim, never swallowed
- ✅ Spray screen (💊 nav) — 🔴 states no fungicide name or dose and defers to the KVK officer
- ✅ Demo scenario switcher — `?view=` deep link runs synthetic weather through the **real** engine
- ⏭️ Supabase: store feedback / device registrations — **deferred by you**, moved to Phase 3
- ⏭️ Deploy to Vercel (free) — **you are doing this yourself**; `vercel.json` + `docs/DEPLOY.md` written and ready

### Why the demo switcher exists
Late blight is a rabi-season disease. A live August run correctly returns `safe` for all 441 cells, so
the act/watch path never appears. `?view=farrukhabad_blight_outbreak` feeds synthetic weather through
the unmodified engine — the engine still decides every band, and the artefact is stamped
`data_status: scenario` so it can never be mistaken for a forecast.

## Phase 3 — Intelligent & Validated (h18–h24): *"it's smart and it proves itself"*
- ⬜ Gemini advisory generation (free AI Studio key) — natural-language guidance
- ⬜ Supabase feedback + device registration (`⚠️ यह गलत है` button, PRD §17.3) — carried over from Phase 2
- ⬜ `ml_delta` residual correction hook (LightGBM ±0.25 cap) — optional, how-to in plan §6
- ⬜ Accuracy page: ERA5 hindcast validation instead of field ground-truth
- ⬜ Confusion matrix / skill scores rendered honestly
- ⬜ Public alert-ledger page + in-browser ChainVerifier
- ⬜ 🎤 Ask screen (needs Gemini) and ☰ More screen
- ⬜ Demo script + judge walkthrough

---

## Costs money → simulated or dropped (₹0 budget)
- ⏸️ Real SMS gateway / IVR / paid WhatsApp → **simulated** in UI, not wired to a paid provider
- ⏸️ Real farmer & field ground-truth data → **not needed** for hackathon; ERA5 hindcast validates instead
- ⏸️ Paid map tiles beyond MapTiler free tier → stay within free quota

## Human-in-the-loop (only where you must act)
- ✅ Paste API keys (done — Gemini, Supabase, MapTiler, OpenTopo)
- ⬜ *(optional)* Fine-tune a model on Colab/Kaggle if we reach Phase 3 ML — how-tos ready in plan §6
- ⬜ Domain-restrict the MapTiler key in their dashboard before public deploy
- ⬜ *(when you make a GitHub repo)* the two workflows activate automatically; no secrets needed (all keyless)
