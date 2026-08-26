import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { bandSemantic } from '../lib/bandToSemantic'
import type { FieldEntry, Lang } from '../lib/types'

declare const __MAPTILER_KEY__: string

const L_TEXT = {
  hi: {
    locate: 'मैं यहाँ हूँ', locating: 'ढूँढ रहे हैं…',
    noKey: 'नक्शा उपलब्ध नहीं (कुंजी नहीं मिली)',
    denied: 'फ़ोन ने जगह बताने से मना किया',
    far: 'आप अपने खेतों से दूर हैं',
    attribution: 'नक्शा: MapTiler · उपग्रह चित्र',
  },
  en: {
    locate: 'I am here', locating: 'Locating…',
    noKey: 'Map unavailable (no key configured)',
    denied: 'Phone denied location access',
    far: 'You are far from your fields',
    attribution: 'Map: MapTiler · satellite imagery',
  },
}

/**
 * §21.2 — the farmer's map.
 *
 * 🔴 What is deliberately ABSENT is the specification:
 *   - NO computation grid, NO cell boundaries. The 0.02° cells are an implementation detail; a
 *     farmer seeing a chequerboard over their village learns that the system is guessing in
 *     squares, which is both true and useless to them.
 *   - NO district choropleth. A red district is how a false alarm becomes a panic, and it tells
 *     a farmer nothing about their own soil.
 *   - NO invented field boundaries. This project has no surveyed plot geometry (hackathon: no
 *     field data), so fields are shown as points at their registered centre. Drawing a plausible
 *     rectangle would be fabricating a boundary the farmer might trust for spraying decisions.
 *
 * What is present: satellite imagery a farmer can actually recognise their land in, their own
 * fields marked and labelled in their own words, and a "you are here" button.
 *
 * Raster tiles via Leaflet rather than vector tiles via MapLibre: ~40 KB of library instead of
 * ~200 KB, which matters more than smooth zooming on a 2G connection.
 */
export function MapScreen({
  fields,
  lang,
  center,
}: {
  fields: FieldEntry[]
  lang: Lang
  center: { lat: number; lon: number }
}) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const meRef = useRef<L.CircleMarker | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [locating, setLocating] = useState(false)
  const t = L_TEXT[lang]
  const key = __MAPTILER_KEY__

  useEffect(() => {
    if (!hostRef.current || mapRef.current || !key) return

    const map = L.map(hostRef.current, {
      center: [center.lat, center.lon],
      zoom: 13,
      zoomControl: true,
      attributionControl: true,
    })
    mapRef.current = map

    L.tileLayer(
      `https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key=${key}`,
      {
        maxZoom: 18,
        // Attribution is a licence condition of the free MapTiler tier, not decoration.
        attribution:
          '&copy; <a href="https://www.maptiler.com/copyright/">MapTiler</a> &copy; ' +
          '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      },
    ).addTo(map)

    const markers: L.Layer[] = []
    for (const f of fields) {
      const sem = bandSemantic(f.band)
      const name = lang === 'hi' ? f.name_hi : f.name_en
      const marker = L.circleMarker([f.center.lat, f.center.lon], {
        radius: 12,
        color: '#FFFFFF',
        weight: 3,
        fillColor: sem.color,
        fillOpacity: 1,
      }).addTo(map)
      // Band label travels with the marker: colour alone is not a signal (§21.3).
      marker.bindTooltip(`${sem.icon} ${name}`, {
        permanent: true,
        direction: 'top',
        className: 'map__label',
      })
      markers.push(marker)
    }

    // Frame the farmer's own fields, not the district. The district extent is a system concept.
    // invalidateSize first: Leaflet measures the container on creation, which here happens before
    // the stylesheet gives it a height, so without this the fit is computed against a zero-size
    // box and only one field ends up on screen.
    const fitToFields = () => {
      map.invalidateSize()
      if (fields.length === 0) return
      const bounds = L.latLngBounds(fields.map((f) => [f.center.lat, f.center.lon] as [number, number]))
      map.fitBounds(bounds.pad(0.35), { maxZoom: 15 })
    }
    fitToFields()
    const raf = requestAnimationFrame(fitToFields)

    return () => {
      cancelAnimationFrame(raf)
      markers.forEach((m) => m.remove())
      map.remove()
      mapRef.current = null
    }
  }, [fields, lang, center.lat, center.lon, key])

  function locate() {
    const map = mapRef.current
    if (!map || !('geolocation' in navigator)) {
      setStatus(t.denied)
      return
    }
    setLocating(true)
    setStatus(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false)
        const { latitude, longitude } = pos.coords
        meRef.current?.remove()
        meRef.current = L.circleMarker([latitude, longitude], {
          radius: 9, color: '#FFFFFF', weight: 3, fillColor: '#2563EB', fillOpacity: 1,
        }).addTo(map)
        map.setView([latitude, longitude], 16)

        // Say so when the fix is nowhere near the registered fields, instead of silently
        // recentring on another district and letting the farmer assume the map moved to them.
        const far = fields.every(
          (f) => Math.abs(f.center.lat - latitude) > 0.5 || Math.abs(f.center.lon - longitude) > 0.5,
        )
        if (far && fields.length > 0) setStatus(t.far)
      },
      () => {
        setLocating(false)
        setStatus(t.denied)
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    )
  }

  if (!key) {
    return (
      <div className="panel panel--error" role="alert">
        <p>{t.noKey}</p>
        <p className="muted mono">MAPTILER_KEY missing from .env</p>
      </div>
    )
  }

  return (
    <div className="map">
      <div className="map__canvas" ref={hostRef} />
      <button className="btn map__locate" onClick={locate} disabled={locating}>
        📍 {locating ? t.locating : t.locate}
      </button>
      {status && <p className="map__status" role="status">{status}</p>}
    </div>
  )
}
