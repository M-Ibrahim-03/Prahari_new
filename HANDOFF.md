# PRAHARI — Session Handoff (resume here)

**Last updated:** 2026-08-26. Build: `cd web && npm run build` passes clean (0 TS errors). Python: 145 tests pass.

PRAHARI = predictive potato late-blight advisory PWA for smallholder farmers (Hindi/English), built per `PRAHARI-BUILD-PLAN.md` phases A–J.

---

## ✅ DONE this session (all committed)

1. **Pipeline: multi-model (Phase B) + confidence (Phase G) genuinely run.**
   - `pipeline/nightly.py` runs BOTH Wallin (late blight) + TOMCAST (early blight) per cell; worst band wins (`engine.aggregate.combine_cell_assessments`). Ledger records which model fired.
   - `engine/confidence.py` → per-cell + per-field confidence (MIN of cells, §21.5). Emitted into `today.geojson` + `fields.json`.
   - Verified: `farrukhabad_blight_outbreak` shows `confidence:0.84`, `firing_model` = `potato_late_blight_hutton` (act/watch) and `potato_early_blight_tomcast` (safe cell).

2. **Artefacts regenerated + synced to `web/public/artefacts/`** for the 3 scenarios. (Web reads `/artefacts/<view>/fields.json`.) `borderline_watch` + `dry_spell` have NO `ledger.jsonl` — 0 alerts, honest.

3. **5 honesty/privacy fakes fixed:**
   - `web/src/screens/Trust.tsx` ledger table — now reads REAL fields (`seq`/`timestamp`/`cell_id`/`band`), was reading dead `run_id`/`district`/`counts` (showed a fake date + mislabelled every ACT as SAFE). Removed the fabricated `generateSampleLedger()` fallback; empty/missing ledger now shows an honest "no alerts / empty" banner. Tamper demo now flips a REAL hash-covered field (`band`).
   - Trust "Accuracy" tab — relabelled ">95% / <0.25" as **design targets, not measured**, and aligned FAR to the PRD high-sensitivity operating point (`≤ 0.60`). Body no longer claims "real physics model performance."
   - `web/src/components/AskModal.tsx` — removed the `setTimeout` simulation + false "§27.5 Gated AI" badge. Now calls `lib/ai.ts`.
   - `web/src/components/LeafScanModal.tsx` — removed fabricated confidence + "On-Device Inference" lie. Honest local symptom-guide always; real AI opinion only when configured.
   - **PII leak fixed** — `FieldCard`/`FeedbackModal` no longer send the farmer's field NAME to analytics (§33.1); send opaque `field.id` as `fieldRef`. Name is display-only.

4. **`web/src/lib/ai.ts` (NEW)** — the honest AI connector. Two paths, never a fake:
   - Real: POST to Supabase Edge Function (`/functions/v1/ask`, `/functions/v1/leaf-scan`) — Gemini runs SERVER-SIDE, key never in browser. Active only when `VITE_SUPABASE_URL` + online.
   - Fallback: **Ask** = deterministic rephrasing of the field's own engine numbers (allowed by governing law 4). **Leaf** = `source:'guide'` → visual self-check, NO invented confidence.

5. **Phase E field validation (§7.4)** — `validateFieldPolygon()` in `web/src/components/MapScreen.tsx` (vertex cap ≤24, area 0.01–20 ha, self-intersection test). Blocks invalid boundaries on save with a localized reason.

6. **Confidence chip** added to `FieldCard` face.

---

## ⏳ REMAINING (start here, in priority order)

1. **Write the 2 Supabase Edge Functions** so the "real AI" path actually runs:
   - `supabase/functions/ask/index.ts` — Deno. Read `GEMINI_API_KEY` from `Deno.env`. Prompt Gemini to REPHRASE the provided engine `facts` into a farmer answer in `lang`; STRICT: never invent a number, never name any chemical/dose/PPE (governing law 3+4). CORS headers. Return `{ text }`.
   - `supabase/functions/leaf-scan/index.ts` — Deno. Gemini Vision (`gemini-2.0-flash`). Input `{ image (base64), lang }`. Return `{ symptom: late_blight|early_blight|healthy|uncertain, confidence, note }`. Framing: guidance only, never changes spray timing.
   - Client already calls these and falls back gracefully, so the app works before they exist.
   - Deploy: `supabase functions deploy ask --no-verify-jwt` (or keep JWT + anon key — client already sends `apikey` + `Authorization: Bearer <anon>`).

2. **Supabase RLS** — `supabase/schema.sql` MUST have RLS enabled on `feedback` before the anon key ships (insert-only for anon, no select). Verify/add before deploy.

3. **Regenerate the LIVE `farrukhabad` artefact** with the new pipeline (needs network): `python -m pipeline.nightly` then copy `artefacts/farrukhabad/*` → `web/public/artefacts/farrukhabad/`. (Currently the live artefact lacks confidence/firing_model; the 3 demo scenarios have them. Demo via the "Demo: blight outbreak" dropdown view.)

4. **Final QA** — `preview_start` port 5173, click through Today→Map→Spray→Ask→Trust in the blight_outbreak view, screenshot. Not yet browser-verified this session (skipped to save credits; build passes).

5. **Optional UI polish** — confidence on the map, general spacing. Low priority.

---

## 🔒 SECURITY (do NOT violate)

- **NEVER commit `.env`** (it holds real keys). It's gitignored; only `.env.example` is tracked. Confirmed clean this session.
- Browser may ONLY receive `MAPTILER_KEY` + `SUPABASE_ANON_KEY` (via explicit `define` allowlist in `web/vite.config.ts`).
- **Server-side ONLY, never in vite allowlist / Vercel build env:** `GEMINI_API_KEY`, `SUPABASE_SERVICE_KEY` (bypasses RLS), `OPENTOPO_KEY`, `SUPABASE_URL`.
- **Rotate ALL keys after the hackathon.**

## Governing laws (never break)
1. ₹0 / no paid tier. 2. `engine/` pure (no net/fs/clock/random/env). 3. NEVER name fungicide/dose/concentration/PPE/re-entry interval. 4. LLM may only REPHRASE engine output, never change a number/band. 5. Every failure shows a named §28.3 rung (L1–L10). 6. Cut from the bottom, never half-build the middle.

## Run / verify
```bash
# web
cd web && npm run build && npm run dev          # dev on :5173
# pipeline scenarios (offline synthetic weather → real engine)
python -m pipeline.nightly --scenario blight_outbreak     # also: borderline_watch, dry_spell
# then sync: cp artefacts/farrukhabad_<scen>/* web/public/artefacts/farrukhabad_<scen>/
python -m pytest -q                             # 145 tests
```
