import { describeAge } from '../lib/types'
import type { Lang } from '../lib/types'

const L = {
  hi: { offline: 'ऑफ़लाइन — सहेजा हुआ डेटा', staleWarn: 'यह पुराना डेटा है — आज का नहीं' },
  en: { offline: 'Offline — showing saved data', staleWarn: 'This data is old — not today’s' },
}

/**
 * 🔴 P5 / §21.5: data age is always visible and stale data is stated, never hidden.
 * L7 is the thesis of the degradation ladder — a cached forecast displayed as if fresh is the
 * failure mode that causes a farmer to spray on three-day-old information.
 */
export function DataAge({
  runId,
  lang,
  fromCache,
}: {
  runId: string
  lang: Lang
  fromCache: boolean
}) {
  const age = describeAge(runId)
  const t = L[lang]
  const label = lang === 'hi' ? age.hi : age.en
  const loud = age.freshness === 'stale' || age.freshness === 'very_stale'

  return (
    <div className={`age age--${age.freshness}`} role={loud ? 'alert' : undefined}>
      <span className="age__dot" aria-hidden="true" />
      <span className="age__text">
        {label}
        {fromCache && <> · {t.offline}</>}
      </span>
      {loud && <strong className="age__warn">{t.staleWarn}</strong>}
    </div>
  )
}
