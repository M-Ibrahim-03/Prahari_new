import { useState } from 'react'
import type { Advisory, FieldEntry, Lang } from '../lib/types'

const L = {
  hi: {
    why: 'क्यों?', more: 'और जानें', less: 'कम दिखाएँ',
    humid: 'नमी', wetHours: 'पत्ते गीले रहे', minTemp: 'न्यूनतम तापमान',
    wetTemp: 'गीले समय का औसत तापमान', criterion: 'मापदंड', met: 'पूरा', notMet: 'पूरा नहीं',
    dsvToday: 'DSV आज', dsvAccum: '७ दिन का संचय', limit: 'सीमा', model: 'मॉडल',
    hours: 'घंटे', cell: 'गणना क्षेत्र',
  },
  en: {
    why: 'Why?', more: 'Learn more', less: 'Show less',
    humid: 'Humidity', wetHours: 'leaves stayed wet', minTemp: 'Minimum temperature',
    wetTemp: 'Mean temp during wet spell', criterion: 'Criterion', met: 'met', notMet: 'not met',
    dsvToday: 'DSV today', dsvAccum: '7-day accumulation', limit: 'threshold', model: 'Model',
    hours: 'hours', cell: 'computation cell',
  },
}

/**
 * §21.4 — three-depth progressive disclosure.
 * 🔴 Depth 1 contains not a single number; depth 2 contains the criterion evaluation. The same
 * facts, rendered for a farmer and for an officer, so one screen serves both without
 * patronising either.
 */
export function WhyPanel({
  field,
  advisory,
  lang,
  modelId,
  modelVersion,
}: {
  field: FieldEntry
  advisory: Advisory
  lang: Lang
  modelId: string
  modelVersion: string
}) {
  const [open, setOpen] = useState(false)
  const t = L[lang]

  return (
    <div className="why">
      <div className="why__depth1">
        {/* Depth 1: plain-language cause, icons, zero numbers. */}
        <div className="why__row"><span aria-hidden="true">💧</span><span>{advisory.why}</span></div>
        <div className="why__row"><span aria-hidden="true">💊</span><span>{advisory.when}</span></div>
      </div>

      <button className="why__toggle" onClick={() => setOpen(!open)} aria-expanded={open}>
        {open ? `${t.less} ▴` : `${t.more} ▾`}
      </button>

      {open && (
        <div className="why__depth2">
          {/* Depth 2: the numbers behind the band, including the criterion evaluation. */}
          <dl className="kv">
            <dt>{t.wetHours}</dt>
            <dd>{field.wet_hours ?? '—'} {t.hours}</dd>

            <dt>{t.minTemp}</dt>
            <dd>{fmt(field.min_temp_c)} °C</dd>

            {/* 🔴 mean_wet_temp_c is exposed deliberately (§29.5): it is the value that reveals
                silent bug 2 to any reviewer who checks — and here it also explains why a humid
                day can still be safe. */}
            <dt>{t.wetTemp}</dt>
            <dd>{fmt(field.mean_wet_temp_c)} °C</dd>

            <dt>{t.criterion}</dt>
            <dd>{field.criterion_met ? `✓ ${t.met}` : `✗ ${t.notMet}`}</dd>

            <dt>{t.dsvToday}</dt>
            <dd>{field.dsv_today ?? 0}</dd>

            <dt>{t.dsvAccum}</dt>
            <dd>{field.dsv_accum_7d ?? 0} <span className="muted">({t.limit} 18)</span></dd>
          </dl>
          <p className="why__meta">
            {t.model}: {modelId} v{modelVersion}
            {field.cell_id && <> · {t.cell} {field.cell_id}</>}
          </p>
        </div>
      )}
    </div>
  )
}

function fmt(n: number | undefined): string {
  return n === undefined || n === null ? '—' : n.toFixed(1)
}
