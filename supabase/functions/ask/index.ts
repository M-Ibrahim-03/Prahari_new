/**
 * POST /functions/v1/ask — server-side Gemini rephrasing of engine facts (PRD §27.5).
 *
 * 🔴 GEMINI_API_KEY is read from Deno.env and never leaves this process. The browser holds only the
 * Supabase anon key, so the paid credential cannot be scraped out of a bundle.
 *
 * Contract with web/src/lib/ai.ts:
 *   in  { facts, question, lang }
 *   out { text }                      → client shows it, source: 'ai'
 *       { text: null, reason }        → client falls back to its deterministic engine answer (L4)
 *
 * 🔴 Returning 200-with-no-text on rejection is deliberate. The client already has a correct
 * offline answer for every field; a rejected LLM reply must degrade to that silently rather than
 * surface an error a farmer cannot act on. `reason` is there for the Trust screen and logs.
 */

import { CORS_HEADERS, callGemini, gateText, json } from '../_shared/guard.ts'

// Mirrors SYSTEM_PROMPT_HI / SYSTEM_PROMPT_EN in pipeline/verbalise.py.
const SYSTEM_HI = `आप प्रहरी (PRAHARI) कृषि मौसम सहायक हैं।
आपका काम दिए गए मौसम और रोग के तथ्यों को किसान भाई-बहनों के लिए सरल, आदरणीय और स्पष्ट हिंदी में बताना है।
नियम:
1. केवल दिए गए तथ्यों पर आधारित रहें। अपने मन से कोई संख्या या समय न जोड़ें।
2. किसी भी दवा, कीटनाशक, फफूंदनाशक का नाम, खुराक, मात्रा या सुरक्षा उपकरण न बताएं।
3. दी गई स्थिति (band) को न बदलें — न बढ़ाएं, न घटाएं।
4. उत्तर अधिकतम 40-50 शब्दों में रखें।
5. यदि प्रश्न का उत्तर दिए गए तथ्यों में नहीं है, तो विनम्रता से कहें कि यह जानकारी उपलब्ध नहीं है।`

const SYSTEM_EN = `You are PRAHARI, an agriculture weather assistant.
Your task is to explain the provided disease facts in simple, respectful words a smallholder farmer can act on.
Rules:
1. State ONLY the facts provided. Never invent a number or a time.
2. NEVER mention any chemical, brand, fungicide, dose, spray volume, or protective equipment.
3. Never change the given risk band — do not upgrade or downgrade it.
4. Keep the response strictly under 50 words.
5. If the question cannot be answered from the given facts, say politely that you do not have that information.`

function factLines(facts: Record<string, unknown>, lang: string): string {
  const label: Record<string, [string, string]> = {
    crop: ['फसल', 'Crop'],
    band: ['स्थिति', 'Risk band'],
    dsv_today: ['आज का DSV', "Today's DSV"],
    dsv_accum_7d: ['7-दिन संचित DSV', '7-day accumulated DSV'],
    wet_hours: ['नमी अवधि (घंटे)', 'Wet hours'],
    mean_wet_temp_c: ['गीले समय का औसत तापमान (°C)', 'Mean wet-period temperature (C)'],
    min_temp_c: ['न्यूनतम तापमान (°C)', 'Minimum temperature (C)'],
    confidence: ['भरोसा', 'Confidence'],
    firing_pathogen: ['रोग', 'Pathogen'],
    criterion_met: ['मानदंड पूरा', 'Criterion met'],
    spray_start_hour: ['छिड़काव शुरू (घंटा)', 'Spray window start hour'],
    spray_end_hour: ['छिड़काव समाप्त (घंटा)', 'Spray window end hour'],
  }
  const i = lang === 'hi' ? 0 : 1
  return Object.entries(facts)
    .filter(([, v]) => v !== null && v !== undefined && v !== '')
    .map(([k, v]) => `${label[k]?.[i] ?? k}: ${v}`)
    .join('\n')
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS_HEADERS })
  if (req.method !== 'POST') return json({ error: 'method_not_allowed' }, 405)

  const apiKey = Deno.env.get('GEMINI_API_KEY')
  if (!apiKey) return json({ text: null, reason: 'no_api_key' })

  let body: { facts?: Record<string, unknown>; question?: string; lang?: string }
  try {
    body = await req.json()
  } catch {
    return json({ error: 'bad_json' }, 400)
  }

  const facts = body.facts ?? {}
  const question = (body.question ?? '').toString().slice(0, 400)
  const lang = body.lang === 'en' ? 'en' : 'hi'
  if (!Object.keys(facts).length) return json({ error: 'facts_required' }, 400)

  const prompt =
    lang === 'hi'
      ? `तथ्य:\n${factLines(facts, lang)}\n\nकिसान का प्रश्न: ${question || 'मेरे खेत की स्थिति बताइए।'}`
      : `Facts:\n${factLines(facts, lang)}\n\nFarmer's question: ${question || 'Tell me the situation in my field.'}`

  let raw: string
  try {
    raw = await callGemini(apiKey, 'gemini-2.0-flash', [{ text: prompt }], lang === 'hi' ? SYSTEM_HI : SYSTEM_EN)
  } catch (err) {
    // Upstream failure is an L4 rung, not a 500 — the client has a working fallback.
    return json({ text: null, reason: String((err as Error).message ?? err) })
  }

  const gate = gateText(raw, { facts, expectedBand: String(facts.band ?? ''), maxChars: 600 })
  if (!gate.passed) return json({ text: null, reason: `gate:${gate.reason}` })

  return json({ text: raw })
})
