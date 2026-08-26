/**
 * Client AI connector (PRAHARI §27.5 / §12).
 *
 * TWO honest paths, never a fake:
 *  1. Real AI — POST to a Supabase Edge Function that calls Gemini server-side
 *     (the GEMINI_API_KEY never touches the browser). Used when VITE_SUPABASE_URL
 *     is configured AND the device is online.
 *  2. Deterministic fallback — for Ask, we rephrase THIS field's own engine numbers
 *     with a template (allowed by governing law 4: "rephrase engine output, never
 *     change a number/band"). For Leaf, we return a "guide" marker so the UI shows a
 *     visual self-check instead of a fabricated diagnosis.
 *
 * Neither path ever invents a risk number, a band, or a chemical/dose (law 3).
 */

import type { FieldEntry, Lang } from './types'

// 🔴 Injected by the explicit `define` allowlist in web/vite.config.ts, NOT by Vite's VITE_*
// convention — that convention ships every prefixed variable to the browser automatically, so one
// careless rename would turn GEMINI_API_KEY into a public string. Reading `import.meta.env.VITE_…`
// here would silently yield undefined, which is exactly the bug this comment replaces: the real AI
// path could never activate no matter how the deployment was configured.
declare const __SUPABASE_URL__: string
declare const __SUPABASE_ANON_KEY__: string

const SUPABASE_URL = __SUPABASE_URL__ || undefined
const SUPABASE_ANON = __SUPABASE_ANON_KEY__ || undefined

export type AskSource = 'ai' | 'engine'
export interface AskResult {
  text: string
  source: AskSource
}

export type LeafSymptom = 'late_blight' | 'early_blight' | 'healthy' | 'uncertain'
export type LeafSource = 'ai' | 'guide'
export interface LeafResult {
  source: LeafSource
  symptom?: LeafSymptom
  confidence?: number
  note?: string
}

export function aiConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_ANON)
}

function edgeHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    apikey: SUPABASE_ANON || '',
    Authorization: `Bearer ${SUPABASE_ANON || ''}`,
  }
}

/** Only the facts the engine actually computed — no free text, so the model cannot drift. */
function fieldFacts(field: FieldEntry): Record<string, unknown> {
  return {
    band: field.band,
    dsv_accum_7d: field.dsv_accum_7d,
    dsv_today: field.dsv_today,
    wet_hours: field.wet_hours,
    mean_wet_temp_c: field.mean_wet_temp_c,
    min_temp_c: field.min_temp_c,
    confidence: field.confidence,
    firing_pathogen: field.firing_pathogen,
    criterion_met: field.criterion_met,
    spray_start_hour: field.spray_start_hour,
    spray_end_hour: field.spray_end_hour,
    crop: field.crop,
  }
}

/**
 * Ask the assistant about one field. Tries the server-side Gemini path; on any failure or
 * when unconfigured/offline, returns a deterministic answer built from the engine's numbers.
 */
export async function askAssistant(field: FieldEntry, question: string, lang: Lang): Promise<AskResult> {
  if (aiConfigured() && navigator.onLine) {
    try {
      const res = await fetch(`${SUPABASE_URL}/functions/v1/ask`, {
        method: 'POST',
        headers: edgeHeaders(),
        body: JSON.stringify({ facts: fieldFacts(field), question, lang }),
      })
      if (res.ok) {
        const data = (await res.json()) as { text?: string }
        if (data.text && data.text.trim()) {
          return { text: data.text.trim(), source: 'ai' }
        }
      }
    } catch {
      // fall through to deterministic answer
    }
  }
  return { text: engineAnswer(field, lang), source: 'engine' }
}

/** Rephrases the field's own engine readings. Deterministic, offline, and never invents a number. */
function engineAnswer(field: FieldEntry, lang: Lang): string {
  const name = lang === 'hi' ? field.name_hi : field.name_en
  const win =
    field.spray_start_hour != null && field.spray_end_hour != null
      ? `${String(field.spray_start_hour).padStart(2, '0')}:00–${String(field.spray_end_hour).padStart(2, '0')}:00`
      : null

  if (lang === 'hi') {
    const parts: string[] = []
    if (field.band === 'act') {
      parts.push(`${name} में झुलसा रोग का उच्च जोखिम है।`)
      parts.push(`पिछले 7 दिनों का रोग-गंभीरता योग (DSV) ${field.dsv_accum_7d} है और पत्तियाँ लगभग ${field.wet_hours} घंटे गीली रहीं।`)
      if (win) parts.push(`छिड़काव के लिए सबसे अनुकूल समय ${win} है — मौसम अनुकूल होने पर इसी में पूरा करें।`)
      else parts.push(`अभी कोई पूरी तरह साफ़ छिड़काव खिड़की नहीं मिली; हवा/बारिश थमने पर ही छिड़काव करें।`)
    } else if (field.band === 'watch') {
      parts.push(`${name} में मौसम रोग के अनुकूल बनने लगा है, पर अभी तुरंत छिड़काव की आवश्यकता नहीं।`)
      parts.push(`7-दिन DSV ${field.dsv_accum_7d} और गीलापन ${field.wet_hours} घंटे — खेत पर नज़र रखें।`)
    } else {
      parts.push(`${name} में आज मौसम सुरक्षित है; किसी छिड़काव की आवश्यकता नहीं।`)
      parts.push(`7-दिन DSV केवल ${field.dsv_accum_7d} है, जो चेतावनी सीमा से नीचे है।`)
    }
    if (field.confidence != null) parts.push(`यह आकलन ${Math.round(field.confidence * 100)}% भरोसे के साथ है।`)
    return parts.join(' ')
  }

  const parts: string[] = []
  if (field.band === 'act') {
    parts.push(`High blight risk on ${name}.`)
    parts.push(`Its 7-day disease-severity total (DSV) is ${field.dsv_accum_7d} and leaves stayed wet for about ${field.wet_hours} hours.`)
    if (win) parts.push(`The most suitable spray window is ${win} — complete it then if weather allows.`)
    else parts.push(`No fully clean spray window was found right now; spray only once wind/rain settles.`)
  } else if (field.band === 'watch') {
    parts.push(`Conditions on ${name} are starting to favour disease, but no spray is needed yet.`)
    parts.push(`7-day DSV is ${field.dsv_accum_7d} with ${field.wet_hours} wet hours — keep watch.`)
  } else {
    parts.push(`All clear on ${name} today; no spraying needed.`)
    parts.push(`The 7-day DSV is only ${field.dsv_accum_7d}, below the warning threshold.`)
  }
  if (field.confidence != null) parts.push(`Confidence in this assessment is ${Math.round(field.confidence * 100)}%.`)
  return parts.join(' ')
}

/**
 * Analyse a leaf photo. Real path sends the image to a server-side Gemini Vision call; the
 * fallback returns { source: 'guide' } so the UI shows a self-check comparison — never a
 * fabricated confidence number.
 */
export async function scanLeaf(imageBase64: string, lang: Lang): Promise<LeafResult> {
  if (aiConfigured() && navigator.onLine) {
    try {
      const res = await fetch(`${SUPABASE_URL}/functions/v1/leaf-scan`, {
        method: 'POST',
        headers: edgeHeaders(),
        body: JSON.stringify({ image: imageBase64, lang }),
      })
      if (res.ok) {
        const data = (await res.json()) as LeafResult
        if (data.symptom) return { ...data, source: 'ai' }
      }
    } catch {
      // fall through to guide
    }
  }
  return { source: 'guide' }
}
