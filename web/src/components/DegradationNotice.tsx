import { useState } from 'react'
import type { FieldPayload, Lang } from '../lib/types'
import '../styles/parts/degradation.css'

type DataStatus = FieldPayload['prahari']['data_status']

/** The rungs of §28.3 this UI can name. 'L?' is every rung it cannot. */
export type DegradationLevel = 'L1' | 'L2' | 'L3' | 'L4' | 'L5' | 'L6' | 'L7' | 'L8' | 'L10' | 'L?'

export type DegradationSeverity = 'info' | 'warn' | 'critical'

export interface DegradationNote {
  level: DegradationLevel
  severity: DegradationSeverity
  /** The normalised code for a recognised note; the ENTIRE original string for one we do not know. */
  code: string
  hi: string
  en: string
  known: boolean
}

interface Rung {
  severity: DegradationSeverity
  hi: string
  en: string
}

/**
 * 🔴 Severity is assigned by what the farmer loses, not by how alarming it sounds to an engineer.
 * "The ML correction did not run" is a headline in a post-mortem and nothing at all in a field:
 * the physics forecast is the forecast, the advice is identical, and there is no action to take.
 * Shouting it would spend the farmer's attention on something they cannot use — and §37 names
 * two false alarms as the worst outcome in the product. Only a rung that changes what the
 * advisory is WORTH gets to be loud.
 *
 * Bilingual strings sit per-entry here rather than in the component's `L` table because this is a
 * semantic lookup table, the same shape as bandToSemantic.ts — a rung's meaning travels with it.
 */
const RUNGS: Record<Exclude<DegradationLevel, 'L?'>, Rung> = {
  L1: {
    severity: 'info',
    hi: 'उपग्रह चित्र नहीं मिले। हरियाली की जाँच इस बार नहीं हुई।',
    en: 'Satellite images unavailable. Crop greenness was not checked this time.',
  },
  L2: {
    severity: 'info',
    hi: 'पूर्वानुमान सिर्फ़ मौसम के नियमों से बना है। सलाह में कोई फ़र्क़ नहीं।',
    en: 'Forecast from the weather rules alone, without the learning model. The advice is unchanged.',
  },
  L3: {
    severity: 'info',
    hi: 'पड़ोस के खेतों की जानकारी कम है। जोखिम सिर्फ़ मौसम से आँका गया है।',
    en: 'Little data from neighbouring fields. Risk estimated from weather alone.',
  },
  L4: {
    severity: 'info',
    hi: 'सलाह बनी-बनाई भाषा में लिखी गई है। बात वही है।',
    en: 'Advisory written from a fixed template. The content is the same.',
  },
  // Info, not warn, deliberately: FieldCard already labels the voice path that actually ran with
  // an ℹ️ note at the moment the farmer presses play. The same fact stated twice at two different
  // volumes teaches them that one of the two is exaggerating. Text is always present (FR-8.9).
  L5: {
    severity: 'info',
    hi: 'रिकॉर्ड की हुई आवाज़ तैयार नहीं है। फ़ोन अपनी आवाज़ में पढ़ेगा।',
    en: 'Recorded audio is not ready. The phone will read it in its own voice.',
  },
  L6: {
    severity: 'warn',
    hi: 'कुछ जगहों का मौसम नहीं मिला। बाक़ी जगहों से अंदाज़ा लगाया गया — भरोसा कुछ कम है।',
    en: 'Weather data missing for some points. Estimated from the rest — confidence is lower.',
  },
  // 🔴 The rung this whole component exists for (§28.3: "L7 is the thesis of this ladder").
  // Yesterday's numbers presented as today's is what makes a farmer spray on old information.
  L7: {
    severity: 'critical',
    hi: 'आज का मौसम नहीं मिल सका। यह कल का पूर्वानुमान है, आज का नहीं।',
    en: "Today's weather could not be fetched. This is yesterday's forecast, not today's.",
  },
  L8: {
    severity: 'info',
    hi: 'हमारा रिकॉर्ड रखने वाला सर्वर नहीं चल रहा। आपकी सलाह पर असर नहीं।',
    en: 'Our records server is unreachable. No effect on your advisory.',
  },
  L10: {
    severity: 'info',
    hi: 'चेतावनी का संदेश भेजने में दिक़्क़त हुई। ऐप में सलाह ताज़ा है।',
    en: 'Alert messages could not be sent. The advisory in the app is current.',
  },
}

/**
 * Codes the pipeline writes, or plausibly will. Deliberately short: guessing a dozen synonyms per
 * rung would give a false sense of coverage, when the honest safety net is the unrecognised path
 * below. L9 and L11 are absent because they are client-side conditions the artefact cannot know
 * about — useFieldPayload and DataAge own those and already say them.
 */
const CODES: Record<string, Exclude<DegradationLevel, 'L?'>> = {
  no_satellite: 'L1',
  no_ndvi: 'L1',
  no_ml: 'L2',
  no_ml_correction: 'L2',
  no_spread: 'L3',
  spread_sparse: 'L3',
  no_llm: 'L4',
  template_advisory: 'L4',
  no_tts: 'L5',
  no_audio: 'L5',
  partial_weather: 'L6',
  weather_partial: 'L6',
  // Three spellings for L7 alone. Misreading the thesis rung as merely unknown is the one
  // classification error with a real cost, so this is where extra aliases earn their bytes.
  weather_failed: 'L7',
  no_weather: 'L7',
  cached_weather: 'L7',
}

const UNRECOGNISED: Rung = {
  severity: 'warn',
  hi: 'यह सूचना ऐप को समझ नहीं आई। जैसी मिली है, वैसी नीचे दी गई है।',
  en: 'The app does not recognise this notice. It is shown below exactly as received.',
}

const UNNAMED: Rung = {
  severity: 'warn',
  hi: 'कुछ जानकारी अधूरी रही, पर कारण नहीं बताया गया। सलाह ध्यान से पढ़ें।',
  en: 'Something was incomplete but the reason was not recorded. Read the advisory with care.',
}

/** The pipeline writes "<code>[:detail] — engineer note". The code is the first token. */
function normalise(raw: string): string {
  const beforeNote = raw.split('—')[0] // em dash, as written by pipeline/nightly.py
  return beforeNote.split(':')[0].trim().toLowerCase().replace(/[\s-]+/g, '_')
}

/**
 * One engineer-facing degradation string -> a farmer-facing note.
 *
 * 🔴 An unrecognised code is surfaced VERBATIM and never dropped. A degradation this UI does not
 * understand is, by construction, one written after this table was — which makes it the most
 * likely of all of them to matter. Swallowing it is the exact failure this component exists to
 * prevent, so the unknown path is the load-bearing one and the lookup table is the optimisation.
 *
 * 🔴 Its severity is 'warn', not 'critical': unknown means unclassified, not catastrophic. Painting
 * every future code in --risk-act would teach a farmer that red sometimes means nothing, which
 * destroys the one signal that must never be doubted. Warn is impossible to miss and impossible
 * to mistake for an emergency — conservative in both directions.
 */
export function classifyDegradation(raw: string): DegradationNote {
  const code = normalise(raw)
  const level = CODES[code]
  if (level) {
    const rung = RUNGS[level]
    return { level, severity: rung.severity, code, hi: rung.hi, en: rung.en, known: true }
  }
  return {
    level: 'L?',
    severity: UNRECOGNISED.severity,
    code: raw.trim(),
    hi: UNRECOGNISED.hi,
    en: UNRECOGNISED.en,
    known: false,
  }
}

const SEVERITY_RANK: Record<DegradationSeverity, number> = { critical: 0, warn: 1, info: 2 }

/**
 * The whole payload's degradation state as notes, worst first.
 *
 * Sorted here rather than only in the markup so that any future consumer which renders this list
 * flat — an officer console, a printed slip — cannot bury an L7 under three lines of trivia.
 * Array.sort is stable (ES2019), so pipeline order survives inside a severity group.
 */
export function degradationNotes(
  dataStatus: DataStatus,
  degradation: readonly string[],
): DegradationNote[] {
  const notes = degradation
    .filter((raw) => raw.trim().length > 0)
    // Synthetic weather is skipped here on purpose: App.tsx renders a much louder standalone
    // banner for it, and two warnings about one fact dilute each other.
    .filter((raw) => normalise(raw) !== 'scenario')
    .map(classifyDegradation)

  // 🔴 A payload may state its condition in `data_status` and forget to explain it in
  // `degradation` — the two fields are written by hand at separate call sites. When that happens
  // the ladder must still be surfaced, so the status field itself becomes the note. Without this
  // a "stale" artefact would render an empty component: the honest-looking silence that L7 is
  // specifically about. DataAge cannot cover the case either, because a run that served cached
  // weather writes a run_id of NOW — fresh timestamp, yesterday's weather.
  if (dataStatus === 'stale' && !notes.some((n) => n.level === 'L7')) {
    notes.push({ ...RUNGS.L7, level: 'L7', code: 'data_status:stale', known: true })
  }
  if (dataStatus === 'degraded' && notes.length === 0) {
    notes.push({ ...UNNAMED, level: 'L?', code: 'data_status:degraded', known: false })
  }

  return notes.sort((a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity])
}

/** Same icons as the risk bands (bandToSemantic.ts) — one visual vocabulary, not two. */
const ICON: Record<DegradationSeverity, string> = { critical: '❗', warn: '⚠', info: 'ℹ️' }

const L = {
  hi: {
    title: 'जानकारी में कमी',
    note: 'तकनीकी सूचना',
    notes: 'तकनीकी सूचनाएँ',
  },
  en: {
    title: 'Data limitations',
    note: 'technical note',
    notes: 'technical notes',
  },
}

/**
 * §28.3 — the degradation ladder, stated to the farmer instead of hidden from them.
 *
 * 🔴 Renders NOTHING at L0. A green "all systems normal" box would occupy this space every single
 * day, and a warning slot that is usually reassuring is a warning slot nobody reads. The space
 * being empty is what makes it mean something when it is not.
 */
export function DegradationNotice({
  dataStatus,
  degradation,
  lang,
}: {
  dataStatus: DataStatus
  degradation: string[]
  lang: Lang
}) {
  const [openInfo, setOpenInfo] = useState(false)
  const t = L[lang]
  const notes = degradationNotes(dataStatus, degradation)
  if (notes.length === 0) return null

  const critical = notes.filter((n) => n.severity === 'critical')
  const warn = notes.filter((n) => n.severity === 'warn')
  const info = notes.filter((n) => n.severity === 'info')

  return (
    <section className="degrade" aria-label={t.title}>
      {critical.length > 0 && (
        // One role="alert" on the group, not on each row: several assertive regions appearing at
        // once interrupt a screen reader over and over and the message is lost in the collisions.
        <div className="degrade__group degrade__group--critical" role="alert">
          {critical.map((n, i) => (
            <Row key={i} note={n} lang={lang} />
          ))}
        </div>
      )}

      {warn.length > 0 && (
        <div className="degrade__group degrade__group--warn">
          {warn.map((n, i) => (
            <Row key={i} note={n} lang={lang} />
          ))}
        </div>
      )}

      {info.length > 0 && (
        <div className="degrade__group degrade__group--info">
          {/* Collapsed by default so that a bad night for the enrichment layers cannot push the
              farmer's actual advisory below the fold. Bounded to one line whether there is one
              note or six — quiet, but one tap from being read in full. */}
          <button
            className="degrade__toggle"
            onClick={() => setOpenInfo(!openInfo)}
            aria-expanded={openInfo}
          >
            <span aria-hidden="true">{ICON.info}</span>{' '}
            {info.length} {info.length === 1 ? t.note : t.notes} {openInfo ? '▴' : '▾'}
          </button>
          {openInfo && info.map((n, i) => <Row key={i} note={n} lang={lang} />)}
        </div>
      )}
    </section>
  )
}

/**
 * 🔴 The ladder level is always shown, in monospace, next to the note. A farmer's eye passes over
 * it; a KVK officer or a judge reading the same screen over their shoulder can look "L7" up in
 * §28.3 and check whether the app told the truth. One screen, two audiences, no second build.
 */
function Row({ note, lang }: { note: DegradationNote; lang: Lang }) {
  return (
    <div className="degrade__row">
      {/* Icon plus text, never colour alone (§21.3) — this box is read in direct sunlight. */}
      <span className="degrade__icon" aria-hidden="true">{ICON[note.severity]}</span>
      <p className="degrade__text">{lang === 'hi' ? note.hi : note.en}</p>
      <span className={note.known ? 'degrade__code' : 'degrade__code degrade__code--raw'}>
        {note.level} · {note.code}
      </span>
    </div>
  )
}
