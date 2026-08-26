# PRAHARI — Demo Deployment, Step by Step

Exact commands for a working public demo. Follow the parts **in order**: Part B ships the anon key
to the browser, and that key is only safe once Part A's Row Level Security is live.

Your Supabase project ref is **`muuyogxmaoiybeadmxvr`** (this is public — it is inside the URL that
ships in the browser bundle). Everywhere below that appears as `<REF>`, use that value.

Total time: about 25 minutes. Everything here is free tier. **Nothing in this guide costs money.**

---

## Part A — Database (5 min, browser only)

RLS must exist before the anon key is public. With RLS off, that key is a read/write handle to the
whole database.

1. Open <https://supabase.com/dashboard> → your project → **SQL Editor** → **New query**.
2. Open `supabase/schema.sql` from this repo, copy the whole file, paste it in.
3. Click **Run**. Expect `Success. No rows returned`.
   - The file is re-runnable, so if you already pasted an older version, just run this one again.
4. Verify RLS is actually on — paste this and Run:

```sql
select tablename, rowsecurity from pg_tables
where schemaname='public' and tablename in ('devices','feedback','ledger_records');
```

All three rows must show `rowsecurity = true`. **If any is false, stop** and re-run step 3;
do not continue to Part B.

5. Confirm the k≥5 view is reachable (this was a real bug — the view had no grant):

```sql
select has_table_privilege('anon','cell_feedback_k5','select');
```

Must return `true`.

---

## Part B — Edge Functions (10 min, terminal)

This is what turns on the real AI. Until it's done, Ask falls back to deterministic engine text and
leaf scan shows the visual self-check guide. **Both of those are working features, not errors** — so
if this part fails, your demo still works.

### B1. Install the Supabase CLI

It is not currently installed. Pick one:

```bash
npm install -g supabase
```

If that errors, use Scoop instead:

```bash
scoop install supabase
```

Verify:

```bash
supabase --version
```

### B2. Log in and link

```bash
supabase login
```

That opens a browser. Then, from the repo root (`clone_latest/prahari`):

```bash
supabase link --project-ref muuyogxmaoiybeadmxvr
```

If it asks for the database password, it's in Supabase → **Settings → Database**.

### B3. Give the functions the Gemini key

The key must live **only** on the server. Copy the value of `GEMINI_API_KEY` from your `.env`:

```bash
supabase secrets set GEMINI_API_KEY=paste_your_gemini_key_here
```

Confirm it registered (this prints a digest, not the key):

```bash
supabase secrets list
```

### B4. Deploy both functions

```bash
supabase functions deploy ask
```

```bash
supabase functions deploy leaf-scan
```

Do **not** pass `--no-verify-jwt`. The app sends the anon key as a Bearer token, which is a valid
JWT, so default verification works and keeps the functions from being open to the world.

### B5. Test `ask` before trusting the UI

Replace `<ANON>` with `SUPABASE_ANON_KEY` from your `.env`:

```bash
curl -s -X POST "https://muuyogxmaoiybeadmxvr.supabase.co/functions/v1/ask" -H "Content-Type: application/json" -H "Authorization: Bearer <ANON>" -H "apikey: <ANON>" -d "{\"lang\":\"hi\",\"question\":\"मेरे खेत में क्या करना है?\",\"facts\":{\"band\":\"act\",\"crop\":\"potato\",\"dsv_accum_7d\":21,\"wet_hours\":13,\"min_temp_c\":11.2,\"mean_wet_temp_c\":17.4,\"confidence\":0.84}}"
```

**Reading the result:**

| Response | Meaning | Action |
|---|---|---|
| `{"text":"…Hindi sentence…"}` | Working. | Done. |
| `{"text":null,"reason":"no_api_key"}` | B3 didn't take. | Redo B3, redeploy B4. |
| `{"text":null,"reason":"gate:…"}` | Gemini replied but the §27.5 safety gate rejected it (invented a number, named a chemical, or contradicted the band). | **This is correct behaviour.** Run it again; the app falls back to engine text meanwhile. |
| `{"text":null,"reason":"gemini_http_429"}` | Free-tier rate limit. | Wait a minute. |
| `401` | Wrong anon key. | Recopy from `.env`. |

---

## Part C — Frontend on Vercel (10 min)

### C1. Push your code

```bash
git push mine main
```

### C2. Import the project

1. <https://vercel.com/new> → import **M-Ibrahim-03/Prahari**.
2. Leave every build setting **untouched**. `vercel.json` already sets the install command, build
   command (`cd web && npm run build`), output directory (`web/dist`), the SPA rewrite that
   deliberately excludes `/artefacts/`, and the cache headers.
3. Do **not** click Deploy yet — set the env vars first (C3), or the first build ships a keyless app.

### C3. Set the three browser environment variables

Vercel → **Project → Settings → Environment Variables**. Add exactly these three, for
**Production, Preview and Development**:

| Name | Value | Why |
|---|---|---|
| `MAPTILER_KEY` | from `.env` | map tiles |
| `SUPABASE_URL` | from `.env` | reaching the edge functions |
| `SUPABASE_ANON_KEY` | from `.env` | authenticating to them |

**Add nothing else.** `GEMINI_API_KEY`, `SUPABASE_SERVICE_KEY` and `OPENTOPO_KEY` must never be set
here — anything in this list can be inlined into a JavaScript file every visitor downloads. The
Gemini key belongs only in `supabase secrets set` (B3).

These are read by `web/vite.config.ts` through an explicit allowlist, so the names must match
exactly — no `VITE_` prefix.

### C4. Deploy

Click **Deploy**. Then verify the keys actually made it in — open the deployed site and run this in
the browser console:

```js
fetch('/artefacts/farrukhabad/fields.json').then(r=>r.json()).then(d=>console.log(d.prahari.market?.momentum, d.prahari.water?.band))
```

Should print something like `rising wet`. If the site loads but the map is grey, `MAPTILER_KEY`
didn't reach the build — check C3 and **redeploy** (env var changes need a new build; they are
compiled in, not read at runtime).

---

## Part D — Nightly artefact refresh (2 min, optional)

Artefacts are committed to the repo and served as static files, so the demo works without this. To
let the nightly workflow commit fresh forecasts:

1. GitHub → your repo → **Settings → Actions → General**.
2. Under **Workflow permissions**, select **Read and write permissions** → Save.

Without this, `nightly.yml` runs but cannot push the artefact, and the demo silently keeps showing
the last committed forecast.

To refresh by hand instead:

```bash
python -m pipeline.nightly
```

```bash
cp -rf artefacts/farrukhabad* web/public/artefacts/ && git add -A && git commit -m "refresh artefact" && git push mine main
```

---

## Demo script (2 minutes, in this order)

1. **Today** — real live forecast. Point at the confidence chip and the data-age line.
2. Scroll to **खेत की और जानकारी** — the FAO-56 irrigation index and the mandi table. Say the line
   that lands: *Agra quotes the highest price at ₹1,340/quintal but nets the least (₹19,240); selling
   at home for ₹1,160 nets ₹23,020, because freight eats the difference.* The app warns about this.
3. Switch the top dropdown to **डेमो: झुलसा प्रकोप**. Note the red banner that says *this is not a
   real forecast* — the app refuses to let synthetic weather pass as real.
4. **छिड़काव (Spray)** — the spray window, with the reason it is bounded.
5. **पूछें (Ask)** — a question. Answer text is either Gemini-rephrased or engine-generated; either
   way the numbers came from the engine, never the model.
6. **Trust** — the hash-chained alert ledger, verified in the browser.
7. Tap **⚠️ यह गलत है** on a card to show the farmer-feedback path.

---

## If a judge asks what isn't built

Answer plainly; the deck promises more than the build has:

- **Index 3 (Soil Health Card + NDVI nutrients)** — not built. Needs Copernicus registration.
- **Bhashini / 22 languages** — Hindi and English only, via keyless `edge-tts`. Bhashini is free but
  needs a signup.
- **SMS / IVR** — not built. Needs a paid gateway, and the budget for this build was ₹0.
- **On-device MobileNetV2** — leaf scan calls Gemini Vision server-side, not a browser CNN.
- **1 km² resolution** — true of the disease grid only. Irrigation and price are district-level, and
  the UI says so on screen.

---

## After the hackathon

**Rotate every key**: Gemini, Supabase service key, MapTiler, OpenTopo. They have been in a local
`.env` and used across many sessions.
