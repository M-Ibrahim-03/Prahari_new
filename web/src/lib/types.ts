/** Types mirroring the artefact contracts written by pipeline/nightly.py. */

export type Lang = 'hi' | 'en'

export interface Advisory {
  lang: string
  which: string
  what: string
  why: string
  when: string
  text: string
  body_text: string
  action: string
  band_label: string
  audio_key: string
  name_audio_key: string
  body_audio_key: string
  audio_segments: string[]
}

export interface FieldEntry {
  id: string
  name_hi: string
  name_en: string
  crop: string
  area_local?: string | null
  center: { lat: number; lon: number }
  cell_id: string | null
  band: string
  risk: number
  physics_risk?: number
  ml_delta?: number
  criterion_met?: boolean
  dsv_today?: number
  dsv_accum_7d?: number
  wet_hours?: number
  min_temp_c?: number
  mean_wet_temp_c?: number
  firing_model?: string
  firing_pathogen?: string
  confidence?: number
  confidence_label?: string
  spray_start_hour?: number

  spray_end_hour?: number
  spray_quality?: number
  spray_blocked_by?: string[]
  advisory?: Record<string, Advisory>
  note?: string
}


export interface FieldPayload {
  prahari: {
    schema_version: string
    run_id: string
    district: string
    model: { id: string; version: string; engine_git_sha: string }
    /**
     * 'scenario' marks synthetic demo weather (adapters/scenario.py). It is a first-class value
     * rather than a flavour of 'degraded' because the UI must treat it differently: degraded data
     * is real data with something missing, whereas scenario data is not a forecast at all and the
     * freshness banner is meaningless for it.
     */
    data_status: 'fresh' | 'stale' | 'degraded' | 'scenario'
    degradation: string[]
    languages: string[]
    field_count: number
    distinct_audio_clips: number
    distinct_body_clips: number
    /**
     * Index 2 — FAO-56 root-zone water balance (engine/water.py).
     *
     * 🔴 Optional, and the UI MUST omit the card when it is absent rather than render zeros: a
     * missing balance shown as 0 mm depletion reads as "no water stress", which is a confident
     * wrong answer. `resolution` is 'district_mean', NOT the 1 km² of the disease grid.
     */
    water?: {
      band: 'wet' | 'adequate' | 'deficit' | 'critical'
      depletion_mm: number
      raw_mm: number
      taw_mm: number
      stress_coefficient: number
      days_until_irrigation: number | null
      rain_mm: number
      etc_mm: number
      hours_scored: number
      resolution: 'district_mean'
      assumptions: string[]
    }
    /**
     * Index 4 — mandi price momentum (engine/market.py).
     *
     * 🔴 `is_snapshot` is always true in this build and `observed_on` is the date the prices were
     * captured. Never render a rupee figure from this object without also rendering that date.
     * Every comparison is on net-of-transport realisation, so the highest `modal_price` is often
     * NOT `best`.
     */
    market?: {
      momentum: 'rising' | 'flat' | 'falling' | 'unknown'
      change_pct: number
      latest_price: number
      mean_price: number
      advice_key: string
      best: MandiOption | null
      alternatives: MandiOption[]
      load_quintals: number
      transport_inr_per_km: number
      commodity: string
      unit: string
      observed_on: string
      source: string
      is_snapshot: boolean
      caveats: string[]
    }
  }
  fields: FieldEntry[]
}

export interface MandiOption {
  mandi: string
  mandi_hi: string
  modal_price: number
  distance_km: number
  transport_cost_inr: number
  net_price_per_quintal: number
  /** Net of round-trip transport for `load_quintals`. This is what the ranking sorts on. */
  net_realisation_inr: number
  /** What the headline price alone suggested, before transport ate into it. */
  gross_premium_inr: number
}

/**
 * 🔴 Staleness is computed on the CLIENT from the artefact's own timestamp, never trusted from
 * a server flag (PRD §28.3 L11: "client detects staleness from artefact timestamp and says so").
 * L7 is the thesis of the ladder — a stale forecast shown without saying so is the failure that
 * makes a farmer spray on three-day-old information.
 */
export type Freshness = 'fresh' | 'aging' | 'stale' | 'very_stale'

export interface AgeInfo {
  freshness: Freshness
  hours: number
  hi: string
  en: string
}

export function describeAge(runId: string, now: Date = new Date()): AgeInfo {
  const then = new Date(runId)
  const hours = (now.getTime() - then.getTime()) / 3_600_000

  // Negative age means the artefact is timestamped in the future — a clock problem on one side.
  // Say so rather than silently rendering it as fresh.
  if (!isFinite(hours) || isNaN(hours)) {
    return { freshness: 'very_stale', hours: NaN, hi: 'समय अज्ञात', en: 'Unknown age' }
  }

  const fmt = (n: number) => Math.max(0, Math.round(n))
  if (hours < 0) {
    return { freshness: 'aging', hours, hi: 'समय की जाँच करें', en: 'Check device clock' }
  }
  if (hours < 24) {
    const h = fmt(hours)
    return {
      freshness: 'fresh',
      hours,
      hi: h < 1 ? 'अभी अपडेट हुआ' : `${h} घंटे पहले का डेटा`,
      en: h < 1 ? 'Updated just now' : `Data from ${h} hour${h === 1 ? '' : 's'} ago`,
    }
  }
  const days = fmt(hours / 24)
  if (hours < 48) {
    return { freshness: 'aging', hours, hi: 'कल का डेटा', en: "Yesterday's data" }
  }
  if (hours < 72) {
    return { freshness: 'stale', hours, hi: `${days} दिन पुराना डेटा`, en: `Data is ${days} days old` }
  }
  return { freshness: 'very_stale', hours, hi: `${days} दिन पुराना डेटा`, en: `Data is ${days} days old` }
}

/** Worst band first (§21.1) — defensive re-sort; the pipeline already orders the payload. */
export function sortWorstFirst(fields: FieldEntry[], rank: (b: string) => number): FieldEntry[] {
  return [...fields].sort((a, b) => rank(a.band) - rank(b.band) || b.risk - a.risk)
}
