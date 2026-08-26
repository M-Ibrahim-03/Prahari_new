# PRAHARI — Phased Implementation Plan

> **This is an implementation plan only.** No code is written here. It reconciles three sources:
> the **PRD** (`PRAHARI-PRD.md`, the source of truth), the step list in
> `PRAHARI-IMPLEMENTATION-PLAN.md`, and a **direct audit of the code as it exists today**.
>
> **Governing laws (from PRD + plan.md — every phase obeys these or it is wrong):**
> 1. **₹0.** No paid tier, no credit card, no expiring trial. Anywhere.
> 2. **`engine/` is PURE** — no network, filesystem, clock, randomness, or env vars. Enforced by `tests/test_purity.py`.
> 3. **The app never names a fungicide, dose, concentration, PPE item, or re-entry interval.** A CI string-test fails the build if one appears (§13.7, §39.2).
> 4. **An LLM may only rephrase what the engine computed.** It may never produce or alter a number or a band (§27).
> 5. **Every step ends in something demonstrable.** Every failure path shows a named `§28.3` degradation rung.
> 6. **Cut from the bottom, never the middle.** If time runs out, drop the last phase whole — never half-build a middle one.

---

## 0. As-built baseline — what is already DONE (verified 2026-08-26)

Confirmed by reading the files, not assumed. **Phase 0 and most of Phase 1 already exist and are correct.**

### ✅ Engine (PURE, tested)
| File | State |
|---|---|
| `engine/rules.py` | ✅ **All four silent bugs handled correctly.** `hours_rh_at_or_above` uses `>=` (bug 1); `longest_wet_spell_hours` counts only contiguous runs (bug 3); `criterion_met` is consecutive-not-total — `[True,False,True]` → `False` (bug 4). |
| `engine/aggregate.py` | ✅ `DayStats`, `CellAssessment`, `daily_stats` (daily-mean not spell-mean — bug 2), `assess_cell` with severity-gated bands. `ml_delta` hardcoded `0.0` (Phase-1 physics-only, correct). |
| `engine/interpolate.py` | ✅ `temp_with_lapse` (6.5 °C/km), `rh_from_temp_and_dewpoint` (Magnus a=17.625 b=243.04), `cell_rh_from_node` (RH **recomputed**, never lapse-corrected), `bilinear`. |
| `engine/grid.py` | ✅ `Cell`, `Grid`, `build_grid`, `interp_at_cell`. |
| `engine/wallin.py` | ✅ `wallin_dsv` — DSV table lookup driven by `models.yaml`. |
| `engine/fields.py` | ✅ `resolve_cell`, `sort_worst_first` (worst-band-first ordering). |
| `engine/advisory.py` | ✅ `build_advisory`, `why_reason`, `audio_key`, `name_audio_key`. |

### ✅ Adapters (all I/O, ≥2 implementations each)
`weather.py` (Open-Meteo + Replay providers, `align_from_date` handles the `past_days` origin shift), `elevation.py` (OpenMeteo + Static + `fetch_and_commit`), `tts.py` (Edge + Silent synthesiser, `synthesise_manifest`, `prune_unused`), `scenario.py` (deterministic scenario weather for demos), `settings.py` (env loader, adapters-only).

### ✅ Pipeline
`nightly.py` (`run_district`, `now_ist`, `engine_source_sha`, `main`), `artefact.py` (full §29.5 contract incl. `mean_wet_temp_c` exposed), `fields.py` (per-field payload slicing + clip manifest), `ledger.py` (**hash chain complete**: `compute_hash`, `append_entry`, `verify_chain`). Config: `models.yaml` (potato late blight Hutton+Wallin, cited), `districts.yaml` (Farrukhabad), `fields.yaml`, `scenarios.yaml`, `advisory_templates.yaml`.

### ✅ Web (farmer PWA — 3 of 5 nav items live)
`App.tsx` (Today / Map / Spray screens + 5-item bottom nav), `MapScreen.tsx` (Leaflet + MapTiler satellite, **no grid/choropleth**, fields as points), `SprayScreen.tsx`, `FieldCard.tsx`, `WhyPanel.tsx`, `DegradationNotice.tsx` (**full L1–L10 ladder, L7 thesis handled**), `DataAge.tsx`, `PlayButton.tsx`. Lib: `bandToSemantic.ts` (single source of band→colour), `types.ts`, `audio.ts`, `useFieldPayload.ts`. Styles: `tokens.css` (design tokens §22.2), `app.css`, `parts/`. PWA: `manifest.webmanifest`, `sw.js`, icons.

### ✅ Ops
`.github/workflows/ci.yml` (pytest + purity + ledger verify), `.github/workflows/nightly.yml` (cron `30 20 * * *` = 02:00 IST, `contents: write`, commits artefacts), `vercel.json`, `requirements.txt`, `pyproject.toml`, `docs/DEPLOY.md`.

### ⚠️ Known divergences from PRD (deliberate hackathon choices — not gaps to "fix")
- **Map stack is Leaflet + MapTiler raster**, not MapLibre GL (PRD §31). Works; keep unless vector layers are needed.
- **Styling is hand-rolled CSS + tokens**, not Tailwind/shadcn. i18n is inline dicts, not i18next.
- Not yet present: TanStack Query, Zustand, Dexie/IndexedDB, onnxruntime-web. These arrive with the phases that need them (offline queue, vision).

### ❌ Verified ABSENT (this is the work)
`engine/spray.py`, `engine/ensemble.py`, `engine/spread.py`, `engine/degree_day.py`, `engine/confidence.py` · `adapters/hindcast.py`, `adapters/ml_delta.py`, `adapters/llm/`, `adapters/satellite.py`, `adapters/osm.py`, `adapters/db.py` · `pipeline/validate.py`, `pipeline/verbalise.py`, `pipeline/config/area_units.yaml`, `pipeline/config/copy.yaml` · `tests/test_spray.py`, `tests/test_gate.py` · `web/src/screens/Trust.tsx`, `web/src/lib/supabase.ts`, `web/src/lib/outbox.ts` · `supabase/schema.sql` · `ml/`, `console/`, `site/` · **confidence is computed nowhere** (the word appears only in one UI string).

---

## How the phases map to the sources

| This plan | plan.md steps | PRD phase gate |
|---|---|---|
| **Phase A — Spray windows** | Step 1 | §40 Phase 3 (partial) |
| **Phase B — Second/third pathogen** | Step 2 | §40 Phase 7 (first validated model) |
| **Phase C — Public trust site** | Step 3 | §40 Phase 1 + Phase 6 |
| **Phase D — Persistence + full nav** | Step 10 | §40 Phase 4 groundwork |
| **Phase E — Field capture** | Step 9 | §40 Phase 2 (**highest-risk gate**) |
| **Phase F — LLM verbaliser** | Step 7 | §40 Phase 5 |
| **Phase G — Confidence + ensemble** | Step 6 | §40 Phase 5 |
| **Phase H — Validation + hindcast** | Step 4 | §40 Phase 6 |
| **Phase I — ML residual correction** | Step 5 | §40 Phase 6 |
| **Phase J — On-device leaf photo** | Step 8 | §40 Phase 7 |
| *(prereq)* **Step 0** — Actions write permission | Step 0 | already satisfied in `nightly.yml` |

> **Step 0 is already done** — `nightly.yml` declares `permissions: contents: write`. Verify once in the Actions tab on first push; no code change needed.

**Ordering rationale.** A→C are the highest value-per-token and unblock the two dead nav buttons and the public credibility surface. D (persistence) must precede E (field capture) because captured fields need somewhere to live. E is the PRD's highest-risk gate and gates the "real farmer" story. F (LLM) unblocks the 🎤 Ask button. G/H/I are the science-rigour layers. J is pure polish. **Everything from F down can be cut from the bottom with the product still coherent.**

---

## PHASE A — Real spray windows *(plan.md Step 1)*

**Goal.** Replace the "window calculation is not built yet" apology in `SprayScreen.tsx` with real, gated spray windows. This is the single most visible half-finished thing in the app.

**Read first:** PRD §13.2 (lines 1404–1444) — the seven gates and reason codes.

**Build**
- `engine/spray.py` (PURE) — `spray_windows(hourly, params) -> list[Window]`. Seven gates with reason codes: `RAIN_NOW`, `RAIN_AFTER`, `WIND_HIGH`, `WIND_CALM`, `TEMP_HIGH`, `DARK`, `TOO_LATE`. PARAMS: `rain_free_hours_after 4.0`, `max_rain_mm_during 0.2`, `wind_max_ms 4.0`, `wind_min_ms 0.5`, `temp_max_c 33.0`, `min_window_hours 2.0`, daylight 06–18. **A window must fully complete before risk onset.**
- `tests/test_spray.py` — one test per gate; assert a window straddling a rain hour is rejected by `RAIN_AFTER`; assert windows that end after risk onset are dropped by `TOO_LATE`.
- Wire into `pipeline/nightly.py` → `run_district`, emit `spray_start_hour`, `spray_end_hour`, `spray_quality`, `spray_blocked_by`, `spray_text_hi` into each field payload (contract already reserves these fields — see `pipeline/artefact.py`).
- Add spray gate params to `models.yaml` (data, not `if`-statements).
- `web/src/components/SprayScreen.tsx` — **delete the `windowTitle`/`windowBody`/`notBuilt` apology block**; render the real window and its blocking reasons.
- Village-collective window (§13.4): ≥60 % coverage rule — compute in pipeline, expose as an optional aggregate. *(Defer if time-boxed; single-field windows are the gate.)*

**Invariants.** Engine stays pure (windows are computed from arrays passed in, clock comes from the pipeline). No dose/PPE strings enter `SprayScreen`. Missing wind/rain data → window omitted with a reason, never guessed.
**Degradation.** No spray inputs → show band only, note "spray timing unavailable", not a fake window.
**Gate / demo.** Open Spray screen on the `farrukhabad` scenario → see "Spray Tuesday 06–09, rain after 14:00" with a real blocking reason. `test_spray.py` green.
**Stop-line (4 h):** windows render for the demo scenario with at least `RAIN_AFTER` and `TOO_LATE` proven in tests.

---

## PHASE B — Second & third pathogen model *(plan.md Step 2)*

**Goal.** Prove the engine is model-agnostic by adding **potato early blight (TOMCAST DSV)** and generalising band selection to worst-band-wins across enabled models.

**Build**
- Generalise `engine/wallin.py` (or add `engine/dsv.py`) so the DSV table + breakpoints come entirely from YAML — no pathogen hardcoded.
- `models.yaml` — add `potato_early_blight_tomcast` with its own `dsv_table`, `citation:` (NOT NULL), `crop:`, `pathogen_kind: fungus` (early blight *is* a fungus; late blight is an oomycete — keep the distinction).
- `engine/aggregate.py` / a new `combine_models` — **worst-band-wins** across all enabled models for a cell.
- `web/src/components/WhyPanel.tsx` — show *which model fired* ("Early blight risk, TOMCAST DSV 19").
- `tests/` — early-blight DSV lookup + worst-band-wins resolution.

**Invariants.** No uncited model (`citation` required). Physics-only; ml_delta still 0. Worst-case aggregation preserved (§8.2 Step 4).
**Degradation.** A model with missing params is skipped, not defaulted; the others still run.
**Gate / demo.** A cell safe for late blight but `act` for early blight shows `act` with the reason naming early blight.
**Stop-line:** two models resolve worst-band-wins in a test + the WhyPanel names the firing model.

---

## PHASE C — Public trust site *(plan.md Step 3)*

**Goal.** The sceptic's surface. A public site at `?app=trust` (or `site/`) with a ledger viewer that verifies the hash chain **in the visitor's own browser**.

**Read first:** PRD §36 (`ChainVerifier`), §18.3 methodology, §18.4 limitations.

**Build**
- `web/src/screens/Trust.tsx` — routes for `/`, `/accuracy`, `/ledger`, `/methodology`, `/limitations`, `/models`, `/data`, `/api`.
- `web/src/lib/chainVerifier.ts` — mirror `pipeline/ledger.py`: `sha256(canonicalJSON(body))`, walk `ledger.jsonl`, report `{ok, brokenAt, count}`. **Must match the Python canonicalisation exactly** (`sort_keys=True, separators=(",",":")`).
- Accuracy page: honest **empty state** now (real numbers arrive in Phase H). Show the §35.4 economic-asymmetry argument (~62×, FAR 0.60 vs 0.15 columns) as the framing.
- Limitations page: verbatim honesty from §34.3 / Part VII ("we estimate wet duration from RH as a proxy", "1 km is computation not measurement resolution").
- Wire the ☰ **More** nav button (currently disabled) → Trust screen.

**Invariants.** Five states on every data surface: loading / empty / error / stale / success. No accuracy number that isn't real — empty state until Phase H.
**Degradation.** Ledger fetch fails → "cannot verify right now", never a fake ✓.
**Gate / demo.** Open `/ledger` → chain verifies green in-browser; tamper one byte in a local copy → it reports `brokenAt: n`. **More** button now works.
**Stop-line (14 h cumulative):** ChainVerifier verifies the committed ledger in-browser and detects a tamper.

---

## PHASE D — Persistence + last two nav buttons *(plan.md Step 10)*

**Goal.** Give fields a home (Supabase + local), add the feedback button, finish the nav. Prereq for Phase E.

**Read first:** PRD §30 (schema), §33 (RLS/privacy), §17.3 (feedback), §28.3 L8/L9.

**Build**
- `supabase/schema.sql` — tables from §30, **RLS on every table**, k≥5 view (`HAVING COUNT(DISTINCT device_hash) >= 5`), ledger append-only SQL rules. **This must be applied before `SUPABASE_ANON_KEY` is trusted in the browser** (see `.env` warning).
- `web/src/lib/supabase.ts` — anon client; inserts only (feedback, device), never cross-farmer reads.
- `web/src/lib/outbox.ts` — offline write queue with **idempotency keys** (L8 DB-unreachable, L9 offline). IndexedDB (Dexie) arrives here.
- `⚠️ यह गलत है` / "This is wrong" feedback button (§17.3) → structured feedback row.
- Store field/cell **reference only** — never name, GPS, polygon, phone, or photo in the analytics path (§33.1).

**Invariants.** k≥5 lives in the SQL, not the client. Phone hashed SHA-256, never raw. RLS mandatory — the migration is not optional.
**Degradation.** DB unreachable → writes queue locally, static artefacts still serve (L8); offline → full cached experience, sync on reconnect (L9).
**Gate / demo.** Submit feedback offline → it queues → reconnect → it syncs exactly once (idempotency proven).
**Stop-line (22 h cumulative):** schema.sql applies with RLS on; feedback button queues and syncs once.

---

## PHASE E — Field boundary capture *(plan.md Step 9 · PRD Phase 2 — HIGHEST-RISK GATE)*

**Goal.** A farmer captures a real field boundary. PRD calls this the highest-risk gate in the whole project. **Call it manual capture, not segmentation** — there is no ML boundary model in this build.

**Read first:** PRD §7 (capture methods), §7.4 (validation), §7.6 (local units), §20.

**Build**
- Leaflet tap/drag/close-polygon capture on the existing satellite `MapScreen`.
- `pipeline/config/area_units.yaml` — bigha-per-district conversions (§7.6). **`[HUMAN]`: each district's bigha value must be officer-confirmed** — this is schedule risk, not code.
- Area shown in **both hectares and local unit** (§20.2 Screen 05 confirmation step).
- §7.4 validation: self-intersection, min/max area sanity.
- Persist via `outbox.ts` → localStorage first, then Supabase (Phase D dependency).
- `capture_method` recorded as `manual` (honest label).

**Invariants.** No fabricated boundaries — the map still shows points until a farmer draws one. Area confirmation in local units is mandatory before save.
**Degradation.** No GPS → manual pan-and-tap still works; no network → localStorage, sync later.
**Gate / demo.** Tap four corners → polygon closes → area shows "0.8 ha / ~2 bigha" → save → reload → field persists.
**Stop-line (9 h for this phase):** a polygon captures, validates, shows dual-unit area, and persists across reload.

---

## PHASE F — Gemini verbaliser behind the §27.5 gate *(plan.md Step 7 · PRD Phase 5)*

**Goal.** Turn engine facts into warm spoken language — as a **translator, never an oracle**. Unblocks the 🎤 Ask button.

**Read first (mandatory before writing a line): PRD lines 3078–3158** — §27.3 system prompt and §27.5 validation gate.

**Build**
- `adapters/llm/base.py` — `LLMProvider` Protocol.
- `adapters/llm/gemini.py` — Gemini free-tier client (server-side only; `GEMINI_API_KEY` never reaches the browser).
- `adapters/llm/template.py` — deterministic template provider (the always-works fallback).
- `pipeline/verbalise.py` — `verbalise(facts, lang)`; `facts` is a **frozen dataclass**, LLM sees only these fields, no tools, no engine access, `max_tokens=200 temperature=0.3`.
- `pipeline/validate.py` — the five rejection rules: invented number, banned chemical term, dose/interval pattern, changed band/verb, length drift (>60 words). Fail → `render_template` + `log_gate_rejection`.
- `tests/test_gate.py` — **adversarial fixtures**: an LLM output that invents "250 ml" → rejected; one that names a fungicide → rejected; one that flips `watch`→`act` → rejected.
- Wire the 🎤 **Ask** nav button (currently disabled).

**Invariants.** The gate is the safety layer — product/dose tables are **absent from the corpus by design** (§27.4). Rejection rate is a monitored metric.
**Degradation.** LLM unavailable or gate rejects → template advisory, `no_llm` → **L4** ("indistinguishable in content quality").
**Gate / demo.** Feed a deliberately poisoned LLM output → gate rejects it → farmer sees the clean template. `test_gate.py` green.
**Stop-line:** all five rejection rules proven in `test_gate.py`; Ask button falls back to template with L4 shown.

---

## PHASE G — Confidence + ensemble agreement *(plan.md Step 6 · PRD Phase 5)*

**Goal.** Turn model agreement into a displayed confidence. **Confidence is currently computed nowhere** — this phase creates it.

**Build**
- `engine/confidence.py` (PURE) — field confidence = **min of cell confidences**; cell confidence from node agreement + data completeness.
- `engine/ensemble.py` (PURE) — agreement across multiple Open-Meteo NWP models → confidence signal.
- `adapters/weather.py` — fetch ≥2 NWP models (still ≤2 API calls/district-night budget via the lattice).
- Emit `confidence`, `confidence_label` into the artefact (contract already names them).
- Surface confidence on `FieldCard` / `WhyPanel` (§21.5 — confidence on every surface).

**Invariants.** ≤2 weather calls per district-night preserved. Confidence = min (worst-case), never mean.
**Degradation.** Single model available → confidence drops and says so (L6), never silently full-confidence.
**Gate / demo.** A cell where two NWP models disagree shows lower confidence than one where they agree.
**Stop-line:** confidence appears on the field card and drops visibly under model disagreement.

---

## PHASE H — Hindcast validation *(plan.md Step 4 · PRD Phase 6)*

**Goal.** Replay ERA5 history through the engine. **Label it honestly: forecast-vs-reanalysis agreement, not disease validation.**

**Read first:** PRD lines 3635–3653 (economic asymmetry, FAR 0.60 operating point) and §35.2 (frozen-ground-truth protocol).

**Build**
- `adapters/hindcast.py` — Open-Meteo ERA5 Archive replay (keyless, free).
- `pipeline/validate.py` (extend) — score hindcast vs the physics engine; contingency table; per-crop×pathogen (never pooled); negative cases scored.
- **Frozen ground truth**: commit the ground-truth file, record the SHA, tune nothing before that commit. Every published metric cites `ground_truth_commit`.
- Feed real numbers into the Phase C accuracy page (replacing the empty state), with the §35.4 two-column cost argument.

**Invariants.** No metric without a `ground_truth_commit` predating all tuning. Sprayed fields excluded from miss counting (§35.3).
**Degradation.** No ground truth yet → accuracy page stays in honest empty state; do not invent numbers.
**Gate / demo.** `/accuracy` shows a real contingency table citing a frozen commit SHA.
**Stop-line:** hindcast runs against ≥1 documented outbreak year and the accuracy page shows real numbers, whatever they are.

---

## PHASE I — ML residual correction *(plan.md Step 5 · PRD §26.5)*

**Goal.** Learn where the physics is *systematically wrong* — bounded, never overriding.

**Build**
- `adapters/ml_delta.py` — LightGBM on (forecast − ERA5) residuals; features: terrain, aspect, TWI, distance-to-water, NDVI, node disagreement, DOY, stage.
- Apply δ in the pipeline: `final_risk = clamp(physics_risk + δ, 0, 1)`, **δ capped ±0.25** (§26.5).
- **Band-flip rule**: a correction may never move `safe → act` on its own — only physics can.
- Untrained / low-confidence → δ = 0.
- Emit `ml_delta` into the artefact (currently hardcoded 0.0 in `aggregate.py`).

**Invariants.** ±0.25 hard cap. Physics alone decides safe→act flips. Model version stamped on output. No model trained on uncitable data.
**Degradation.** ML unavailable → δ = 0, pure physics, officer trace shows it → **L2** (`no_ml`).
**Gate / demo.** Officer trace shows `physics_risk 0.62 + δ 0.05 = 0.67`; disabling ML changes nothing structural.
**Stop-line:** δ applied and capped in a test; disabling the model degrades to L2 cleanly.

---

## PHASE J — On-device leaf photo *(plan.md Step 8 · PRD §12)*

**Goal.** A leaf-photo confirmation model that runs **on the phone**, offline. Confirmation only.

**Build**
- MobileNetV3-Small → ONNX opset 13 → int8, ≤5 MB. Lazy-loaded, ≤400 ms inference.
- `onnxruntime-web` (arrives here). Keep the bundle lean (current ~102 kB gzip; model is lazy, not in the initial bundle).
- Photo **never leaves the device** (§33.2) — no upload without explicit per-image consent.
- State the domain gap honestly (lab-vs-field accuracy, §12.3).

**Invariants (P3).** The classifier **may never change a spray recommendation.** It confirms; the engine decides.
**Degradation.** Model unavailable → "photo check not available", the forecast is unaffected.
**Gate / demo.** Scan a leaf offline → get a confidence-scored suggestion that does *not* alter the spray verdict.
**Stop-line:** on-device inference runs offline in <400 ms and cannot move a band.

---

## Cross-cutting checklist (verify at every phase gate)

- [ ] `python -m pytest` green — purity + four silent-bug tests still pass.
- [ ] CI string-test: **no fungicide/dose/PPE string** in any UI copy, template, or YAML.
- [ ] Every new failure path shows a **named L-rung** from §28.3 (not a blank screen).
- [ ] Five states on every data surface: loading / empty / error / **stale** / success.
- [ ] Design tokens only (§22.2): risk colours from `bandToSemantic.ts`, `--touch-min 56px`, amber uses dark `--on-risk-watch` text.
- [ ] Artefact still within payload budget (<150 KB/district, <20 KB/farmer).
- [ ] `≤2` weather API calls per district-night.
- [ ] Any new external system sits behind an adapter Protocol with **≥2 implementations**.
- [ ] **Rotate all keys after the hackathon** (the `.env` keys were shared in chat).

## `[HUMAN]` work — start early, cannot be coded faster
Bigha values per district (Phase E), retrieval corpus + human-reviewed translations (Phase F), ground-truth collection + pathologist sign-off (Phase H), real-device 3G testing, farmer usability test for the Phase E gate. **These are the schedule risk, not the code.**

## The stop-lines, restated
**4 h** → spray windows (A). **9 h** → field capture (E). **14 h** → trust site + ChainVerifier (C). **22 h** → persistence + feedback (D). Beyond that, F→J are added **one at a time, cut from the bottom**. Shipping A–E fully is a coherent product; shipping ten half-built phases is not.
