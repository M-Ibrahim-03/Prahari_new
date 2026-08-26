import { useState } from 'react'
import { DataAge } from './components/DataAge'
import { DegradationNotice } from './components/DegradationNotice'
import { FieldCard } from './components/FieldCard'
import { MapScreen } from './components/MapScreen'
import { SprayScreen } from './components/SprayScreen'
import { BAND, bandSemantic } from './lib/bandToSemantic'
import { sortWorstFirst, type Lang } from './lib/types'
import { useFieldPayload } from './lib/useFieldPayload'

const DISTRICT = 'farrukhabad'
// Fallback view centre, used only until the map can frame the farmer's own fields.
const DISTRICT_CENTER = { lat: 27.40, lon: 79.60 }

/**
 * Demo views. Late blight is a rabi-season disease, so a live August run correctly returns `safe`
 * for every cell and the act/watch path — the spray advisory, the loud card, the chained ledger
 * alert — never appears. These entries point at artefacts built by
 * `python -m pipeline.nightly --scenario NAME`, which runs SYNTHETIC WEATHER through the real
 * engine. Selecting one is how the alerting path gets demonstrated in August without faking a
 * result; the engine still decides every band.
 *
 * Picked up from `?view=` too, so a demo can be linked to directly.
 */
const VIEWS = [
  { id: 'farrukhabad', hi: 'लाइव पूर्वानुमान', en: 'Live forecast' },
  { id: 'farrukhabad_blight_outbreak', hi: 'डेमो: झुलसा प्रकोप', en: 'Demo: blight outbreak' },
  { id: 'farrukhabad_borderline_watch', hi: 'डेमो: सीमा रेखा', en: 'Demo: borderline' },
  { id: 'farrukhabad_dry_spell', hi: 'डेमो: सूखा दौर', en: 'Demo: dry spell' },
] as const

function initialView(): string {
  const q = new URLSearchParams(location.search).get('view')
  return VIEWS.some((v) => v.id === q) ? (q as string) : DISTRICT
}

type Screen = 'today' | 'map' | 'spray'

const L = {
  hi: {
    title: 'प्रहरी', addField: 'दूसरा खेत जोड़ें', demoNote: 'डेमो खेत',
    loading: 'लोड हो रहा है…',
    emptyTitle: 'कोई खेत नहीं', emptyBody: 'अपना पहला खेत जोड़ें।',
    errorTitle: 'डेटा नहीं मिला', errorRetry: 'फिर कोशिश करें',
    errorBody: 'इंटरनेट जाँचें। सहेजा हुआ डेटा भी नहीं मिला।',
    nav: { today: 'आज', map: 'नक्शा', spray: 'छिड़काव', ask: 'पूछें', more: 'और' },
    soon: 'अगले चरण में',
    demoTitle: '⚠️ यह असली पूर्वानुमान नहीं है',
    demoBody: 'यह बनाया हुआ मौसम है, सिर्फ़ दिखाने के लिए। इस पर छिड़काव का फ़ैसला न लें।',
    view: 'दृश्य',
  },
  en: {
    title: 'PRAHARI', addField: 'Add another field', demoNote: 'demo fields',
    loading: 'Loading…',
    emptyTitle: 'No fields yet', emptyBody: 'Add your first field.',
    errorTitle: 'Could not load data', errorRetry: 'Try again',
    errorBody: 'Check your connection. No saved data was found either.',
    nav: { today: 'Today', map: 'Map', spray: 'Spray', ask: 'Ask', more: 'More' },
    soon: 'Coming next',
    demoTitle: '⚠️ This is not a real forecast',
    demoBody: 'Synthetic weather, shown to demonstrate the alert path. Do not spray on this.',
    view: 'View',
  },
}

export default function App() {
  const [lang, setLang] = useState<Lang>('hi')
  const [screen, setScreen] = useState<Screen>('today')
  const [view, setView] = useState<string>(initialView)
  const state = useFieldPayload(view)
  const t = L[lang]
  const fields = state.status === 'ready' ? state.data.fields : []
  const isScenario = state.status === 'ready' && state.data.prahari.data_status === 'scenario'

  function changeView(next: string) {
    setView(next)
    // Keep the URL in step so a demo view can be shared or reloaded into.
    const url = new URL(location.href)
    if (next === DISTRICT) url.searchParams.delete('view')
    else url.searchParams.set('view', next)
    history.replaceState(null, '', url)
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1 className="topbar__title">{t.title}</h1>
        <select
          className="topbar__view"
          value={view}
          onChange={(e) => changeView(e.target.value)}
          aria-label={t.view}
        >
          {VIEWS.map((v) => (
            <option key={v.id} value={v.id}>{lang === 'hi' ? v.hi : v.en}</option>
          ))}
        </select>
        <button
          className="topbar__lang"
          onClick={() => setLang(lang === 'hi' ? 'en' : 'hi')}
          aria-label={lang === 'hi' ? 'Switch to English' : 'हिंदी में बदलें'}
        >
          {lang === 'hi' ? 'हिंदी' : 'EN'}
        </button>
      </header>

      <main className="main">
        {/* 🔴 Synthetic weather is called out ABOVE everything, on every screen, and it replaces
            the freshness banner rather than sitting beside it. A scenario's run_id is the moment
            it was computed, so DataAge would truthfully report "updated just now" about weather
            dated next December — a true sentence that leaves a false impression. The one thing
            this app must never do is let invented data pass for a forecast. */}
        {isScenario && (
          <div className="panel panel--demo" role="alert">
            <h2>{t.demoTitle}</h2>
            <p>{t.demoBody}</p>
            <p className="muted mono">{state.data.prahari.degradation.join(' · ')}</p>
          </div>
        )}

        {screen === 'map' ? (
          <MapScreen fields={fields} lang={lang} center={DISTRICT_CENTER} />
        ) : (
          <>
            {/* §21.5 — all five states defined, not just success. */}
            {state.status === 'loading' && <SkeletonList label={t.loading} />}

            {state.status === 'error' && (
              <div className="panel panel--error" role="alert">
                <h2>{t.errorTitle}</h2>
                <p>{t.errorBody}</p>
                <p className="muted mono">{state.message}</p>
                <button className="btn" onClick={() => location.reload()}>{t.errorRetry}</button>
              </div>
            )}

            {state.status === 'ready' && (screen === 'spray' ? (
              <SprayScreen
                fields={state.data.fields}
                lang={lang}
                modelId={state.data.prahari.model.id}
                modelVersion={state.data.prahari.model.version}
                runId={state.data.prahari.run_id}
              />
            ) : (
              <>
                {/* Freshness is meaningless for synthetic weather, so the demo banner above stands
                    in for it rather than both being shown. */}
                {!isScenario && (
                  <DataAge
                    runId={state.data.prahari.run_id}
                    lang={lang}
                    fromCache={state.fromCache}
                  />
                )}

                {/* §28.3 — the ladder, in plain language, with the rung named for whoever is
                    reading over the farmer's shoulder. Renders nothing at L0. */}
                <DegradationNotice
                  dataStatus={state.data.prahari.data_status}
                  degradation={state.data.prahari.degradation}
                  lang={lang}
                />

                {state.data.fields.length === 0 ? (
                  <div className="panel">
                    <h2>{t.emptyTitle}</h2>
                    <p>{t.emptyBody}</p>
                  </div>
                ) : (
                  sortWorstFirst(state.data.fields, (b) => bandSemantic(b).rank).map((f, i) => (
                    <FieldCard
                      key={f.id}
                      field={f}
                      lang={lang}
                      primary={i === 0}
                      modelId={state.data.prahari.model.id}
                      modelVersion={state.data.prahari.model.version}
                    />
                  ))
                )}

                <button className="addfield" disabled title={t.soon}>
                  ➕ {t.addField} <span className="muted">({t.soon})</span>
                </button>

                <p className="footnote">
                  {t.demoNote} · {state.data.prahari.field_count} · engine{' '}
                  <span className="mono">{state.data.prahari.model.engine_git_sha}</span>
                </p>
              </>
            ))}
          </>
        )}
      </main>

      <nav className="bottomnav">
        <button
          className={screen === 'today' ? 'bottomnav__item bottomnav__item--active' : 'bottomnav__item'}
          onClick={() => setScreen('today')}
        >
          🏠<span>{t.nav.today}</span>
        </button>
        <button
          className={screen === 'map' ? 'bottomnav__item bottomnav__item--active' : 'bottomnav__item'}
          onClick={() => setScreen('map')}
        >
          🗺️<span>{t.nav.map}</span>
        </button>
        <button
          className={screen === 'spray' ? 'bottomnav__item bottomnav__item--active' : 'bottomnav__item'}
          onClick={() => setScreen('spray')}
        >
          💊<span>{t.nav.spray}</span>
        </button>
        <button className="bottomnav__item" disabled title={t.soon}>🎤<span>{t.nav.ask}</span></button>
        <button className="bottomnav__item" disabled title={t.soon}>☰<span>{t.nav.more}</span></button>
      </nav>
    </div>
  )
}

/** 🔴 Skeleton matching the final layout — never a spinner over a blank screen (§21.5). */
function SkeletonList({ label }: { label: string }) {
  return (
    <div aria-busy="true" aria-label={label}>
      {[0, 1, 2].map((i) => (
        <article className="card card--skeleton" key={i}>
          <header className="card__band" style={{ background: 'var(--border)' }} />
          <div className="card__body">
            <div className="sk sk--title" />
            <div className="sk sk--line" />
            <div className="sk sk--play" />
          </div>
        </article>
      ))}
      <span className="sr-only">{label}</span>
      {/* Keep the band map referenced so the single source of truth cannot be tree-shaken
          into irrelevance during refactors. */}
      <span hidden>{Object.keys(BAND).length}</span>
    </div>
  )
}
