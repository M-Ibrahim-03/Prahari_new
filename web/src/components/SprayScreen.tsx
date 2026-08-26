import '../styles/parts/spray.css'
import { useState } from 'react'
import { BAND, bandSemantic, type Band } from '../lib/bandToSemantic'
import type { AudioMode } from '../lib/audio'
import { describeAge, sortWorstFirst, type FieldEntry, type Lang } from '../lib/types'
import { PlayButton } from './PlayButton'

const L = {
  hi: {
    actTitle: 'आज छिड़काव करना है',
    actSub: { one: 'एक खेत में', many: '{n} खेतों में' },
    noSprayTitle: 'आज छिड़काव नहीं करना है',
    watchSub: { one: 'पर एक खेत पर नज़र रखें', many: 'पर {n} खेतों पर नज़र रखें' },
    clearTitle: 'सब ठीक है',
    clearBody: 'आज किसी खेत में छिड़काव की ज़रूरत नहीं है।',
    clearBodyPartial: 'जिन खेतों का हिसाब हुआ, उनमें आज छिड़काव की ज़रूरत नहीं है।',
    keepLooking: 'खेत देखते रहें।',
    noFieldsTitle: 'कोई खेत नहीं',
    noFieldsBody: 'पहले अपना खेत जोड़ें। उसके बाद छिड़काव की सलाह यहाँ दिखेगी।',
    actHead: 'क्या करना है',
    watchHead: 'इन खेतों पर नज़र रखें',
    unknownHead: 'इन खेतों की जानकारी नहीं',
    unknownBody: 'इनके बारे में हम कुछ नहीं कह सकते।',
    whenLabel: 'कब',
    noSprayYet: 'अभी छिड़काव नहीं',
    noData: 'इस खेत की जानकारी नहीं',
    doseTitle: 'कौन सी दवा और कितनी मात्रा?',
    doseBody: 'यह ऐप दवा का नाम और मात्रा नहीं बताता। अपने KVK या कृषि अधिकारी से पूछें।',
    doseWhy: 'ज़िले की मंज़ूर की गई दवाओं की सूची इस ऐप में अभी डाली नहीं गई है।',
    windowBlocked: {
      RAIN_NOW: 'बारिश के घंटे छोड़ दिए',
      RAIN_AFTER: 'छिड़काव बारिश से पहले पूरा हो',
      WIND_HIGH: 'तेज़ हवा के घंटे छोड़ दिए',
      WIND_CALM: 'बिलकुल शांत हवा के घंटे छोड़ दिए',
      TEMP_HIGH: 'ज़्यादा गर्मी के घंटे छोड़ दिए',
      DARK: 'अँधेरे के घंटे छोड़ दिए',
      TOO_LATE: 'बीमारी शुरू होने के बाद के घंटे छोड़ दिए',
    } as Record<string, string>,
    notBuilt: 'अभी नहीं बना',
    staleWarn: 'यह पुराना डेटा है। छिड़काव का फ़ैसला इस पर न लें — नया डेटा आने तक रुकें।',
    deviceVoice: 'फ़ोन की आवाज़ (रिकॉर्डेड आवाज़ अभी नहीं)',
    noVoice: 'इस फ़ोन पर आवाज़ नहीं चली — ऊपर लिखा पढ़ें या किसी से पढ़वाएँ',
    model: 'मॉडल',
    run: 'हिसाब का समय',
  },
  en: {
    actTitle: 'Spray today',
    actSub: { one: 'in one field', many: 'in {n} fields' },
    noSprayTitle: 'No spraying today',
    watchSub: { one: 'but keep watch on one field', many: 'but keep watch on {n} fields' },
    clearTitle: 'All clear',
    clearBody: 'No field needs spraying today.',
    clearBodyPartial: 'Of the fields we could compute, none needs spraying today.',
    keepLooking: 'Keep watching your field.',
    noFieldsTitle: 'No fields yet',
    noFieldsBody: 'Add a field first. Spray advice will appear here afterwards.',
    actHead: 'What to do',
    watchHead: 'Keep watch on these fields',
    unknownHead: 'No data for these fields',
    unknownBody: 'We cannot say anything about these.',
    whenLabel: 'When',
    noSprayYet: 'No spraying yet',
    noData: 'No data for this field',
    doseTitle: 'Which medicine, and how much?',
    doseBody: 'This app does not name a medicine or an amount. Ask your KVK or agriculture officer.',
    doseWhy: "The district's approved list has not been loaded into this app yet.",
    windowNote: 'Best hours are shown above.',
    windowBlocked: {
      RAIN_NOW: 'rain hours skipped',
      RAIN_AFTER: 'spray must finish before the rain',
      WIND_HIGH: 'high-wind hours skipped',
      WIND_CALM: 'dead-calm hours skipped',
      TEMP_HIGH: 'too-hot hours skipped',
      DARK: 'dark hours skipped',
      TOO_LATE: 'hours after infection onset skipped',
    } as Record<string, string>,
    notBuilt: 'Not yet implemented',
    staleWarn: 'This data is old. Do not decide a spray on it — wait for fresh data.',
    deviceVoice: "Phone's own voice (recorded audio not yet available)",
    noVoice: 'Voice did not play on this phone — read the text above',
    model: 'Model',
    run: 'Run',
  },
}

/**
 * The spray screen (PRD §13.3) — one question: what, if anything, do I do to my crop, and when.
 *
 * 🔴 This screen gives TIMING ONLY. It names no product, no active ingredient, no dose, no
 * concentration, no tank mix, no spray volume, no re-entry or pre-harvest interval and no PPE.
 * FR-7.10 and §39.2: recommending a product and dose is a licensed advisory act, and this repo
 * holds no district-approved chemical list to recommend from. Where a production build prints a
 * dose, this renders an explicit refusal that routes to a human (see `doseTitle` below). Every
 * sentence of advice on this screen is text the engine already wrote into the artefact
 * (advisory_templates.yaml → engine/advisory.py); none of it is composed here.
 *
 * 🔴 The all-clear is the common and correct answer for most of the year (late blight is a rabi
 * disease), so it is rendered as a confident positive verdict in the safe band's own colour —
 * never as an empty state. A farmer who reads a blank screen concludes the app is broken.
 */
export function SprayScreen({
  fields,
  lang,
  modelId,
  modelVersion,
  runId,
}: {
  fields: FieldEntry[]
  lang: Lang
  modelId: string
  modelVersion: string
  runId: string
}) {
  const t = L[lang]
  const g = groupByBand(fields)
  const needsSpray = g.act.length > 0
  const hasWatch = g.watch.length > 0

  // 🔴 Stale data qualifies the verdict, so it is stated ABOVE the advice rather than beside it.
  // L7: acting on a three-day-old forecast is the failure this whole product exists to prevent,
  // and a spray decision is the most expensive place for it to happen.
  //
  // A blank runId means "no payload yet", which is NOT the same as "age unknown": describeAge('')
  // reports a NaN age as very_stale, which would fire a red "this data is old" alarm over a screen
  // that has no data at all. A non-blank but unparseable runId still warns, deliberately — an age
  // we cannot compute is a reason for caution, not for silence.
  const known = runId.trim() !== ''
  const age = describeAge(runId)
  const stale = known && (age.freshness === 'stale' || age.freshness === 'very_stale')

  // The verdict takes the worst band present: the answer to "do I spray" is driven by the one
  // field in trouble, never by the average across parcels.
  const verdict = bandSemantic(needsSpray ? 'act' : hasWatch ? 'watch' : 'safe')

  return (
    <div className="spray">
      {stale && (
        <p className="spray__stale" role="alert">
          <span aria-hidden="true">⚠️</span> {t.staleWarn}
        </p>
      )}

      {fields.length === 0 ? (
        <div className="panel">
          <h2>{t.noFieldsTitle}</h2>
          <p>{t.noFieldsBody}</p>
        </div>
      ) : (
        <>
          {/* Band colour and icon come from the one file allowed to own them (§22.3), and the
              text label is always present beside the icon — colour is never the only signal. */}
          <section
            className="spray__verdict"
            style={{ background: verdict.color, color: verdict.on }}
            role={needsSpray ? 'alert' : undefined}
          >
            <span className="spray__verdict-icon" aria-hidden="true">{verdict.icon}</span>
            <div className="spray__verdict-copy">
              <h2 className="spray__verdict-title">
                {needsSpray ? t.actTitle : hasWatch ? t.noSprayTitle : t.clearTitle}
              </h2>
              {needsSpray && <p className="spray__verdict-sub">{plural(t.actSub, g.act.length)}</p>}
              {!needsSpray && hasWatch && (
                <p className="spray__verdict-sub">{plural(t.watchSub, g.watch.length)}</p>
              )}
              {!needsSpray && !hasWatch && (
                <p className="spray__verdict-sub">
                  {/* 🔴 Never claim safety for a field we could not compute. A field that resolved
                      to no cell is excluded from the all-clear by wording, not hidden from it. */}
                  {g.unknown.length > 0 ? t.clearBodyPartial : t.clearBody} {t.keepLooking}
                </p>
              )}
            </div>
          </section>

          {needsSpray && (
            <section className="spray__section">
              <h3 className="spray__section-head">{t.actHead}</h3>
              {g.act.map((f) => (
                <FieldAdvice key={f.id} field={f} lang={lang} t={t} primary />
              ))}
            </section>
          )}

          {hasWatch && (
            <section className="spray__section">
              <h3 className="spray__section-head">{t.watchHead}</h3>
              {g.watch.map((f) => (
                <FieldAdvice key={f.id} field={f} lang={lang} t={t} primary={false} />
              ))}
            </section>
          )}

          {/* 🔴 The honest empty state. A farmer told to spray immediately asks "with what, and how
              much" — and this is the one screen in the app where a plausible-looking invented
              answer could poison a family or breach a residue limit that costs them the sale.
              Shown for 'watch' too, because the watch advisory says to get medicine ready.
              Dashed border is this codebase's existing visual language for not-yet-built. */}
          {(needsSpray || hasWatch) && (
            <section className="spray__note">
              <h3 className="spray__note-title">
                <span aria-hidden="true">ℹ️</span> {t.doseTitle}
              </h3>
              <p className="spray__note-body">{t.doseBody}</p>
              <p className="spray__note-why">{t.doseWhy}</p>
              <span className="spray__tag">{t.notBuilt}</span>
            </section>
          )}

          {g.unknown.length > 0 && (
            <section className="spray__section">
              <h3 className="spray__section-head">{t.unknownHead}</h3>
              <p className="spray__unknown-body">{t.unknownBody}</p>
              {g.unknown.map((f) => (
                <FieldAdvice key={f.id} field={f} lang={lang} t={t} primary={false} />
              ))}
            </section>
          )}

          {/* Attribution: which model, which run. An officer checking a disputed call needs to know
              exactly what produced it, and a farmer deserves to see the advice is not anonymous. */}
          {known && (
            <p className="spray__meta">
              {t.model}: {modelId} v{modelVersion} · {t.run} {runId}
            </p>
          )}
        </>
      )}
    </div>
  )
}

/**
 * One field's advice. The timing gets its own emphasised row because it is the question this
 * screen answers; `what` and `why` are the engine's own sentences, shown verbatim.
 */
function FieldAdvice({
  field,
  lang,
  t,
  primary,
}: {
  field: FieldEntry
  lang: Lang
  t: (typeof L)[Lang]
  primary: boolean
}) {
  const sem = bandSemantic(field.band)
  const advisory = field.advisory?.[lang]
  const name = lang === 'hi' ? field.name_hi : field.name_en
  const isWatch = field.band === 'watch'
  const [mode, setMode] = useState<AudioMode | null>(null)

  return (
    <article className="spray__row">
      <span className="spray__chip" style={{ background: sem.color, color: sem.on }}>
        <span aria-hidden="true">{sem.icon}</span>
        {lang === 'hi' ? sem.hi : sem.en}
      </span>

      <h4 className="spray__name">{name}</h4>
      {field.area_local && <p className="spray__area">{field.area_local}</p>}

      {advisory ? (
        <>
          <p className="spray__what">{advisory.what}</p>

          {/* 🔴 Watch means the criterion has not been met: say "not yet" in words, next to the
              amber chip, so the farmer does not read amber as a quiet instruction to spray. */}
          {isWatch && (
            <p className="spray__badge">
              <span aria-hidden="true">⏳</span> {t.noSprayYet}
            </p>
          )}

          <div className="spray__when">
            <span className="spray__when-icon" aria-hidden="true">🕘</span>
            <span className="spray__when-copy">
              <span className="spray__when-label">{t.whenLabel}</span>
              <span className="spray__when-text">{advisory.when}</span>
              {/* Why the window ends where it does (§13.2). Timing without a reason reads as
                  arbitrary; the reason is what lets a farmer trust "not this afternoon". */}
              {field.band === 'act' && field.spray_blocked_by && field.spray_blocked_by.length > 0 && (
                <span className="spray__when-reason">
                  {field.spray_blocked_by
                    .map((code) => t.windowBlocked[code])
                    .filter(Boolean)
                    .join(' · ')}
                </span>
              )}
            </span>
          </div>

          <p className="spray__why">
            <span aria-hidden="true">💧</span> {advisory.why}
          </p>

          <PlayButton advisory={advisory} lang={lang} primary={primary} onMode={setMode} />

          {/* Which voice path actually ran (degradation L5). A button that plays nothing and says
              nothing reads as a broken app; the advisory text sits directly above, but only a
              farmer who knows the audio failed will go back and read it. */}
          {mode === 'device_speech' && <p className="spray__why">ℹ️ {t.deviceVoice}</p>}
          {mode === 'unavailable' && (
            <p className="spray__badge" role="alert">⚠️ {t.noVoice}</p>
          )}
        </>
      ) : (
        // No advisory at all — an unresolved field. The band map already carries the honest
        // explanation for that case, so it is reused rather than restated.
        <>
          <p className="spray__what">{t.noData}</p>
          <p className="spray__why">{lang === 'hi' ? sem.action_hi : sem.action_en}</p>
        </>
      )}
    </article>
  )
}

/**
 * 🔴 An unrecognised band becomes 'unknown', never 'safe'. Defaulting an unreadable band to safe
 * would print "nothing needs spraying" over a field the engine never computed.
 */
function groupByBand(fields: FieldEntry[]): Record<Band, FieldEntry[]> {
  const out: Record<Band, FieldEntry[]> = { act: [], watch: [], safe: [], unknown: [] }
  for (const f of sortWorstFirst(fields, (b) => bandSemantic(b).rank)) {
    out[f.band in BAND ? (f.band as Band) : 'unknown'].push(f)
  }
  return out
}

/** Hindi needs the oblique plural ("खेतों"), so both forms are authored in the table. */
function plural(form: { one: string; many: string }, n: number): string {
  return n === 1 ? form.one : form.many.replace('{n}', String(n))
}
