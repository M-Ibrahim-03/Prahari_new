# Deploying PRAHARI to Vercel (free)

Static site, zero rupees: Vercel **Hobby**, MapTiler **Free**, Supabase **Free**. No serverless
functions, no cron on Vercel, nothing that needs a paid plan.

The "server" stays GitHub Actions. `.github/workflows/nightly.yml` runs the pipeline at 02:00 IST
and **commits** `artefacts/`; that commit triggers a Vercel rebuild, and that is the only way a new
forecast reaches a farmer's phone. Vercel just serves files.

---

## 1. Prerequisites

- This repo pushed to GitHub (Vercel deploys from git).
- A Vercel account on the free **Hobby** plan — log in with GitHub.
- Your `MAPTILER_KEY` (it is already in the gitignored root `.env`).
- Node 20+ locally, only for the pre-flight build below.

### Pre-flight: prove the build works locally before you trust the cloud

The artefacts must be **in git**. They are committed on purpose (see `.gitignore`):

```bash
git ls-files artefacts | head
```

If that prints nothing, stop — the deploy will have a working app and no data.

```bash
cd web && npm ci
```

```bash
cd web && npm run build
```

```bash
ls web/dist/artefacts/farrukhabad
```

That must list `fields.json` and `today.geojson`. This is `closeBundle()` in `web/vite.config.ts`
copying `../artefacts` into `dist`. **If this directory is empty locally, it will be empty in
production too, and every field card will fail to load.**

```bash
git push
```

---

## 2. What `vercel.json` already configures — do not re-enter it in the dashboard

Repo root `vercel.json` sets:

| Setting | Value |
|---|---|
| Framework Preset | `null` ("Other") |
| Install Command | `cd web && npm ci` |
| Build Command | `cd web && npm run build` |
| Output Directory | `web/dist` |

### 🔴 Leave Root Directory EMPTY. Do not set it to `web`.

This is the single setting that silently ships a data-less site. Vercel's docs on Root Directory:
*"Your app will not be able to access files outside of that directory. You also cannot use `..` to
move up a level."*

`closeBundle()` copies `path.resolve(__dirname, '..', 'artefacts')`. With Root Directory = `web`,
that path is outside the sandbox, so `fs.existsSync(ARTEFACTS)` is simply `false` — the copy is
**skipped without an error**. The build goes green, the shell deploys, the map draws, and every
artefact request 404s. Nothing in the build log hints at it.

So: repo root stays the project root, and the build reaches into `web/` from there. That is why the
build command is a root-level `buildCommand` and not the Root Directory setting.

(`vercel.json` is read from the project root, which is another reason to keep the root as-is —
with Root Directory = `web`, Vercel would look for `web/vercel.json` and this file would be
ignored entirely, including the rewrite rule below.)

---

## 3. HUMAN STEPS — you must do these by hand, in a browser

Nothing in this section can be scripted. Steps 3.2 and 3.3 must both be done **before** you give
the URL to anyone.

### 3.1 Import the project

1. Go to **vercel.com/new** and pick this GitHub repo.
2. Framework Preset will say **Other**. Leave it.
3. Open **Build and Output Settings** — the fields should be greyed out / prefilled from
   `vercel.json`. Do not override them.
4. **Root Directory: leave blank** (see §2). If the import UI pre-selected `web`, clear it.
5. Add the environment variables (3.2) *before* clicking Deploy, or you will need a redeploy.
6. Deploy.

### 3.2 Set the environment variables (Settings → Environment Variables)

Add these three, ticked for **Production, Preview and Development**:

| Name | Value |
|---|---|
| `MAPTILER_KEY` | your MapTiler key |
| `SUPABASE_URL` | `https://<project>.supabase.co` |
| `SUPABASE_ANON_KEY` | your Supabase **anon** key |

Plain names, no `VITE_` prefix: `web/vite.config.ts` reads the root `.env` **and** `process.env`
with an empty prefix, then hand-picks what the browser may see.

**These three are the only variables that may ever reach a browser bundle.**
- `MAPTILER_KEY` is browser-safe *only once domain-restricted* (3.3).
- `SUPABASE_ANON_KEY` is browser-safe *only with Row Level Security on* — that is what
  `supabase/schema.sql` (3.4) turns on.

### 🔴 `GEMINI_API_KEY` and `SUPABASE_SERVICE_KEY` must NEVER be added to Vercel.

The service key bypasses RLS; the Gemini key is billable. This deployment is **100% static** — no
function ever runs on Vercel, so a secret added here cannot be used by anything except the build,
where its only possible destination is the JavaScript bundle. It would buy you nothing and leak
everything. Those two live in the gitignored root `.env` locally and in **GitHub Secrets** for the
pipeline, and nowhere else.

Two things stop an accidental leak today, and both need to keep working: the explicit allowlist in
`web/vite.config.ts` (`define: { __MAPTILER_KEY__ }` only — never switch to Vite's `VITE_*`
prefix convention), and this rule.

After changing any env var: **Deployments → ⋯ → Redeploy**. Values are inlined at build time, so an
env var added after the build has no effect until you rebuild.

> Note: `SUPABASE_URL` / `SUPABASE_ANON_KEY` are set now so the deploy is ready for the feedback
> feature, but the web app does not read them yet — they are not in the `define` allowlist in
> `web/vite.config.ts`. Setting them changes nothing visible. That is expected, not a bug.

### 3.3 Restrict the MapTiler key to the deployed domain — BEFORE the site is public

1. Copy your production domain from Vercel, e.g. `prahari.vercel.app` (no `https://`, no path).
2. MapTiler Cloud → **Keys** → your key → **Allowed origins / HTTP referrers**.
3. Add `https://prahari.vercel.app/*` — plus `http://localhost:5173/*` so local dev keeps working.
4. Save.

An unrestricted key on a public URL is **someone else's free quota**: the key is visible in the
JS bundle to anyone who opens DevTools, and the free tier is a monthly tile allowance that a
scraper can drain in an afternoon. Then the judges' demo shows a blank map.

Preview deployments get random `*-git-*.vercel.app` domains that will **not** match the
restriction, so previews show a blank map. That is correct behaviour — demo from production.

### 🔴 Do not add a `Referrer-Policy` header to `vercel.json`.

MapTiler enforces the domain restriction using the `Referer` header the browser sends with each
tile request. A `Referrer-Policy: no-referrer` (or `same-origin`) would strip it, MapTiler would
reject every tile with 403, and the map would go blank with no console error that names the cause.
The browser default (`strict-origin-when-cross-origin`) sends exactly the origin MapTiler needs.

### 3.4 Run the Supabase schema

1. Supabase dashboard → your project → **SQL Editor** → **New query**.
2. Paste the entire contents of `supabase/schema.sql` from this repo.
3. **Run**. Confirm it ends without an error and that RLS is enabled on the new tables
   (Table Editor shows a padlock).

The anon key you put in Vercel is only safe because of the policies in that file. If
`supabase/schema.sql` does not exist in the repo yet, skip this step — it lands with the feedback
feature, and everything else on the site works without it.

---

## 4. Verify the deploy actually works

Set your domain once (Git Bash on Windows is fine):

```bash
SITE=https://prahari.vercel.app
```

### 4.1 The artefact loads

```bash
curl -sS "$SITE/artefacts/farrukhabad/fields.json" | head -c 120
```

Expect JSON starting `{"prahari":{"schema_version":"2.0.0"`. If you get `<!doctype html>`, the
rewrite is wrong (§7.2). If you get a 404 page, the artefacts never made it into `dist` (§7.1).

### 4.2 🔴 A missing artefact returns 404 — the test that matters most

```bash
curl -sS -o /dev/null -w '%{http_code} %{content_type}\n' "$SITE/artefacts/audio/definitely_missing.mp3"
```

**Expect the status code `404`** (the content type will be Vercel's own HTML error page,
`text/html; charset=utf-8` — that part does not matter). Any **`200`** here means the SPA catch-all
is swallowing missing artefacts and the voice feature is silently broken — see §5.

### 4.3 A real clip is served as audio, and deep links still work

```bash
curl -sSI "$SITE/artefacts/audio/safe_hi_ba31.mp3"
```

Expect `200`, `content-type: audio/mpeg`, `cache-control: public, max-age=604800`. This is a HEAD
request — exactly what `clipExists()` in `web/src/lib/audio.ts` does, and it accepts the clip only
if the content type starts with `audio/`.

```bash
curl -sS -o /dev/null -w '%{http_code}\n' "$SITE/anything/not/a/real/file"
```

Expect `200` — non-artefact paths must still fall back to the app shell.

```bash
curl -sSI "$SITE/artefacts/farrukhabad/today.geojson" | grep -i content-type
```

Expect `application/geo+json; charset=utf-8`.

### 4.4 The map renders

Open `$SITE` on a phone and go to the map screen.

- Satellite tiles + field markers → done.
- Text **"MAPTILER_KEY missing from .env"** → the key was not in the environment *at build time*.
  Add it (3.2) and **redeploy**.
- Blank/grey tiles, no message → tiles are being refused. DevTools → Network → a request to
  `api.maptiler.com/tiles/...` returning **403** means the domain restriction (3.3) does not list
  this exact domain.

### 4.5 Audio plays

Tap **सुनें** on a field card. You should hear Hindi within about a second. With DevTools →
Network open, a pre-generated clip shows a `HEAD` then a `GET` of `/artefacts/audio/*.mp3`, both
`200`. If you instead hear the phone's own robotic voice (or see "आवाज़ उपलब्ध नहीं"), the clip
lookup failed — re-run 4.2 and 4.3.

### 4.6 Offline reload

1. Load `$SITE` once, fully.
2. DevTools → **Application → Service Workers**: `prahari-v1` is *activated and running*.
3. Turn on airplane mode (or DevTools → Network → **Offline**).
4. **Reload.**

The app must still render: shell from the service worker cache, fields from `localStorage`, and the
data-age banner honestly reporting how old the forecast is. A blank page means the service worker
never installed — check that `$SITE/sw.js` returns JavaScript, not HTML.

---

## 5. Why the rewrite rule looks like that

```json
{ "source": "/:path((?!artefacts/|assets/).*)", "destination": "/index.html" }
```

A single-page app needs unmatched paths to return `index.html`. The naive rule everyone writes —
`{"source": "/(.*)", "destination": "/index.html"}` — reintroduces a bug this codebase has already
been bitten by, and reintroduces it in production, where it is far harder to notice than in dev.

With a catch-all, a request for a **file that does not exist** does not 404. It returns
`index.html` with **HTTP 200**. So `/artefacts/audio/safe_hi_9999.mp3` looks like a successful
fetch: `res.ok` is `true`, the app concludes a pre-generated clip exists, hands HTML to
`new Audio()`, playback fails, and the device-speech fallback never runs. A farmer who cannot read
gets silence and no explanation. `web/vite.config.ts` has the same red-circle warning on the dev
middleware, which answers 404 itself instead of calling `next()`; `clipExists()` additionally
requires an `audio/` content type. This rewrite is the third layer, in the one environment that
actually matters.

The pattern is Vercel's own documented negative-lookahead form (their example is
`"/:path((?!uk/).*)"`), so it is a supported `source`, not a guess. Requests under `/artefacts/`
are excluded from the rewrite, so a missing one falls through to Vercel's default **404**.
Existing artefacts are unaffected either way — Vercel gives the filesystem precedence over
rewrites, which is also why `/sw.js` and `/manifest.webmanifest` are still served as real files
despite matching the pattern.

`assets/` is excluded for the same reason one step removed: Vite's content-hashed bundles live
there, and a stale service worker asking for a chunk that a new deploy has removed would otherwise
receive `index.html` with a `200` and cache HTML under a `.js` URL — a self-poisoning shell cache.
A 404 lets it fail loudly instead. The global `X-Content-Type-Options: nosniff` backs this up: a
browser will refuse to execute HTML delivered as a script rather than guessing.

Known and accepted: the bare path `/artefacts` (no trailing slash, a directory the app never
requests) still returns the shell. Only `/artefacts/...` is excluded.

---

## 6. Cache headers, and why each one

They must not contradict `web/public/sw.js`, whose header comment explains the split: shell and
audio are cache-first, artefacts are **network-first** because a forecast is time-sensitive.

| Path | `Cache-Control` | Why |
|---|---|---|
| `/artefacts/*` (not audio) | `public, max-age=0, must-revalidate` | 🔴 A long max-age on `today.geojson`/`fields.json` would serve **yesterday's forecast** from the browser's HTTP cache — the exact failure degradation L7 forbids. `must-revalidate` still allows a cheap `304`, which matters on 2G, but never serves unvalidated data. The app also fetches these with `cache: 'no-store'`; this header is the second line of defence for anything that does not. |
| `/artefacts/audio/*` | `public, max-age=604800` (7 days) | Medium on purpose. Keys are content-derived, so a cached clip cannot disagree with its key — but the key truncates the hash to 4 hex characters, and a district with a few hundred field names would reach the birthday bound. A week caps how long a colliding clip could be wrong; `immutable` for a year would not. The service worker caches these cache-first anyway, so repeat playback is free offline. |
| `/assets/*` | `public, max-age=31536000, immutable` | Vite content-hashes these; a cached asset can never be the wrong one, and a new build produces new filenames. This is the only long cache here, and it is what makes a repeat visit on 2G nearly instant. |
| `/sw.js`, `/manifest.webmanifest` | `public, max-age=0, must-revalidate` | A cached service worker cannot be replaced, so the app would be frozen at an old shell forever. Vercel's default is already this, but it is too important to leave implicit. |
| everything else (`index.html`) | Vercel default: `public, max-age=0, must-revalidate` | Navigations are network-first in the service worker; the HTTP layer must agree. |

Content types: Vercel very probably infers `audio/mpeg` and `application/geo+json` from the file
extension on its own, but both are pinned explicitly anyway, because `clipExists()` **gates the
whole voice feature on `content-type: audio/`**. That check must not depend on MIME inference
staying the way it is today, and 4.3 tells you within a second whether the pin took effect.
(`Content-Type` is not one of Vercel's reserved headers — only `x-matched-path`, `server` and
`content-length` are — so overriding it is supported.)

No `s-maxage` anywhere: every deployment is immutable and served from Vercel's edge already, so CDN
TTLs would add a second staleness dimension for no gain.

---

## 7. Troubleshooting

### 7.1 Most likely: the site loads but there is no data

Symptom: shell renders, the map draws, every field card errors or shows only cached data. 4.1
returns a 404 page.

```bash
curl -sS -o /dev/null -w '%{http_code}\n' "$SITE/artefacts/farrukhabad/fields.json"
```

`404` here, with the shell working, has exactly three causes, in order of likelihood:

1. **Root Directory is set to `web`.** Then `../artefacts` was unreachable during the build and
   `closeBundle()` skipped the copy silently (§2). Fix: Settings → Build and Deployment → Root
   Directory → clear it → Save → Redeploy. Nothing in the build log will have complained.
2. **`artefacts/` is not in git.** Fix: `git ls-files artefacts | head`. If that is empty,
   `git add artefacts && git commit -m "artefacts" && git push`.
3. **Output Directory was overridden in the dashboard.** A dashboard override wins over
   `vercel.json`. Clear it so `web/dist` from `vercel.json` applies.

Confirm the fix by re-running the curl above: it must return `200`.

### 7.2 A missing clip returns 200 instead of 404

Someone replaced the rewrite with a catch-all, or added a later rewrite that matches everything.
Re-read §5 and restore the negative-lookahead source. `vercel.json` must be at the **repo root**,
not in `web/` — if it is in the wrong place it is ignored entirely and Vercel's own SPA fallback
takes over.

### 7.3 Map is blank

See 4.4 — it is either the key missing from the build (needs a redeploy after adding the env var)
or a domain restriction that does not list this exact domain. Do not "fix" it by unrestricting the
key.

### 7.4 An old version keeps loading after a deploy

The previous service worker is serving its cached shell. It self-updates on the next load
(`skipWaiting` + `clients.claim`), so reload twice. To force it: DevTools → Application → Service
Workers → **Unregister**, then reload. If it happens on every deploy, check that `/sw.js` is not
being served with a long `max-age`.

### 7.5 Build fails: `tsc` or `vite` not found

The install command did not run in `web/`. Confirm `installCommand` is `cd web && npm ci` and that
`web/package-lock.json` is committed — `npm ci` requires the lockfile and fails without it.

### 7.6 Every curl returns 401

You are testing a **preview** URL. Vercel protects preview deployments with Vercel Authentication
by default, so `curl` gets a login page. Use the production domain for all of §4.
