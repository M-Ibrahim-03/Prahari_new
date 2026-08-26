/**
 * Indices 2 and 4 on one card — FAO-56 irrigation and mandi price momentum (deck p.2).
 *
 * 🔴 Both indices are DISTRICT-level while the disease grid is 1 km². This component says so on
 * screen, in the farmer's language, every time. The deck's "1 km² resolution" claim is earned by
 * the disease map alone, and letting these two borrow that number would be the easiest and most
 * damaging lie in the product.
 *
 * 🔴 Renders nothing when an index is absent. See FieldPayload.prahari.water — a missing balance
 * drawn as "0 mm" reads as "your field has plenty of water".
 *
 * 🔴 These indices never mention spraying and never touch a band. Irrigation and price live in a
 * different vocabulary and a different colour from safe/watch/act, so a farmer can never read
 * "sell now" as "spray now".
 */

import type { FieldPayload, Lang, MandiOption } from '../lib/types'

interface Props {
  meta: FieldPayload['prahari']
  lang: Lang
}

const T = {
  hi: {
    heading: 'खेत की और जानकारी',
    districtNote: 'यह जानकारी पूरे ज़िले के लिए है, आपके अलग खेत के लिए नहीं।',
    waterHeading: '💧 सिंचाई',
    bands: {
      wet: 'मिट्टी में पानी भरपूर है',
      adequate: 'नमी ठीक है',
      deficit: 'पानी की कमी होने लगी है',
      critical: 'फ़सल को पानी की सख़्त ज़रूरत है',
    } as Record<string, string>,
    depletion: 'मिट्टी से घटा पानी',
    threshold: 'सिंचाई की सीमा',
    rain: 'बीते दिनों की बारिश',
    daysUntil: (d: number) =>
      d === 0 ? 'सिंचाई का समय अब है' : `अनुमान: ${d} दिन बाद सिंचाई की ज़रूरत`,
    marketHeading: '₹ मंडी भाव',
    momentum: {
      rising: 'भाव चढ़ रहे हैं',
      falling: 'भाव गिर रहे हैं',
      flat: 'भाव लगभग स्थिर हैं',
      unknown: 'भाव का रुझान बताने के लिए पर्याप्त आँकड़े नहीं',
    } as Record<string, string>,
    advice: {
      'market.hold_prices_rising': 'भाव चढ़ रहे हैं — बेचने में जल्दबाज़ी न करें।',
      'market.sell_soon_prices_falling': 'भाव गिर रहे हैं — जल्दी बेचने पर विचार करें।',
      'market.no_timing_edge': 'भाव स्थिर हैं — समय का कोई ख़ास फ़ायदा नहीं।',
      'market.insufficient_data': 'आँकड़े कम हैं — कोई सलाह नहीं।',
    } as Record<string, string>,
    bestMandi: 'सबसे अधिक बचत',
    netNote: (q: number) => `${q} क्विंटल पर, आने-जाने का भाड़ा घटाकर`,
    perQuintal: 'प्रति क्विंटल',
    away: 'दूर',
    freight: 'भाड़ा',
    net: 'शुद्ध',
    snapshot: (d: string) => `भाव ${d} के हैं, आज के नहीं। मंडी जाने से पहले पता कर लें।`,
    headlineTrap: 'ध्यान दें: सबसे ऊँचा भाव हमेशा सबसे ज़्यादा बचत नहीं देता — भाड़ा घटाकर देखें।',
  },
  en: {
    heading: 'More about your land',
    districtNote: 'This information is for the whole district, not your individual field.',
    waterHeading: '💧 Irrigation',
    bands: {
      wet: 'Soil moisture is plentiful',
      adequate: 'Moisture is adequate',
      deficit: 'Water is starting to run short',
      critical: 'The crop urgently needs water',
    } as Record<string, string>,
    depletion: 'Soil water depleted',
    threshold: 'Irrigation threshold',
    rain: 'Rain in the scored window',
    daysUntil: (d: number) =>
      d === 0 ? 'Irrigation is due now' : `Estimated ${d} days until irrigation is needed`,
    marketHeading: '₹ Mandi prices',
    momentum: {
      rising: 'Prices are rising',
      falling: 'Prices are falling',
      flat: 'Prices are roughly flat',
      unknown: 'Not enough observations to report a trend',
    } as Record<string, string>,
    advice: {
      'market.hold_prices_rising': 'Prices are rising — no need to rush a sale.',
      'market.sell_soon_prices_falling': 'Prices are falling — consider selling sooner.',
      'market.no_timing_edge': 'Prices are flat — no timing advantage either way.',
      'market.insufficient_data': 'Too few observations — no advice.',
    } as Record<string, string>,
    bestMandi: 'Best net return',
    netNote: (q: number) => `on ${q} quintal, after round-trip freight`,
    perQuintal: 'per quintal',
    away: 'away',
    freight: 'Freight',
    net: 'Net',
    snapshot: (d: string) => `Prices are from ${d}, not today. Confirm before you travel.`,
    headlineTrap:
      'Note: the highest headline price does not always give the best return — freight changes the answer.',
  },
} as const

function inr(n: number): string {
  return '₹' + Math.round(n).toLocaleString('en-IN')
}

function MandiRow({ o, lang, best }: { o: MandiOption; lang: Lang; best: boolean }) {
  const t = T[lang]
  const name = lang === 'hi' ? o.mandi_hi : o.mandi
  return (
    <li className={best ? 'mandi mandi--best' : 'mandi'}>
      <span className="mandi__name">
        {best ? '★ ' : ''}
        {name}
      </span>
      <span className="mandi__meta">
        {inr(o.modal_price)} / {t.perQuintal} · {o.distance_km} km {t.away} · {t.freight}{' '}
        {inr(o.transport_cost_inr)}
      </span>
      <span className="mandi__net">
        {t.net} {inr(o.net_realisation_inr)}
      </span>
    </li>
  )
}

export function IndicesPanel({ meta, lang }: Props) {
  const t = T[lang]
  const water = meta.water
  const market = meta.market

  // Nothing to say is a valid outcome — say nothing rather than render an empty shell.
  if (!water && !market) return null

  const all = market?.best ? [market.best, ...market.alternatives] : []
  // 🔴 Only warn about the headline trap when it actually bites here, i.e. some other mandi quotes a
  // higher price than the one that nets most. A permanent warning is wallpaper; a conditional one
  // is information.
  const headlineTrap =
    market?.best != null && all.some((o) => o.modal_price > market.best!.modal_price)

  return (
    <section className="indices" aria-label={t.heading}>
      <h2 className="indices__heading">{t.heading}</h2>
      <p className="indices__scope">{t.districtNote}</p>

      {water && (
        <div className="indices__block">
          <h3 className="indices__sub">{t.waterHeading}</h3>
          <p className="indices__lead">{t.bands[water.band] ?? water.band}</p>
          <p className="indices__detail">
            {t.depletion}: {water.depletion_mm} mm · {t.threshold}: {water.raw_mm} mm · {t.rain}:{' '}
            {water.rain_mm} mm
          </p>
          {water.days_until_irrigation != null && (
            <p className="indices__detail">{t.daysUntil(water.days_until_irrigation)}</p>
          )}
        </div>
      )}

      {market && (
        <div className="indices__block">
          <h3 className="indices__sub">{t.marketHeading}</h3>
          <p className="indices__lead">
            {t.momentum[market.momentum] ?? market.momentum}
            {market.momentum !== 'unknown' && ` (${market.change_pct > 0 ? '+' : ''}${market.change_pct}%)`}
          </p>
          <p className="indices__detail">{t.advice[market.advice_key] ?? ''}</p>

          {all.length > 0 && (
            <>
              <p className="indices__detail indices__detail--strong">
                {t.bestMandi}: {t.netNote(market.load_quintals)}
              </p>
              <ul className="mandi-list">
                {all.map((o) => (
                  <MandiRow key={o.mandi} o={o} lang={lang} best={o.mandi === market.best?.mandi} />
                ))}
              </ul>
              {headlineTrap && <p className="indices__warn">{t.headlineTrap}</p>}
            </>
          )}

          {/* 🔴 Non-negotiable: a rupee figure never appears without its date. */}
          <p className="indices__stale">{t.snapshot(market.observed_on)}</p>
        </div>
      )}
    </section>
  )
}
