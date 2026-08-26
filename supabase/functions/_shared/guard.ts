/**
 * PRAHARI — shared guard for every server-side Gemini call (PRD §27.4, §27.5, §39.2).
 *
 * 🔴 This file is the reason an LLM is allowed anywhere near this product. The model is a
 * TRANSLATOR, never an oracle: it receives facts the deterministic engine already computed and
 * rephrases them. Everything it returns passes back through `gateText` before a farmer sees it.
 *
 * Mirror of pipeline/validate.py. If you change a rule there, change it here — the whole point is
 * that the browser path and the nightly path enforce the same boundary.
 *
 * 🔴 Rejection is ROUTINE, not exceptional. On rejection these functions return no text at all,
 * which makes web/src/lib/ai.ts fall back to its deterministic engine answer. The farmer sees a
 * correct, slightly plainer sentence and loses nothing. That is the designed behaviour, so the
 * gate is free to be strict.
 */

export const CORS_HEADERS: Record<string, string> = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
  })
}

/**
 * 🔴 Active ingredients and brand names sold for potato blight in India. The app must never put
 * one of these in front of a farmer: choosing a product is a licensed agronomist's judgement that
 * depends on resistance history, pre-harvest interval and what the local dealer actually stocks,
 * and there is no agronomist in this loop (PRD §39.2).
 *
 * Note what is deliberately ABSENT: the generic Hindi word "दवा" (medicine) and "छिड़काव" (spraying).
 * The engine's own templates use both — "दवा तैयार रखें" tells a farmer to have their usual product
 * ready without naming one, which is exactly the permitted register. Blocking generic vocabulary
 * would reject the product's own correct sentences.
 */
const CHEMICAL_BLOCKLIST = [
  'mancozeb', 'metalaxyl', 'cymoxanil', 'cymoxanil', 'chlorothalonil', 'propineb', 'zineb',
  'dimethomorph', 'fluopicolide', 'azoxystrobin', 'difenoconazole', 'carbendazim', 'captan',
  'fosetyl', 'famoxadone', 'fenamidone', 'iprovalicarb', 'mandipropamid', 'oxathiapiprolin',
  'copper oxychloride', 'bordeaux', 'cuprous oxide',
  'ridomil', 'dithane', 'antracol', 'curzate', 'acrobat', 'blitox', 'melody', 'sectin', 'equation',
  'indofil', 'saaf', 'krilaxyl', 'matco',
  'मैंकोजेब', 'मेटालैक्सिल', 'कॉपर', 'बोर्डो', 'रिडोमिल', 'डाइथेन', 'ब्लाइटॉक्स', 'इंडोफिल',
]

/** Dose, concentration and volume patterns. A number next to any of these is a prescription. */
const DOSE_PATTERN =
  /\d+(\.\d+)?\s*(ml|मिली|मि\.?ली|l\b|लीटर|litre|liter|g\b|gm|ग्राम|kg|किलो|%|ppm|per\s*(litre|liter|l\b|acre|hectare|ha\b|एकड़|बीघा|हेक्टेयर)|\/\s*(l\b|litre|acre|ha\b))/i

/** Personal protective equipment and re-entry intervals — also a licensed judgement. */
const PPE_PATTERN =
  /\b(mask|gloves|goggles|respirator|protective\s+clothing|re-?entry)\b|मास्क|दस्ताने|चश्मा|सुरक्षा\s*वस्त्र/i

/** Devanagari digits, so a Hindi reply cannot smuggle a number past the numeric check. */
function normaliseDigits(s: string): string {
  return s.replace(/[०-९]/g, (d) => String('०१२३४५६७८९'.indexOf(d)))
}

function numbersIn(text: string): number[] {
  const matches = normaliseDigits(text).match(/\d+(\.\d+)?/g)
  return matches ? matches.map(Number) : []
}

/**
 * Every number the model is permitted to utter, derived from the facts it was given.
 *
 * 🔴 7 is allowed as a documented STRUCTURAL constant: the accumulation window is seven days and
 * every template in the product says so ("7-day DSV", "पिछले 7 दिनों"). Nothing else is granted a
 * free pass — an invented "spray within 10 days" is rejected, which is the case that matters.
 */
export function allowedNumbers(facts: Record<string, unknown>): Set<number> {
  const allowed = new Set<number>([7])
  for (const value of Object.values(facts)) {
    if (typeof value !== 'number' || !Number.isFinite(value)) continue
    allowed.add(value)
    allowed.add(Math.round(value))
    allowed.add(Math.round(value * 10) / 10)
    // A confidence of 0.84 is spoken as "84%".
    if (value > 0 && value <= 1) allowed.add(Math.round(value * 100))
  }
  return allowed
}

export interface GateResult {
  passed: boolean
  reason?: string
}

/** The band the model was told about must be the band its wording implies. */
const BAND_CONTRADICTION: Record<string, RegExp> = {
  safe: /\b(spray now|spray immediately|urgent|high risk)\b|तुरंत\s*छिड़काव|उच्च\s*जोखिम/i,
  act: /\b(no spray|not needed|all clear|no action)\b|आवश्यकता\s*नहीं|कोई\s*ज़रूरत\s*नहीं/i,
}

export function gateText(
  text: string,
  opts: { facts: Record<string, unknown>; expectedBand?: string; maxChars?: number },
): GateResult {
  const t = (text ?? '').trim()
  if (!t) return { passed: false, reason: 'empty' }

  const maxChars = opts.maxChars ?? 600
  if (t.length > maxChars) return { passed: false, reason: `too_long:${t.length}` }

  const lower = t.toLowerCase()
  for (const term of CHEMICAL_BLOCKLIST) {
    if (lower.includes(term.toLowerCase())) return { passed: false, reason: `chemical:${term}` }
  }
  if (DOSE_PATTERN.test(t)) return { passed: false, reason: 'dose_pattern' }
  if (PPE_PATTERN.test(t)) return { passed: false, reason: 'ppe_or_reentry' }

  const allowed = allowedNumbers(opts.facts)
  for (const n of numbersIn(t)) {
    if (!allowed.has(n)) return { passed: false, reason: `invented_number:${n}` }
  }

  if (opts.expectedBand) {
    const contradiction = BAND_CONTRADICTION[opts.expectedBand]
    if (contradiction && contradiction.test(t)) {
      return { passed: false, reason: `band_contradiction:${opts.expectedBand}` }
    }
  }

  return { passed: true }
}

/** Calls Gemini and returns the first candidate's text, or throws. */
export async function callGemini(
  apiKey: string,
  model: string,
  parts: unknown[],
  systemInstruction: string,
  maxOutputTokens = 220,
): Promise<string> {
  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ role: 'user', parts }],
        systemInstruction: { parts: [{ text: systemInstruction }] },
        // Low temperature: this is a rephrasing task, and creativity here is only a source of
        // gate rejections.
        generationConfig: { temperature: 0.2, maxOutputTokens, topP: 0.8 },
        safetySettings: [],
      }),
    },
  )
  if (!res.ok) throw new Error(`gemini_http_${res.status}`)
  const data = await res.json()
  const text = data?.candidates?.[0]?.content?.parts?.map((p: { text?: string }) => p.text ?? '').join('')
  if (!text) throw new Error('gemini_empty')
  return String(text).trim()
}
