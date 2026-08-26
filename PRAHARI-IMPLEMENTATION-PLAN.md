# PRAHARI — HACKATHON IMPLEMENTATION PLAN (24 hours, ₹0 budget)

> **Companion to `PRAHARI-PRD.md`.** The PRD is the full production vision. This document is the **24-hour hackathon build plan** — free resources only, no real farmers, no field data collection, and "human work" redefined as *the API keys you paste in* and *the models you set up (with how-to)*.
>
> This is a **plan only**. No code is created by this document.

---

## 0. THE TWO GROUND RULES FOR THIS VERSION

**Ground rule 1 — Everything is free. Build cost = ₹0. No credit card, anywhere.**
Every resource below has a free tier or needs no key. The *only* things in the production PRD that cost money are the last-mile delivery channels, and we **simulate or drop all of them** (see §2). Free-tier quotas exist but a 24 h demo never approaches them.

**Ground rule 2 — "Human work" means two things only (your clarification):**
1. 🔑 **You paste in an API key** — a short checklist of accounts to create (all free, all <5 min).
2. 🤖 **You set up / fine-tune a model** — I tell you exactly how; you run the free notebook.

Everything the production PRD marked `[HUMAN]` that needs **real farmers, real officers, or real field data collected over a season** is **DROPPED for the hackathon** and listed explicitly in §7 so nothing looks silently skipped. A hackathon is judged on a working, credible demo — not a deployed government programme.

---

## 1. WHAT CHANGED FROM THE PRODUCTION PLAN

| Production PRD assumption | Hackathon reality | Change |
|---|---|---|
| Phases are multi-week capability gates | 24 hours, one team | Phases become **hour-blocked tracks** with **demo-able** gates, not season-long validations |
| Real farmers map fields; 10/12 unaided <90 s | No real farmers | You + teammates walk the flow; throttle with Chrome DevTools instead of a ₹8,000 Android |
| Per-district bigha confirmed by a local officer | No officer access | Use the **published constants already in `area_units.yaml`** (PRD §7.6) — demote from `[HUMAN]` to a code default |
| Retrieval corpus of ~395 curated docs | No time | **~15-doc demo corpus** you paste in (still no product names/doses) |
| Hand-label Indian parcels; train segmentation | No labelling time | **Pre-trained SAM point-prompt at inference — train nothing.** Manual-draw fallback always there |
| 5,000+ human pairs → fine-tune Gemma LoRA | No time / not needed | **Use Gemini free tier + output gate.** Gemma LoRA is an **optional stretch** with a how-to in §6 |
| Ground truth frozen; prospective season scored | No field season | **Hindcast** a documented historical outbreak year via free ERA5 archive — a real validation story with **zero field data** |
| Pathologist sign-off; officer 4-week usage | No experts on hand | Build the **trace screen** and demo it; drop the human sign-off gate |
| SMS + IVR + WhatsApp delivery | Costs money | **Simulate** (mock inbox / free Telegram bot); IVR dropped |

**What we KEEP unchanged** (cheap to build, and they are exactly what wins a hackathon on credibility): the four silent-bug tests, the purity test, the no-product-names CI string test, the L7 "never hide staleness" rule, k≥5 in the SQL schema, the ±0.25 ML bound, the hash-chained ledger + in-browser verifier, the three risk bands, 56 px touch targets. See §8.

---

## 2. THE FREE-RESOURCE LEDGER (what to use, what to simulate)

**No key at all — use freely (all server-side):**
Open-Meteo Forecast + **Archive/ERA5** (ERA5 is the hindcast validation source) · Sentinel-2 L2A + Sentinel-1 GRD (STAC/AWS) · OpenStreetMap/Overpass · **edge-tts** (the voice output — free, no key, instant).

**Free key or free account (all free, no card):**

| Service | What it's for | Sign-up friction | Hackathon note |
|---|---|---|---|
| **GitHub (+ Actions)** | Repo + the nightly "server" | Instant | Use a **public** repo → unlimited Actions minutes |
| **Vercel** or **GitHub Pages** | Host the PWA + serve artefacts | Instant | Vercel is the fastest deploy |
| **Supabase** | Postgres + PostGIS + pgvector | Instant | Free 500 MB; holds ledger + community reports |
| **Gemini API (Google AI Studio)** | Advisory verbaliser + RAG QA | Instant, **no card** | The one LLM you need; free tier is plenty |
| **MapTiler** | Satellite basemap tiles | Instant | 🔴 The **only** browser-facing key — restrict it to your Vercel domain |
| **Kaggle** or **Colab** | Free GPU for *optional* model training | Instant | Only needed if you do a §6 stretch model |
| **OpenTopography (SRTM)** | Elevation for lapse correction | Free key | 🔴 Fetch **once**, commit the file. Or skip lapse for a flat demo district |

**Slower/optional free accounts — default to the keyless alternative for a 24 h build:**

| Service | Why it's optional | Use instead |
|---|---|---|
| **Google Earth Engine** | Non-commercial approval can lag | **Sentinel via STAC/AWS (no key)** for NDVI on one demo tile |
| **Bhashini / ULCA** | Registration/access flow is slow | **edge-tts (no key)** for all voice |
| **Agmarknet / data.gov.in** | Only needed for mandi prices (not core) | Skip prices for the demo |

**💸 Costs money → SIMULATE or DROP (none needed for the demo):**

| Channel | Decision |
|---|---|
| Real **SMS** gateway | **Simulate** — render the SMS text in a "sent messages" panel, or pipe to a free **Telegram bot** |
| **IVR** phone calls | **Drop** |
| **WhatsApp** beyond free tier | **Simulate** the send (or one message inside the free tier) |

🔴 **Result: the entire hackathon build runs at ₹0 with no card.** (This matches the PRD's own §38.3 operating-cost table — every line there is ₹0 except telephony.)

---

## 3. 🔑 YOUR API-KEY CHECKLIST (the only "keys" human work)

Do this once, at the start. Put every secret in **GitHub Secrets** (for the Actions job) and **Vercel env vars** (for the app) — 🔴 **never commit them; `.env` stays gitignored.** Only the MapTiler key is allowed in the browser, and it must be **domain-restricted**.

| # | Key / account | Where you get it | Where it goes | Reaches browser? |
|---|---|---|---|---|
| 1 | **GEMINI_API_KEY** | aistudio.google.com → "Get API key" | GitHub Secret + Vercel env | ❌ server-side only |
| 2 | **MAPTILER_KEY** | maptiler.com → free account → Keys | Vercel env (public) | ✅ **yes — restrict to your domain** |
| 3 | **SUPABASE_URL / SUPABASE_SERVICE_KEY** | supabase.com → new project | GitHub Secret + Vercel env | ❌ service key server-side; use the anon key client-side |
| 4 | **OPENTOPO_KEY** *(optional)* | opentopography.org | Local only — run once, commit the elevation file | ❌ never at runtime |
| 5 | **GitHub token** | automatic in Actions (`GITHUB_TOKEN`) | — | ❌ |

That's the whole list. Open-Meteo, Sentinel, Overpass, and edge-tts need **no key**. Gemini needs **no credit card**.

---

## 4. THE MODELS — WHAT TO TRAIN (almost nothing) VS USE OFF-THE-SHELF

The PRD lists 9 models. 🔴 **For the hackathon you train nothing mandatory.** Here is the honest triage:

| # | PRD model | Hackathon decision | How |
|---|---|---|---|
| 1 | **Field segmentation** | ✅ **Use pre-trained, no training** | **SAM / MobileSAM point-prompt** at inference (Apache-2.0, free). Farmer taps → polygon. Confidence low → **manual draw** (always available). Export to ONNX for `onnxruntime-web` if you want it on-device |
| 2 | Crop-type classifier | ❌ **Skip** | Farmer picks crop from a dropdown (their answer wins anyway, PRD §26.3) |
| 3 | Phenology / sowing date | ❌ **Skip** | Farmer enters sowing date (authoritative anyway) |
| 4 | Risk residual corrector | 🟡 **Optional stretch** | Tiny LightGBM on hindcast residuals, bounded ±0.25. Trains in seconds on CPU. See §6 |
| 5 | Weather downscaler | ❌ **Skip** | Bilinear + lapse is fine for one demo district |
| 6 | Leaf/pest vision | 🟡 **Optional stretch** | Fine-tune MobileNetV3-Small on free **PlantVillage** dataset, export ONNX, run on-device. See §6 |
| 7 | **Grounded LLM** | ✅ **Use Gemini free tier** | Verbalise `AdvisoryFacts` → advisory, behind the output gate (§27.5). No training |
| 8 | Indic ASR (voice input) | ❌ **Skip** | Voice *output* (pre-generated edge-tts) is the important part; voice *questions* are not demo-critical |
| 9 | Embedding model (RAG) | ✅ **Off-the-shelf** | A multilingual sentence-transformer; no training |

🔴 **The demo-critical model is #1 (segmentation), and it needs zero training** — SAM is promptable out of the box. The LLM (#7) is Gemini free tier. Everything else is deterministic engine code or a dropdown. This is what makes the project achievable in 24 hours.

---

## 5. THE 24-HOUR BUILD — 3 PHASES AS HOUR BLOCKS

Same 3 phases as before, but the gates are now **"demo-able in the room,"** not "validated over a season." Rough hour splits assume a small team working in parallel (engine / app / ML+pipeline tracks).

### PHASE 1 — PROVABLE CORE  (≈ hours 0–8)
**Gate:** one clean, deterministic nightly run produces a correct risk artefact for one district, and the credibility tests pass.

Build:
- Repo with the `engine/ adapters/ pipeline/` **purity split** (PRD §25.4).
- 🔴 **`test_purity.py`** (AST walker) + the **four silent-bug tests** (§8.6) — wire into CI first. *(Cheap, and a judge-magnet.)*
- `models.yaml` — `potato_late_blight_hutton`, `pathogen_kind: oomycete`, Hutton params, Wallin DSV table.
- Weather adapter with the **three Open-Meteo traps** handled (§29.2).
- Interpolation: bilinear + lapse + **Magnus RH recompute** (never lapse RH). *(For a flat demo district you may skip lapse and note it.)*
- One district: grid + nodes; landmarks (Overpass) and elevation (SRTM) fetched **once and committed**.
- Nightly GitHub Actions job (`cron "30 20 * * *"` = 02:00 IST) — but for the demo, trigger it with `workflow_dispatch`.
- Artefact JSON to the **§29.5 contract**, within the **<150 KB** budget.
- Hash-chained **ledger** (append-only via SQL rules) + a CI chain-verify step.
- **Degradation ladder L0–L7**, including 🔴 **L7: show yesterday's forecast labelled stale with its age**.
- Accuracy-page scaffold with an **honest empty state**.

**Demo gate (replaces "7 nights unattended"):** one end-to-end run succeeds; re-running gives a **byte-identical** artefact (determinism); `criterion_met([True, False, True]) is False`; purity test blocks a deliberate violation.

**🔑 Keys this phase:** GitHub, Supabase. *(No browser key yet.)*
**🤖 Models this phase:** none.

---

### PHASE 2 — THE FARMER-FACING PWA  (≈ hours 8–18)
**Gate:** you can open the app, tap your field on satellite imagery, and get a spoken, banded advisory — offline-capable.

Build:
- Map screen: **MapTiler satellite** + landmark overlay + GPS locate.
- **SAM point-prompt segmentation** (pre-trained) → polygon; tap-to-snap + **manual vertex correction**; manual draw fallback. Walk-the-boundary optional.
- Onboarding Screens 01–08 (trim to essentials for the demo).
- Area in **hectares + local unit** from `area_units.yaml` constants.
- Field ↔ cell **worst-case aggregation** (§8.2 Step 4).
- TODAY screen: per-field cards, three bands (safe/watch/act) via the single `bandToSemantic.ts` source of truth.
- **Spray-window engine, all seven gates** (§13.2) + the village-collective ≥60% window.
- **Pre-generated, hash-keyed TTS via edge-tts** (§14.2) — audio built at pipeline time, keyed by text hash.
- Three-depth **Why** panel.
- **Offline-first PWA** (Workbox + IndexedDB) — full airplane-mode.
- **Delivery = simulated:** a "messages" panel showing the SMS/WhatsApp text (or a free Telegram bot). No paid gateway.
- Minimal **officer console**: weekly triage list + the **model trace screen** (the credibility view).

**Demo gate (replaces real-farmer tests):** you + a teammate map a field and reach a spoken advisory unaided; airplane-mode still shows the last forecast; DevTools 3G-throttle confirms it loads.

**🔑 Keys this phase:** **MapTiler** (browser, domain-restricted).
**🤖 Models this phase:** SAM (pre-trained, no training).

---

### PHASE 3 — INTELLIGENT & VALIDATED (the demo-winner)  (≈ hours 18–24)
**Gate:** the app gives a grounded AI advisory that cannot invent facts, and the accuracy page shows a **real hindcast result**.

Build:
- **Grounded AI agronomist:** Gemini free tier verbalises frozen `AdvisoryFacts` → advisory, behind the 🔴 **output gate (§27.5)** — every number must be in `allowed_numbers()`, banned-term check, >60 words rejected, on failure fall back to the deterministic template. *(This gate is the single most impressive safety feature to show a judge.)*
- **RAG QA** over your **~15-doc demo corpus** (embeddings in Supabase pgvector). 🔴 No product names or doses in the corpus.
- 🔴 **Hindcast validation (no field data):** replay a **documented historical late-blight outbreak** (pick a year+district) through the engine using the **free keyless ERA5 archive**; show DSV accumulation crossing threshold **before** the recorded outbreak date. Put the real contingency numbers on the accuracy page — honest, whatever they are.
- **k≥5 community outbreak demo:** reports stored **cell-only**, phone as SHA-256 hash, k-anonymity **in the SQL view** (`HAVING COUNT(DISTINCT device_hash) >= 5`).
- **Spread simulation** viz: anisotropic wind kernel, combined multiplicatively with env risk.
- **In-browser `ChainVerifier`** on the ledger — anyone can verify it live.
- *(Optional stretch, only if ahead of schedule):* the ±0.25 **residual GBM** and/or the **MobileNetV3 leaf-vision** model from §6.

**Demo gate:** generate ~20 advisories and eyeball them → **zero invented facts** (a quick human check *you* can do — this is the one "human judgment" task that survives); hindcast fires before the historical outbreak; chain verifies in the browser.

**🔑 Keys this phase:** Gemini.
**🤖 Models this phase:** Gemini (no training); embeddings (off-the-shelf); optional §6 stretch models.

---

## 6. 🤖 HOW TO FINE-TUNE THE OPTIONAL MODELS (free GPU, only if you have time)

You asked how to create/fine-tune models — here are concise, free-only recipes. **All are optional stretch goals; the demo works without any of them.**

**A. Risk residual corrector (LightGBM, ±0.25) — cheapest, CPU-only, ~minutes**
- Data: from the hindcast, rows of `(features → residual)` where `residual = observed_severity − physics_risk`. Features: `min_temp_c, wet_hours, mean_wet_temp_c, dsv_accum_7d, elevation, ndvi_anomaly`.
- Train: `LightGBMRegressor` (or sklearn `GradientBoostingRegressor`), small; **clip output to ±0.25**; 🔴 never let it flip safe→act alone.
- Serve: load in `engine`-adjacent code as a pure function; expose `ml_delta` in the artefact; δ=0 when off (degradation L2).

**B. Gemma LoRA verbaliser (Colab free T4, ~1–2 h) — replaces Gemini for offline independence**
- Data: a few hundred–few thousand `(AdvisoryFacts JSON → target advisory)` pairs. **Generate them with Gemini, then you eyeball-review** a sample (this is legitimate synthetic-data bootstrapping).
- Train: Colab free GPU + **Unsloth** or HuggingFace **PEFT/QLoRA** (4-bit) on `gemma-2-2b-it`. ~a few hundred steps.
- Serve: export adapter; load in `adapters/llm/local_gemma.py`; the output gate (§27.5) still applies.

**C. Leaf/pest vision (MobileNetV3-Small, Kaggle/Colab GPU, ~1 h) — on-device disease photo confirm**
- Data: **PlantVillage** (free, public) — or PlantDoc for field-realistic images.
- Train: transfer-learn MobileNetV3-Small; export **ONNX**; run on-device via `onnxruntime-web`. 🔴 Images **never stored**; cloud only on explicit per-image consent.

**D. Segmentation distillation (optional) —** distil SAM's outputs to a small U-Net student on a public field-boundary dataset for faster on-device inference. Only worth it if SAM feels heavy in the demo; otherwise use SAM point-prompt directly.

---

## 7. WHAT'S DROPPED / DEFERRED FOR THE HACKATHON (nothing hidden)

These production `[HUMAN]` items need real farmers, officers, or a growing season. They are **out of scope for 24 h** and would each be resumed for a real deployment:

- Real-farmer mapping test (10/12 unaided <90 s), non-literate screen-covered test, TalkBack-in-Hindi run, noon-LCD readability, real ₹8,000-Android-on-3G test → *replaced by* self/teammate walkthrough + DevTools throttling.
- Per-district bigha confirmation with a local officer → *replaced by* published constants; flag as `[VERIFY]`, not `[HUMAN]`.
- 395-doc corpus curation → *replaced by* ~15-doc demo corpus.
- Season-long ground-truth collection + frozen-commit + prospective scoring → *replaced by* ERA5 hindcast of a historical outbreak.
- Plant-pathologist sign-off; officer 4-week usage → trace screen built and shown; human sign-off deferred.
- Real SMS / IVR / paid WhatsApp → simulated or dropped.

---

## 8. NON-NEGOTIABLES TO KEEP (cheap + they win the judging)

Keep every one of these — they cost almost nothing and are the credibility story:

| Keep | Why it wins |
|---|---|
| Four silent-bug tests + purity test | Shows engineering rigour a judge can see in one screen |
| 🔴 No-product-names / no-dose CI string test | The safety headline: "we physically cannot recommend a pesticide" |
| L7 — never show a stale forecast without its age | The honesty headline |
| ±0.25 ML bound; ML can't flip safe→act | "The AI only nudges physics; it can't overrule it" |
| k≥5 in the SQL schema; cell-only; SHA-256 phone | The privacy headline judges love |
| Hash-chained ledger + in-browser verifier | "You don't have to trust us — verify the chain yourself" |
| Three bands, 56 px touch, single `bandToSemantic.ts` | The "built for a non-literate farmer" story |
| Grounded LLM output gate + template fallback | "The AI is a translator, not an oracle" |

---

## 9. ONE-PARAGRAPH SUMMARY

Nothing in this plan costs money — the whole build runs on free tiers with **no credit card**, and the only paid things (real SMS, IVR, paid WhatsApp) are **simulated or dropped**. "Human work" is now just two things: **paste 3 API keys** (Gemini, MapTiler, Supabase — all free, all instant) and **optionally fine-tune a model** using the free Colab/Kaggle recipes in §6 — but the demo needs **zero training**, because field segmentation uses pre-trained SAM point-prompting and the advisory uses Gemini's free tier. In 24 hours you build **Phase 1** (a pure, tested engine that emits one district's risk artefact deterministically), **Phase 2** (a satellite-map PWA where you tap a field and hear a banded spoken advisory, offline, with simulated messaging), and **Phase 3** (a grounded Gemini advisory behind an output gate that can't invent facts, validated by an **ERA5 hindcast of a real historical outbreak — no field data needed**, with a live-verifiable ledger and k≥5 privacy). Keep the cheap credibility features (silent-bug tests, purity, no-product-names, staleness honesty, ±0.25 bound, hash chain) because they are exactly what wins a hackathon; drop the real-farmer/field/officer validation because a hackathon is judged on a working, honest demo, not a deployed programme.
