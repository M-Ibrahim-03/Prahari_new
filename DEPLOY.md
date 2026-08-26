# PRAHARI — Demo Deployment, Step by Step

Exact commands for a working public demo. Follow the parts **in order** — A must finish before C,
because C publishes the anon key to the browser and A is what makes that key safe.

Your Supabase project ref is **`muuyogxmaoiybeadmxvr`**. This is public information — it is inside
the URL that ships in the browser bundle.

Total time: about **35 minutes**. Everything here is free tier. **Nothing in this guide costs money.**

## What you're doing, at a glance

| Part | What | Where | Required? |
|---|---|---|---|
| **A** | Database tables + Row Level Security | Supabase dashboard, browser | **Yes** — before C |
| **B** | Deploy 2 edge functions, set the Gemini secret | Terminal | Optional; app degrades honestly without it |
| **C** | Frontend build + 3 env vars | Vercel dashboard | **Yes** |
| **D** | Nightly forecast refresh | GitHub settings | Optional |

Before you start, confirm you have all four keys locally. From `clone_latest/prahari`:

```bash
grep -oE '^(GEMINI_API_KEY|SUPABASE_URL|SUPABASE_ANON_KEY|SUPABASE_SERVICE_KEY|MAPTILER_KEY)' .env | sort
```

You need at minimum `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `MAPTILER_KEY` (for Part C) and
`GEMINI_API_KEY` (for Part B). If `.env` is missing, see step A1.

---

## Part A — Database schema + RLS (8 min, browser only)

**Why this part comes first:** Part C publishes `SUPABASE_ANON_KEY` inside a JavaScript file that
every visitor downloads. That is by design — it is a JWT carrying the role `anon`, and what makes it
safe is not secrecy, it is the Row Level Security policies you are about to create. Ship the key
before the policies exist and it becomes a public read-and-write handle to your whole database.

### A0. Open the right project

1. Go to <https://supabase.com/dashboard> and log in.
2. Click your project. Look at the browser address bar — it must read
   `.../project/muuyogxmaoiybeadmxvr`. If it shows a different ref, you are in the wrong project
   and everything below will land in the wrong place.

### A1. Get your keys into `.env` (skip if `.env` already has them)

Your `.env` at the repo root should already contain `SUPABASE_URL` and `SUPABASE_ANON_KEY`. To
check, from `clone_latest/prahari`:

```bash
grep -c SUPABASE_ANON_KEY .env
```

`1` means it's there. If you get `0`, fetch them from the dashboard:

1. Left sidebar → the gear icon (**Project Settings**) → **API Keys** (older dashboards call this
   page **API**).
2. **Project URL** → this is `SUPABASE_URL`. It looks like
   `https://muuyogxmaoiybeadmxvr.supabase.co` — no trailing slash.
3. The **`anon` / `public`** key (newer dashboards label it **publishable**) → this is
   `SUPABASE_ANON_KEY`. It is a long string starting `eyJ`.
4. 🔴 On the same page there is a **`service_role`** / **secret** key. **Do not copy that one into
   anything the browser touches.** It bypasses RLS completely. It belongs only in `.env` as
   `SUPABASE_SERVICE_KEY`, used by the Python pipeline on your machine.

### A2. Run the schema

1. Left sidebar → **SQL Editor**.
2. Click **+ New query** (top left of that pane).
3. In this repo open `supabase/schema.sql`. Select **all** of it (Ctrl+A) and copy (Ctrl+C).
4. Click into the empty SQL editor box and paste (Ctrl+V).
5. Click **Run** (bottom right, or Ctrl+Enter).
6. Expected result: a green **Success. No rows returned**.

The file is written to be re-runnable — every `create policy` is preceded by
`drop policy if exists`, so if you pasted an older version earlier, just run this one again. It
does not delete data.

**If you get an error instead:**

| Error text | Cause | Fix |
|---|---|---|
| `policy "…" for table "…" already exists` | You ran an **old** copy of the file. | Make sure you copied the current `supabase/schema.sql` from this repo — it has the `drop policy` lines. Re-run. |
| `permission denied` | You are logged in as a non-owner member. | Use the account that owns the project. |
| `relation "…" does not exist` | Only part of the file got pasted. | Ctrl+A in the editor, delete, re-paste the **whole** file. |

### A3. Verify the four things that must be true

Do not skip this. Each of these was a real bug at some point in the build.

**Check 1 — the tables exist.** New query, paste, Run:

```sql
select table_name from information_schema.tables
where table_schema='public' order by table_name;
```

You must see at least: `cell_feedback_k5`, `devices`, `feedback`, `ledger_records`.

**Check 2 — RLS is actually on.** This is the one that protects you:

```sql
select tablename, rowsecurity from pg_tables
where schemaname='public' and tablename in ('devices','feedback','ledger_records');
```

All three rows must show `rowsecurity = true`. 🔴 **If any row shows `false`, stop here.** Re-run
A2 and re-check. Do not do Part C until all three are `true`.

**Check 3 — anon can write feedback but not read it back.** The app's whole feedback path depends
on the first, and farmer privacy depends on the second:

```sql
select
  has_table_privilege('anon','feedback','insert') as can_insert,
  has_table_privilege('anon','devices','insert')  as can_add_device,
  has_table_privilege('anon','cell_feedback_k5','select') as can_read_aggregate;
```

All three must be `true`. `can_read_aggregate` is the k≥5 view — the view had no `GRANT` at one
point, which silently made it unreadable.

**Check 4 — an anonymous insert really works.** This simulates exactly what a farmer's phone does.
It runs inside a transaction that rolls back, so it leaves no test row behind:

```sql
begin;
set local role anon;
insert into feedback (idempotency_key, device_hash, district, cell_id, field_ref, run_id, feedback_type)
values ('deploy-test-1', 'deploy-test-device', 'farrukhabad', 'c1', 'f1', '2026-08-26T00:00:00Z', 'false_alarm');
select count(*) as rows_anon_can_read from feedback;
reset role;
rollback;
```

Two things must both happen:
- the `insert` **succeeds** — that's the ⚠️ यह गलत है button working;
- `rows_anon_can_read` comes back **`0`** — anon may submit feedback but must never read anyone
  else's. If that number is greater than 0, the `No public read on individual feedback` policy
  didn't apply; re-run A2.

If the insert fails with `new row violates row-level security policy`, the insert policy is missing —
re-run A2.

✅ **Part A is done.** Your database is now safe to point a public app at.

---

## Part B — Edge Functions: the real AI (12 min, terminal)

This is what turns Gemini on. **If this part fails your demo still works** — Ask falls back to
deterministic engine text and leaf scan shows the visual self-check guide, both of which are real
shipped features, not error screens. So do Part C even if B goes wrong.

Two functions get deployed:

| Function | What it does | Called from |
|---|---|---|
| `ask` | Rephrases the engine's verdict into natural Hindi/English. It may **only** rephrase — the §27.5 gate rejects any reply that invents a number, names a chemical, or contradicts the band. | 🎤 पूछें button |
| `leaf-scan` | Gemini Vision looks at a leaf photo and returns one of four labels. Spray timing still comes from the weather engine, never the photo. | 📸 पत्ती जाँच button |

### B1. Install the Supabase CLI

It is **not** installed on this machine right now. Open a terminal (Git Bash) and run:

```bash
npm install -g supabase
```

Then confirm — you should see a version number like `2.115.0`:

```bash
supabase --version
```

**If `npm install -g` fails** (permissions, or npm refuses to install the binary), use Scoop:

```bash
powershell -c "irm get.scoop.sh | iex"
```

```bash
scoop install supabase
```

**If you don't want to install anything at all**, put `npx ` in front of every `supabase` command
below (e.g. `npx supabase login`). It works, it's just slower each time, and the first call will
ask you to confirm the download — answer `y`.

### B2. Move into the project folder

Every command from here must run from the repo root, the folder that contains the `supabase/`
directory:

```bash
cd "C:/Users/muham/OneDrive/Desktop/Test/claudeproj/clone_latest/prahari"
```

Confirm you're in the right place — this must print `functions` and `schema.sql`:

```bash
ls supabase
```

### B3. Log in

```bash
supabase login
```

This prints a URL and opens your browser. Approve it, copy the token it shows if it asks, paste it
back into the terminal. Confirm it worked — this should list your project:

```bash
supabase projects list
```

### B4. Link this folder to your project

```bash
supabase link --project-ref muuyogxmaoiybeadmxvr
```

- It may ask for your **database password**. That is *not* your Supabase login password. Find it at
  Dashboard → gear icon → **Database** → **Database password** → **Reset database password** if you
  never saved it.
- Linking is only needed once; it writes `supabase/.temp/`, which is gitignored.

### B5. Store the Gemini key **on the server only**

🔴 This is the most important line in the whole guide. The Gemini key must never appear in Vercel,
never in `web/`, never in `vite.config.ts`. It goes here and nowhere else.

Open `.env`, copy the value after `GEMINI_API_KEY=` (starts with `AIza`), and run:

```bash
supabase secrets set GEMINI_API_KEY=paste_the_AIza_value_here
```

No quotes needed, no spaces around the `=`. Confirm it registered — this prints a hash digest, not
the key itself:

```bash
supabase secrets list
```

You should see a row named `GEMINI_API_KEY`.

### B6. Deploy the two functions

```bash
supabase functions deploy ask
```

Wait for `Deployed Functions on project muuyogxmaoiybeadmxvr: ask`. Then:

```bash
supabase functions deploy leaf-scan
```

Notes:
- 🔴 Do **not** add `--no-verify-jwt`. The app already sends the anon key as a Bearer token, which
  is a valid JWT, so the default works — and it stops the internet at large from burning your free
  Gemini quota.
- If it says `Docker is not running`: you don't need Docker for deploys. Add `--use-api`:
  `supabase functions deploy ask --use-api`.
- Both functions read `GEMINI_API_KEY` at request time, so if you ever change the secret you do
  **not** need to redeploy.

### B7. Prove `ask` works before you trust the UI

Set your anon key as a shell variable once so the next two commands stay readable:

```bash
ANON=$(grep '^SUPABASE_ANON_KEY=' .env | cut -d= -f2-)
```

Then call the function exactly the way the app does:

```bash
curl -s -X POST "https://muuyogxmaoiybeadmxvr.supabase.co/functions/v1/ask" -H "Content-Type: application/json" -H "Authorization: Bearer $ANON" -H "apikey: $ANON" -d '{"lang":"hi","question":"मेरे खेत में क्या करना है?","facts":{"band":"act","crop":"potato","dsv_accum_7d":21,"wet_hours":13,"min_temp_c":11.2,"mean_wet_temp_c":17.4,"confidence":0.84}}'
```

**Reading the result:**

| Response | Meaning | What to do |
|---|---|---|
| `{"text":"…a Hindi sentence…"}` | ✅ Working. Gemini answered and the safety gate passed it. | Nothing. Move on. |
| `{"text":null,"reason":"no_api_key"}` | B5 didn't take. | Redo B5, then redo B6. |
| `{"text":null,"reason":"gate:chemical:mancozeb"}` | Gemini named a fungicide. Blocked. | ✅ **The system working.** Retry for a passing sample. |
| `{"text":null,"reason":"gate:invented_number:400"}` | Gemini produced a figure that wasn't in the input facts. Blocked. | ✅ Same — retry. |
| `{"text":null,"reason":"gate:dose_pattern"}` / `gate:ppe_or_reentry` / `gate:band_contradiction:act` | A dose, a PPE instruction, or advice contradicting the band. Blocked. | ✅ Same — retry. |
| `{"text":null,"reason":"gemini_http_429"}` | Free-tier rate limit. | Wait 60 seconds, retry. |
| `{"text":null,"reason":"gemini_http_400"}` | Key present but invalid, or the Generative Language API isn't enabled for it. | Re-copy from <https://aistudio.google.com/apikey>, redo B5 and B6. |
| `{"text":null,"reason":"gemini_http_403"}` | Key is restricted (referrer/IP limits). | Make a fresh unrestricted key, redo B5. |
| `{"code":401,"message":"Invalid JWT"}` | Wrong anon key. | Check `echo $ANON` prints a long `eyJ…` string. |
| `{"code":404}` | Function name typo, or B6 didn't finish. | Run `supabase functions list`; both `ask` and `leaf-scan` must appear. |

🔴 Any `gate:` reason is a **pass**, not a failure. It is the §27.5 output gate refusing to let a
language model change a number, name a chemical, or flip a verdict. In the app the user never sees an
error — they get the engine's own deterministic sentence instead, and the screen marks rung L4.

### B8. Prove `leaf-scan` is reachable

You don't need a real photo to check the plumbing — send a 1-pixel PNG:

```bash
curl -s -X POST "https://muuyogxmaoiybeadmxvr.supabase.co/functions/v1/leaf-scan" -H "Content-Type: application/json" -H "Authorization: Bearer $ANON" -H "apikey: $ANON" -d '{"lang":"hi","image":"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="}'
```

Any JSON back that mentions `label` or `uncertain` means the function is live and the key works —
a blank pixel *should* come back `uncertain`, which is the honest answer. A `404` means B6 didn't
complete for this function.

### B9. Watch the logs (only if something is wrong)

Dashboard → **Edge Functions** → click `ask` → **Logs**. Or:

```bash
supabase functions logs ask
```

✅ **Part B is done.** The AI is live.

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
