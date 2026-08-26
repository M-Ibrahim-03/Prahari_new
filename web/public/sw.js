/*
 * PRAHARI offline shell (§28.3, degradation L4).
 *
 * 🔴 The caching strategy is DIFFERENT per resource type, and that difference is the whole point:
 *
 *   app shell      cache-first    — Vite content-hashes these; a cached asset is never wrong.
 *   audio clips    cache-first    — keys are content-addressed (sha of the text), so a cached
 *                                   clip cannot disagree with its key.
 *   artefacts      NETWORK-FIRST  — a forecast is time-sensitive. Serving yesterday's JSON from
 *                                   cache without trying the network first would let the app
 *                                   present stale data as current, which is exactly the failure
 *                                   L7 forbids. We fall back to cache only after the network
 *                                   actually fails, and the payload's run_id then drives the
 *                                   visible "old data" banner.
 *
 * Cache-first for artefacts would be faster and would look identical in a demo. It is still wrong.
 */

const VERSION = 'prahari-v1'
const SHELL_CACHE = `${VERSION}-shell`
const DATA_CACHE = `${VERSION}-data`
const AUDIO_CACHE = `${VERSION}-audio`

const SHELL_URLS = ['/', '/index.html', '/manifest.webmanifest', '/icon.svg']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      // Individual misses must not fail the whole install.
      .then((c) => Promise.allSettled(SHELL_URLS.map((u) => c.add(u))))
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const req = event.request
  if (req.method !== 'GET') return

  const url = new URL(req.url)
  if (url.origin !== self.location.origin) return

  if (url.pathname.startsWith('/artefacts/audio/')) {
    event.respondWith(cacheFirst(req, AUDIO_CACHE))
    return
  }
  if (url.pathname.startsWith('/artefacts/')) {
    event.respondWith(networkFirst(req, DATA_CACHE))
    return
  }
  if (req.mode === 'navigate') {
    event.respondWith(networkFirst(req, SHELL_CACHE).catch(() => caches.match('/index.html')))
    return
  }
  event.respondWith(cacheFirst(req, SHELL_CACHE))
})

async function cacheFirst(req, cacheName) {
  const cache = await caches.open(cacheName)
  const hit = await cache.match(req)
  if (hit) return hit
  const res = await fetch(req)
  if (res && res.ok) cache.put(req, res.clone())
  return res
}

async function networkFirst(req, cacheName) {
  const cache = await caches.open(cacheName)
  try {
    // cache: 'no-store' on the network leg so an HTTP-cached copy cannot masquerade as a fresh
    // fetch; the SW cache is the only fallback layer we want.
    const res = await fetch(req, { cache: 'no-store' })
    if (res && res.ok) cache.put(req, res.clone())
    return res
  } catch (err) {
    const hit = await cache.match(req)
    if (hit) return hit
    throw err
  }
}
