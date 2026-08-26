import { useEffect, useState } from 'react'
import type { FieldPayload } from './types'

const CACHE_PREFIX = 'prahari:fields:v1'

/**
 * 🔴 The cache key includes the district. A single shared key looked fine while there was one
 * district, but the payload is per-district: switching (to another district, or to a demo
 * scenario, which is written under its own code) served the PREVIOUS district's fields
 * instantly and flagged them `fromCache`, so the app would confidently show a farmer someone
 * else's field names and bands. Cached data must be keyed by what it is data ABOUT.
 */
function cacheKey(district: string): string {
  return `${CACHE_PREFIX}:${district}`
}

export type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string; cached?: FieldPayload }
  | { status: 'ready'; data: FieldPayload; fromCache: boolean }

/**
 * Load the farmer's field payload.
 *
 * 🔴 Offline-first (PRD P6 / §28.3 L9): the last good payload is cached in localStorage and
 * served immediately, so the app is fully usable in airplane mode. Connectivity is an
 * enhancement that delivers fresh data, not a precondition for the product functioning.
 * When a fetch fails we fall back to cache and say so — we never show nothing, and we never
 * present cached data as if it were fresh (the age banner always states the artefact's age).
 */
export function useFieldPayload(district: string): LoadState {
  const [state, setState] = useState<LoadState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false

    // A district switch must not leave the previous district's cards on screen while the new
    // payload loads, so start from a clean slate rather than carrying stale state across.
    setState({ status: 'loading' })

    const cached = readCache(district)
    if (cached) setState({ status: 'ready', data: cached, fromCache: true })

    fetch(`/artefacts/${district}/fields.json`, { cache: 'no-store' })
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return (await r.json()) as FieldPayload
      })
      .then((data) => {
        if (cancelled) return
        writeCache(district, data)
        setState({ status: 'ready', data, fromCache: false })
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const message = err instanceof Error ? err.message : String(err)
        const fallback = readCache(district)
        if (fallback) setState({ status: 'ready', data: fallback, fromCache: true })
        else setState({ status: 'error', message })
      })

    return () => {
      cancelled = true
    }
  }, [district])

  return state
}

function readCache(district: string): FieldPayload | null {
  try {
    const raw = localStorage.getItem(cacheKey(district))
    return raw ? (JSON.parse(raw) as FieldPayload) : null
  } catch {
    return null
  }
}

function writeCache(district: string, data: FieldPayload) {
  try {
    localStorage.setItem(cacheKey(district), JSON.stringify(data))
  } catch {
    // Storage full or blocked — the app still works, it just won't survive a reload offline.
  }
}
