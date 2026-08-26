import { useState } from 'react'
import { bandSemantic } from '../lib/bandToSemantic'
import type { AudioMode } from '../lib/audio'
import type { FieldEntry, Lang } from '../lib/types'
import { PlayButton } from './PlayButton'
import { WhyPanel } from './WhyPanel'

const L = {
  hi: {
    crop: { potato: 'आलू' },
    deviceVoice: 'फ़ोन की आवाज़ (रिकॉर्डेड आवाज़ अभी नहीं)',
    noVoice: 'इस फ़ोन पर आवाज़ नहीं चली — ऊपर लिखा पढ़ें या किसी से पढ़वाएँ',
    noData: 'इस खेत की जानकारी नहीं',
  },
  en: {
    crop: { potato: 'potato' },
    deviceVoice: "Phone's own voice (recorded audio not yet available)",
    noVoice: 'Voice did not play on this phone — read the text above',
    noData: 'No data for this field',
  },
}

/**
 * One card per field (§21.1). Three parcels = three cards, no aggregation — an "average risk"
 * across a farmer's plots is a meaningless number.
 *
 * 🔴 Every card resolves to an action, including "no risk" (P2). The play button is the largest
 * interactive element on the card.
 */
export function FieldCard({
  field,
  lang,
  primary,
  modelId,
  modelVersion,
}: {
  field: FieldEntry
  lang: Lang
  primary: boolean
  modelId: string
  modelVersion: string
}) {
  const [mode, setMode] = useState<AudioMode | null>(null)
  const sem = bandSemantic(field.band)
  const t = L[lang]
  const advisory = field.advisory?.[lang]
  const name = lang === 'hi' ? field.name_hi : field.name_en
  const crop = (t.crop as Record<string, string>)[field.crop] ?? field.crop

  return (
    <article className={primary ? 'card card--primary' : 'card'}>
      {/* Band strip: colour + icon + text label. Colour is never the only signal (§21.3). */}
      <header className="card__band" style={{ background: sem.color, color: sem.on }}>
        <span className="card__band-icon" aria-hidden="true">{sem.icon}</span>
        <span className="card__band-label">{lang === 'hi' ? sem.hi : sem.en}</span>
        <span className="card__crop">{crop}</span>
      </header>

      <div className="card__body">
        <h2 className="card__name">{name}</h2>
        {field.area_local && <p className="card__area">{field.area_local}</p>}

        {advisory ? (
          <>
            {/* The action, always present — even for "no risk". */}
            <p className="card__action">{advisory.action}</p>

            <PlayButton advisory={advisory} lang={lang} primary={primary} onMode={setMode} />

            {/* Honest about which voice path actually ran (degradation L5). A voice that silently
                fails is worse than one that says it failed — the text is always there to fall
                back on (FR-8.9), but only if the farmer knows to look at it. */}
            {mode === 'device_speech' && <p className="card__degraded">ℹ️ {t.deviceVoice}</p>}
            {mode === 'unavailable' && (
              <p className="card__degraded" role="alert">⚠️ {t.noVoice}</p>
            )}

            <WhyPanel
              field={field}
              advisory={advisory}
              lang={lang}
              modelId={modelId}
              modelVersion={modelVersion}
            />
          </>
        ) : (
          <p className="card__action">{t.noData}{field.note ? ` (${field.note})` : ''}</p>
        )}
      </div>
    </article>
  )
}
