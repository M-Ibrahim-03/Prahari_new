/**
 * POST /functions/v1/leaf-scan — server-side Gemini Vision leaf check (PRD §12, §39.2).
 *
 * 🔴 GEMINI_API_KEY is read from Deno.env only.
 *
 * Contract with web/src/lib/ai.ts:
 *   in  { image (base64, no data-URL prefix), lang }
 *   out { symptom, confidence, note }  → client shows it, source: 'ai'
 *       { symptom: null, reason }      → client shows the visual self-check guide instead
 *
 * 🔴 THIS IS NOT A DIAGNOSIS AND MUST NEVER MOVE A SPRAY DECISION. Spray timing comes from the
 * weather engine (Hutton + Wallin + TOMCAST) and nothing else. A photo of one leaf cannot know
 * yesterday's wet hours, and a farmer who sprays because a phone said "late blight" on a
 * nitrogen-deficient leaf has wasted money we told them to spend. The symptom is a second opinion
 * on what the farmer is already looking at — the `note` says so in the farmer's own language.
 *
 * `confidence` is the MODEL'S OWN self-reported score, not a validated accuracy figure. There is no
 * labelled Indian potato-leaf test set in this build, so we never present it as one.
 */

import { CORS_HEADERS, callGemini, gateText, json } from '../_shared/guard.ts'

const VALID = ['late_blight', 'early_blight', 'healthy', 'uncertain'] as const

const SYSTEM = `You are a plant-pathology assistant looking at a single potato leaf photograph.

Classify the visible symptom as exactly one of:
- "late_blight"  — water-soaked dark grey/brown lesions with irregular edges, often a pale halo, sometimes white fuzzy growth on the underside
- "early_blight" — small brown spots with concentric rings ("target spot"), usually on older lower leaves, with a yellow surround
- "healthy"      — no disease lesions visible
- "uncertain"    — blurred, too dark, not a potato leaf, or symptoms you cannot separate confidently

Rules you must obey:
1. Reply with ONLY a JSON object: {"symptom": "...", "confidence": 0.0-1.0, "note": "..."}
2. NEVER name any chemical, fungicide, brand, dose, quantity, or protective equipment.
3. NEVER tell the farmer when to spray, or whether to spray. You are not the spray decision.
4. Do not state any number other than your confidence value.
5. The "note" must be one short sentence describing only what is VISIBLE in the photo.
6. Prefer "uncertain" over guessing. A wrong confident answer costs a farmer money.`

const NOTE_HI: Record<string, string> = {
  late_blight: 'फ़ोटो में पछेती झुलसा जैसे गहरे, पानी-सने धब्बे दिख रहे हैं।',
  early_blight: 'फ़ोटो में अगेती झुलसा जैसे गोल छल्लेदार भूरे धब्बे दिख रहे हैं।',
  healthy: 'फ़ोटो में पत्ती पर रोग के धब्बे नहीं दिख रहे।',
  uncertain: 'फ़ोटो से पक्का नहीं कहा जा सकता — साफ़ रोशनी में दोबारा फ़ोटो लें।',
}

/** Appended to every reply so the boundary travels with the answer, not just the docs. */
const DISCLAIMER: Record<string, string> = {
  hi: 'यह केवल फ़ोटो से मिला संकेत है; छिड़काव का समय मौसम के आकलन से ही तय होता है।',
  en: 'This is only a hint from the photo; spray timing comes from the weather assessment.',
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS_HEADERS })
  if (req.method !== 'POST') return json({ error: 'method_not_allowed' }, 405)

  const apiKey = Deno.env.get('GEMINI_API_KEY')
  if (!apiKey) return json({ symptom: null, reason: 'no_api_key' })

  let body: { image?: string; lang?: string }
  try {
    body = await req.json()
  } catch {
    return json({ error: 'bad_json' }, 400)
  }

  const lang = body.lang === 'en' ? 'en' : 'hi'
  // Tolerate a full data URL as well as raw base64.
  const image = (body.image ?? '').replace(/^data:image\/\w+;base64,/, '')
  if (!image) return json({ error: 'image_required' }, 400)
  // ~4 MB of base64. Bigger than this is a 2G upload we should never have accepted client-side.
  if (image.length > 5_600_000) return json({ symptom: null, reason: 'image_too_large' })

  let raw: string
  try {
    raw = await callGemini(
      apiKey,
      'gemini-2.0-flash',
      [
        { inline_data: { mime_type: 'image/jpeg', data: image } },
        { text: 'Classify this potato leaf. Reply with only the JSON object.' },
      ],
      SYSTEM,
      200,
    )
  } catch (err) {
    return json({ symptom: null, reason: String((err as Error).message ?? err) })
  }

  // Gemini often fences JSON in ```json … ``` despite instructions.
  const match = raw.match(/\{[\s\S]*\}/)
  if (!match) return json({ symptom: null, reason: 'unparseable' })

  let parsed: { symptom?: string; confidence?: number; note?: string }
  try {
    parsed = JSON.parse(match[0])
  } catch {
    return json({ symptom: null, reason: 'unparseable' })
  }

  const symptom = VALID.includes(parsed.symptom as typeof VALID[number]) ? parsed.symptom! : 'uncertain'
  let confidence = typeof parsed.confidence === 'number' ? parsed.confidence : 0
  if (!Number.isFinite(confidence) || confidence < 0) confidence = 0
  if (confidence > 1) confidence = 1

  // 🔴 A low-confidence guess is reported as uncertain rather than as a named disease. The farmer
  // gets "take a clearer photo", which is actionable, instead of a coin-flip that looks like fact.
  const finalSymptom = confidence < 0.55 ? 'uncertain' : symptom

  // The note is free text from the model, so it goes through the same gate as the Ask path. On
  // rejection we substitute our own note and keep the classification — the symptom label itself is
  // a closed enum and cannot carry an invented number or a chemical name.
  let note = (parsed.note ?? '').toString().trim()
  const gate = gateText(note, { facts: { confidence }, maxChars: 200 })
  if (!note || !gate.passed) {
    note = lang === 'hi' ? NOTE_HI[finalSymptom] : ''
  }

  const composed = [note, DISCLAIMER[lang]].filter(Boolean).join(' ')

  return json({ symptom: finalSymptom, confidence: Math.round(confidence * 100) / 100, note: composed })
})
