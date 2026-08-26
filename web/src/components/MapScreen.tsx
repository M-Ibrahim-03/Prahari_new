import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { bandSemantic } from '../lib/bandToSemantic'
import type { FieldEntry, Lang } from '../lib/types'
import { getCustomFields, saveCustomField, type CustomField } from '../lib/outbox'

declare const __MAPTILER_KEY__: string

const L_TEXT = {
  hi: {
    locate: 'मैं यहाँ हूँ', locating: 'ढूँढ रहे हैं…',
    noKey: 'नक्शा उपलब्ध नहीं (कुंजी नहीं मिली)',
    denied: 'फ़ोन ने जगह बताने से मना किया',
    far: 'आप अपने खेतों से दूर हैं',
    attribution: 'नक्शा: MapTiler · उपग्रह चित्र',
    drawBtn: '✏️ नया खेत बनाएँ',
    drawingActive: 'नक्शे पर खेत के कोने छुएँ (कम से कम 3 कोने)',
    finishDraw: 'खेत सहेजें',
    cancelDraw: 'रद्द करें',
    clearPoints: 'साफ़ करें',
    namePrompt: 'खेत का नाम (जैसे: बड़ा खेत):',
    defaultName: 'मेरा नया खेत',
    areaLabel: 'क्षेत्रफल:',
    ha: 'हेक्टेयर',
    bigha: 'बीघा (~UP मान)',
    savedToast: '✓ नया खेत सहेजा गया!',
    invalid: {
      tooFew: 'कम से कम 3 कोने चाहिए',
      tooMany: 'बहुत ज़्यादा कोने — 24 से कम रखें',
      selfIntersect: 'खेत की रेखाएँ आपस में कट रही हैं — दोबारा बनाएँ',
      tooSmall: 'क्षेत्र बहुत छोटा है — कोने ठीक से रखें',
      tooBig: 'क्षेत्र बहुत बड़ा है (20 हेक्टेयर से अधिक) — जाँचें',
    },
  },
  en: {
    locate: 'I am here', locating: 'Locating…',
    noKey: 'Map unavailable (no key configured)',
    denied: 'Phone denied location access',
    far: 'You are far from your fields',
    attribution: 'Map: MapTiler · satellite imagery',
    drawBtn: '✏️ Draw Field Boundary',
    drawingActive: 'Tap corners on satellite map (minimum 3 points)',
    finishDraw: 'Save Field',
    cancelDraw: 'Cancel',
    clearPoints: 'Clear Points',
    namePrompt: 'Field Name:',
    defaultName: 'My Field',
    areaLabel: 'Area:',
    ha: 'ha',
    bigha: 'bigha (~Central UP)',
    savedToast: '✓ Field boundary saved!',
    invalid: {
      tooFew: 'Need at least 3 corners',
      tooMany: 'Too many corners — keep it under 24',
      selfIntersect: 'Field edges cross each other — redraw the boundary',
      tooSmall: 'Area too small — place corners more carefully',
      tooBig: 'Area too large (over 20 ha) — please check',
    },
  },
}

function computePolygonAreaHa(coords: [number, number][]): number {
  if (coords.length < 3) return 0
  const R = 6378137 // Earth radius meters
  let area = 0
  for (let i = 0; i < coords.length; i++) {
    const j = (i + 1) % coords.length
    const lat1 = (coords[i][0] * Math.PI) / 180
    const lon1 = (coords[i][1] * Math.PI) / 180
    const lat2 = (coords[j][0] * Math.PI) / 180
    const lon2 = (coords[j][1] * Math.PI) / 180
    area += (lon2 - lon1) * (2 + Math.sin(lat1) + Math.sin(lat2))
  }
  area = Math.abs((area * R * R) / 2.0)
  return Number((area / 10000).toFixed(2)) // sqm to ha
}

// §7.4 field-boundary validation. Coords are [lat, lon]; the planar tests are exact enough at
// field scale. Returns an error key (mapped to language in the component) or null when valid.
const MAX_VERTICES = 24
const MIN_AREA_HA = 0.01
const MAX_AREA_HA = 20

function segmentsCross(
  a: [number, number], b: [number, number], c: [number, number], d: [number, number],
): boolean {
  const ccw = (p: [number, number], q: [number, number], r: [number, number]) =>
    (r[1] - p[1]) * (q[0] - p[0]) > (q[1] - p[1]) * (r[0] - p[0])
  return ccw(a, c, d) !== ccw(b, c, d) && ccw(a, b, c) !== ccw(a, b, d)
}

function isSelfIntersecting(coords: [number, number][]): boolean {
  const n = coords.length
  if (n < 4) return false
  for (let i = 0; i < n; i++) {
    const a = coords[i]
    const b = coords[(i + 1) % n]
    for (let j = i + 1; j < n; j++) {
      // Skip edges that share a vertex (adjacent, and the wrap-around pair).
      if (j === i || (j + 1) % n === i || (i + 1) % n === j) continue
      const c = coords[j]
      const dd = coords[(j + 1) % n]
      if (segmentsCross(a, b, c, dd)) return true
    }
  }
  return false
}

export function validateFieldPolygon(coords: [number, number][]): string | null {
  if (coords.length < 3) return 'tooFew'
  if (coords.length > MAX_VERTICES) return 'tooMany'
  if (isSelfIntersecting(coords)) return 'selfIntersect'
  const area = computePolygonAreaHa(coords)
  if (area < MIN_AREA_HA) return 'tooSmall'
  if (area > MAX_AREA_HA) return 'tooBig'
  return null
}

export function MapScreen({
  fields,
  lang,
  center,
  onFieldAdded,
}: {
  fields: FieldEntry[]
  lang: Lang
  center: { lat: number; lon: number }
  onFieldAdded?: (custom: CustomField) => void
}) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const meRef = useRef<L.CircleMarker | null>(null)
  const drawLayerRef = useRef<L.FeatureGroup | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [locating, setLocating] = useState(false)
  const [isDrawing, setIsDrawing] = useState(false)
  const [drawCoords, setDrawCoords] = useState<[number, number][]>([])
  const [fieldName, setFieldName] = useState('')
  const [customFields, setCustomFields] = useState<CustomField[]>(getCustomFields)
  const t = L_TEXT[lang]
  const key = __MAPTILER_KEY__

  // Initialize Map
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
        attribution:
          '&copy; <a href="https://www.maptiler.com/copyright/">MapTiler</a> &copy; ' +
          '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      },
    ).addTo(map)

    const drawLayer = new L.FeatureGroup().addTo(map)
    drawLayerRef.current = drawLayer

    // Draw baseline fields
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
      marker.bindTooltip(`${sem.icon} ${name}`, {
        permanent: true,
        direction: 'top',
        className: 'map__label',
      })
    }

    // Draw saved custom fields polygons
    for (const cf of customFields) {
      if (cf.coordinates.length >= 3) {
        const poly = L.polygon(cf.coordinates, {
          color: '#10B981',
          weight: 3,
          fillColor: '#10B981',
          fillOpacity: 0.25,
        }).addTo(map)
        const name = lang === 'hi' ? cf.name_hi : cf.name_en
        poly.bindTooltip(`📍 ${name} (${cf.area_bigha} ${lang === 'hi' ? 'बीघा' : 'bigha'})`, {
          permanent: true,
          direction: 'center',
          className: 'map__label',
        })
      }
    }

    const fitToFields = () => {
      map.invalidateSize()
      const allPoints: [number, number][] = fields.map((f) => [f.center.lat, f.center.lon])
      for (const cf of customFields) {
        for (const pt of cf.coordinates) allPoints.push(pt)
      }
      if (allPoints.length === 0) return
      const bounds = L.latLngBounds(allPoints)
      map.fitBounds(bounds.pad(0.35), { maxZoom: 15 })
    }
    fitToFields()

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [fields, lang, center.lat, center.lon, key, customFields])

  // Handle map click for drawing
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    function onMapClick(e: L.LeafletMouseEvent) {
      if (!isDrawing) return
      const newPt: [number, number] = [e.latlng.lat, e.latlng.lng]
      setDrawCoords((prev) => [...prev, newPt])
    }

    map.on('click', onMapClick)
    return () => {
      map.off('click', onMapClick)
    }
  }, [isDrawing])

  // Render active drawing shape
  useEffect(() => {
    const layer = drawLayerRef.current
    if (!layer) return
    layer.clearLayers()

    if (drawCoords.length > 0) {
      drawCoords.forEach((pt, i) => {
        L.circleMarker(pt, {
          radius: 6,
          color: '#F59E0B',
          fillColor: '#FFFFFF',
          fillOpacity: 1,
          weight: 2,
        }).addTo(layer).bindTooltip(`${i + 1}`, { permanent: true, direction: 'top' })
      })

      if (drawCoords.length >= 3) {
        L.polygon(drawCoords, {
          color: '#F59E0B',
          weight: 3,
          dashArray: '6, 6',
          fillColor: '#F59E0B',
          fillOpacity: 0.2,
        }).addTo(layer)
      } else if (drawCoords.length === 2) {
        L.polyline(drawCoords, { color: '#F59E0B', weight: 3, dashArray: '6, 6' }).addTo(layer)
      }
    }
  }, [drawCoords])

  function handleSaveField() {
    if (drawCoords.length < 3) return
    // §7.4 — reject self-intersecting, absurdly sized, or over-complex boundaries before saving.
    const err = validateFieldPolygon(drawCoords)
    if (err) {
      setStatus(t.invalid[err as keyof typeof t.invalid])
      return
    }
    const areaHa = computePolygonAreaHa(drawCoords)
    const areaBigha = Number((areaHa * 3.9536).toFixed(1)) // 1 ha = 3.9536 Farrukhabad bigha
    const finalName = fieldName.trim() || t.defaultName

    const custom: CustomField = {
      id: 'field_custom_' + Date.now(),
      name_hi: finalName,
      name_en: finalName,
      crop: 'potato',
      area_ha: areaHa,
      area_bigha: areaBigha,
      coordinates: drawCoords,
      district: 'farrukhabad',
      createdAt: new Date().toISOString(),
    }

    saveCustomField(custom)
    setCustomFields(getCustomFields())
    setIsDrawing(false)
    setDrawCoords([])
    setFieldName('')
    setStatus(t.savedToast)
    if (onFieldAdded) onFieldAdded(custom)
  }

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
      },
      () => {
        setLocating(false)
        setStatus(t.denied)
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    )
  }

  const currentAreaHa = computePolygonAreaHa(drawCoords)
  const currentAreaBigha = Number((currentAreaHa * 3.9536).toFixed(1))

  return (
    <div className="map">
      <div className="map__canvas" ref={hostRef} />

      {/* Action overlay buttons */}
      <div className="map__controls">
        {!isDrawing ? (
          <>
            <button className="btn btn--primary map__control-btn" onClick={() => setIsDrawing(true)}>
              {t.drawBtn}
            </button>
            <button className="btn map__locate" onClick={locate} disabled={locating}>
              📍 {locating ? t.locating : t.locate}
            </button>
          </>
        ) : (
          <div className="map__draw-toolbar">
            <div className="map__draw-info">
              <span className="badge badge--act">{drawCoords.length} pts</span>
              <span>{t.areaLabel} <strong>{currentAreaHa} {t.ha}</strong> (~{currentAreaBigha} {t.bigha})</span>
            </div>
            <input
              type="text"
              className="map__field-input"
              placeholder={t.namePrompt}
              value={fieldName}
              onChange={(e) => setFieldName(e.target.value)}
            />
            <div className="map__draw-actions">
              <button
                className="btn btn--primary"
                onClick={handleSaveField}
                disabled={drawCoords.length < 3}
              >
                {t.finishDraw}
              </button>
              <button
                className="btn btn--secondary"
                onClick={() => {
                  setIsDrawing(false)
                  setDrawCoords([])
                }}
              >
                {t.cancelDraw}
              </button>
            </div>
          </div>
        )}
      </div>

      {status && <p className="map__status" role="status">{status}</p>}
    </div>
  )
}
