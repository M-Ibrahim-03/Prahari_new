/**
 * Advisory playback.
 *
 * 🔴 §14.2 pre-generation law: audio is generated in the nightly job, never at request time.
 * So the preferred path is a cached clip at /artefacts/audio/<key>.mp3, played back-to-back
 * (field name first, then the shared advice body — see engine/advisory.py on why it's split).
 *
 * When those clips do not exist yet, we fall back to the device's own speech synthesis. That is
 * degradation level L5 (§28.3: "TTS unavailable -> text + generic clip"), and the UI labels it
 * as such rather than pretending it is the real voice pipeline. Text is ALWAYS available
 * alongside audio (FR-8.9), so a failure here never blocks the advisory.
 */

export type AudioMode = 'pregenerated' | 'device_speech' | 'unavailable'

const clipCache = new Map<string, boolean>()
let current: HTMLAudioElement | null = null

/** Rough spoken duration. Shared with the play button so the label and the watchdog agree. */
export function estimateSeconds(text: string): number {
  const words = text.trim().split(/\s+/).length
  return Math.max(5, Math.round((words / 2.2) * 10) / 10) // ~2.2 words/sec at rate 0.9
}

/**
 * 🔴 `res.ok` alone is NOT enough. Static hosts with an SPA fallback (Vite's dev server, Vercel,
 * Netlify) answer a missing path with index.html and HTTP 200. Trusting `ok` therefore made every
 * non-existent clip look present: the app reported "pre-generated audio" and tried to play HTML,
 * so the voice failed with no fallback and no explanation. Require an audio content type, so a
 * missing clip is detected as missing on any host.
 */
async function clipExists(key: string): Promise<boolean> {
  if (clipCache.has(key)) return clipCache.get(key)!
  let ok = false
  try {
    const r = await fetch(`/artefacts/audio/${key}.mp3`, { method: 'HEAD' })
    const type = r.headers.get('content-type') ?? ''
    ok = r.ok && type.startsWith('audio/')
  } catch {
    ok = false
  }
  clipCache.set(key, ok)
  return ok
}

function playClip(key: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const el = new Audio(`/artefacts/audio/${key}.mp3`)
    current = el
    el.onended = () => resolve()
    el.onerror = () => reject(new Error(`clip failed: ${key}`))
    void el.play().catch(reject)
  })
}

export function speechAvailable(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

/**
 * Speak text with the device engine. Resolves true only if the engine actually spoke.
 *
 * 🔴 Two engine behaviours make the naive "resolve on onend" version unusable:
 *   1. Some engines accept the utterance and then silently do nothing — common in Android WebView
 *      and on devices with no Hindi voice installed. Nothing is heard and onend never fires.
 *   2. onend is unreliable even on engines that do speak.
 * Either way the promise would never settle, leaving the play button stuck on "playing" forever
 * with no sound and no explanation. A silent stall is the worst possible failure for a farmer
 * who cannot read the text — so we detect the no-op, bound the wait, and report honestly.
 */
function speak(text: string, lang: string): Promise<boolean> {
  return new Promise((resolve) => {
    if (!speechAvailable()) return resolve(false)

    let settled = false
    let startCheck: ReturnType<typeof setTimeout>
    let watchdog: ReturnType<typeof setTimeout>
    const finish = (spoke: boolean) => {
      if (settled) return
      settled = true
      clearTimeout(startCheck)
      clearTimeout(watchdog)
      resolve(spoke)
    }

    const u = new SpeechSynthesisUtterance(text)
    u.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    u.rate = 0.9 // slightly slow: comprehension matters more than brevity
    u.onend = () => finish(true)
    u.onerror = () => finish(false)

    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(u)

    // Case 1: accepted but never started.
    startCheck = setTimeout(() => {
      const s = window.speechSynthesis
      if (!s.speaking && !s.pending) finish(false)
    }, 700)

    // Case 2: started but onend never arrives. Generous ceiling, then assume it played.
    watchdog = setTimeout(() => finish(true), estimateSeconds(text) * 1000 + 5000)
  })
}

/** Play the advisory, preferring pre-generated clips. Returns which mode actually ran. */
export async function playAdvisory(
  segments: string[],
  fallbackText: string,
  lang: string,
): Promise<AudioMode> {
  const haveAll = segments.length > 0 && (await Promise.all(segments.map(clipExists))).every(Boolean)
  if (haveAll) {
    try {
      for (const key of segments) await playClip(key)
      return 'pregenerated'
    } catch {
      // fall through to device speech
    }
  }
  if (speechAvailable()) {
    // Report 'unavailable' when the engine silently refused, so the UI can say so instead of
    // claiming the phone spoke.
    return (await speak(fallbackText, lang)) ? 'device_speech' : 'unavailable'
  }
  return 'unavailable'
}

export function stopAudio() {
  if (speechAvailable()) window.speechSynthesis.cancel()
  if (current) {
    current.pause()
    current = null
  }
}
