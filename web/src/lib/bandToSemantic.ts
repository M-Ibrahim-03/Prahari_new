/**
 * 🔴 The ONLY place a band maps to a colour, icon, or label (PRD §22.3).
 * Anything hardcoding '#DC2626' or 'red' elsewhere in this app is a bug.
 *
 * Why this file is load-bearing: a band appears on cards, maps, timelines, notifications and
 * the officer console. Any one of those hardcoding a colour creates drift where the same risk
 * looks different in two places — which quietly destroys the reliability of the product's core
 * vocabulary. One file, imported everywhere, makes drift impossible.
 */
export type Band = 'safe' | 'watch' | 'act' | 'unknown'

export interface BandSemantic {
  color: string
  on: string
  /** 🔴 Colour is never the only signal (§21.3): every band carries an icon AND a text label,
   *  for colour-blind users and for direct sunlight where colour discrimination degrades. */
  icon: string
  hi: string
  en: string
  action_hi: string
  action_en: string
  /** Sort order: worst first (§21.1). */
  rank: number
}

export const BAND: Record<Band, BandSemantic> = {
  act: {
    color: 'var(--risk-act)',
    on: 'var(--on-risk-act)',
    icon: '❗', // heavy exclamation
    hi: 'छिड़काव करें',
    en: 'Act',
    action_hi: 'बताए समय पर छिड़काव करें',
    action_en: 'Spray in the window shown',
    rank: 0,
  },
  watch: {
    color: 'var(--risk-watch)',
    on: 'var(--on-risk-watch)',
    icon: '⚠', // warning triangle
    hi: 'ध्यान दें',
    en: 'Watch',
    action_hi: 'दवा तैयार रखें',
    action_en: 'Get medicine ready',
    rank: 1,
  },
  safe: {
    color: 'var(--risk-safe)',
    on: 'var(--on-risk-safe)',
    icon: '✓', // check
    hi: 'सुरक्षित',
    en: 'Safe',
    action_hi: 'कुछ नहीं करना है',
    action_en: 'Nothing to do',
    rank: 2,
  },
  // A field that resolved to no cell. Shown honestly rather than defaulted to 'safe' —
  // claiming safety we have not computed is the one thing we must never do.
  unknown: {
    color: 'var(--text-muted)',
    on: '#FFFFFF',
    icon: '?',
    hi: 'जानकारी नहीं',
    en: 'No data',
    action_hi: 'यह खेत ज़िले की सीमा से बाहर है',
    action_en: 'This field is outside the district grid',
    rank: 3,
  },
}

export function bandSemantic(band: string): BandSemantic {
  return BAND[(band as Band)] ?? BAND.unknown
}
