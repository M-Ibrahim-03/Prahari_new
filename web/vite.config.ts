import { defineConfig, loadEnv, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'

const ARTEFACTS = path.resolve(__dirname, '..', 'artefacts')

/**
 * Serve the repo's committed artefacts at /artefacts/* without duplicating them into
 * web/public. The nightly job (pipeline/nightly.py) is the single writer; the app is a
 * pure reader. On build, the directory is copied into dist so the deployed site is static.
 */
function artefacts(): Plugin {
  return {
    name: 'prahari-artefacts',
    configureServer(server) {
      server.middlewares.use('/artefacts', (req, res, next) => {
        const rel = decodeURIComponent((req.url || '/').split('?')[0])
        const file = path.join(ARTEFACTS, rel)
        // Keep the handler inside ARTEFACTS even if the URL contains traversal segments.
        if (!file.startsWith(ARTEFACTS)) return next()

        // 🔴 A missing artefact must answer 404, NOT fall through to next(). Vite's SPA fallback
        // answers unmatched paths with index.html and HTTP 200, so calling next() here made a
        // non-existent audio clip look like a successful fetch — the app then believed a
        // pre-generated clip existed, tried to play HTML as audio, and never fell back to device
        // speech. A silent failure of the voice path is the worst possible degradation.
        if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
          res.statusCode = 404
          res.setHeader('Content-Type', 'application/json; charset=utf-8')
          res.end(JSON.stringify({ error: 'artefact_not_found', path: rel }))
          return
        }

        const type = file.endsWith('.json') ? 'application/json'
          : file.endsWith('.geojson') ? 'application/geo+json'
          : file.endsWith('.mp3') ? 'audio/mpeg'
          : 'application/octet-stream'
        // charset applies to text formats only — tagging binary audio with one is wrong and
        // some stricter clients reject it.
        const isText = type.startsWith('application/json') || type.startsWith('application/geo')
        res.setHeader('Content-Type', isText ? `${type}; charset=utf-8` : type)
        fs.createReadStream(file).pipe(res)
      })
    },
    closeBundle() {
      if (fs.existsSync(ARTEFACTS)) {
        fs.cpSync(ARTEFACTS, path.resolve(__dirname, 'dist', 'artefacts'), { recursive: true })
      }
    },
  }
}

export default defineConfig(({ mode }) => {
  // Read the repo-root .env (the single place keys live) rather than duplicating it into web/.
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')

  // 🔴 loadEnv reads .env FILES ONLY — it never looks at process.env. On a CI or hosting platform
  // (Vercel, GitHub Actions) there is no .env file because .env is gitignored, and the keys arrive
  // as real environment variables instead. Without this fallback every value below would be '' in
  // production: the map would render keyless, aiConfigured() would return false so Ask and
  // leaf-scan could never reach the edge functions, and every feedback write would be dropped —
  // all of it silently, because '' is a valid string and nothing would throw.
  const fromEnv = (name: string): string => env[name] ?? process.env[name] ?? ''

  // 🔴 EXPLICIT ALLOWLIST — do not switch this to Vite's VITE_* convention.
  // With a prefix convention, any future variable that happens to be prefixed is shipped to the
  // browser automatically; the root .env also holds the Supabase SERVICE key and the Gemini key,
  // which must never reach a client. Naming each exposed variable here means adding a browser
  // secret takes a deliberate edit to this line, which is reviewable.
  //
  // MapTiler is domain-restricted in the MapTiler dashboard rather than kept secret — see README
  // (human step before any public deploy).
  //
  // SUPABASE_ANON_KEY is likewise public BY DESIGN: it is a JWT carrying the role "anon", and what
  // makes it safe is not secrecy but the Row Level Security policies in supabase/schema.sql, which
  // permit anon to INSERT feedback and device rows and nothing else. 🔴 With RLS disabled this key
  // is a public read-and-write handle to the whole database, so the schema migration and this line
  // are a pair — shipping the key without running the migration is the failure mode.
  //
  // 🔴 SUPABASE_SERVICE_KEY and GEMINI_API_KEY must NEVER appear in this object. The service key
  // bypasses RLS entirely, and anything named here is inlined verbatim into a JavaScript file that
  // every visitor downloads. There is no such thing as a hidden value in a browser bundle.
  const browserEnv = {
    __MAPTILER_KEY__: JSON.stringify(fromEnv('MAPTILER_KEY')),
    __SUPABASE_URL__: JSON.stringify(fromEnv('SUPABASE_URL')),
    __SUPABASE_ANON_KEY__: JSON.stringify(fromEnv('SUPABASE_ANON_KEY')),
  }

  // 🔴 Fail loudly at BUILD time, not silently at runtime in a farmer's hand. A production build
  // with an empty Supabase URL still runs — it just quietly has no AI and no feedback path, which
  // is the hardest class of bug to notice from a screenshot. Dev builds stay permissive so the app
  // works offline with no keys at all.
  if (mode === 'production') {
    const missing = Object.entries(browserEnv)
      .filter(([, v]) => v === '""')
      .map(([k]) => k.replace(/^__|__$/g, ''))
    if (missing.length) {
      console.warn(
        `\n⚠️  PRAHARI build: missing browser env [${missing.join(', ')}].\n` +
          `   The app will build and run, but features depending on them are disabled:\n` +
          `   MAPTILER_KEY -> map tiles, SUPABASE_URL/SUPABASE_ANON_KEY -> Ask, leaf scan, feedback.\n` +
          `   Set them in the host's environment settings (Vercel: Project -> Settings -> Environment Variables).\n`,
      )
    }
  }

  return {
    plugins: [react(), artefacts()],
    server: { port: 5173 },
    define: browserEnv,
  }
})
