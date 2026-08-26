import { useRef, useState } from 'react'
import type { Lang } from '../lib/types'
import { scanLeaf, aiConfigured, type LeafSymptom } from '../lib/ai'

const L = {
  hi: {
    title: '📸 पत्ती लक्षण जाँच',
    subtitle: 'खेत में दिखे झुलसा/धब्बे के लक्षण पहचानने में मदद',
    privacyLocal: '🔒 फोटो आपके फोन पर रहती है। AI राय माँगने पर ही यह सुरक्षित रूप से भेजी जाती है।',
    takePhoto: '📷 फोटो खींचें या चुनें',
    analyzing: 'AI जाँच रहा है…',
    aiBtn: '✨ AI से राय लें (फोटो भेजी जाएगी)',
    resultTitle: 'AI आकलन:',
    guideTitle: 'लक्षण मिलाएँ — अपनी पत्ती इनसे तुलना करें:',
    guideNote: 'यह केवल मार्गदर्शन है। पक्का लगे तो "यह गलत है" से रिपोर्ट करें।',
    disclaimerTitle: '⚠️ महत्वपूर्ण नियम (§12):',
    disclaimer: 'फोटो जाँच छिड़काव के निर्णय को नहीं बदलती। छिड़काव का फ़ैसला केवल मौसम/रोग मॉडल पर आधारित होता है।',
    close: 'बंद करें',
    retake: 'दूसरी फोटो',
    symptoms: {
      late_blight: { t: 'पछेती झुलसा (Late Blight)', d: 'भूरे/काले जल-सोखे धब्बे, किनारे पर सफ़ेद फफूँद' },
      early_blight: { t: 'अगेती झुलसा (Early Blight)', d: 'छल्लेदार कत्थई धब्बे (टार्गेट जैसा)' },
      healthy: { t: 'स्वस्थ पत्ती', d: 'कोई गलन/धब्बा नहीं' },
      uncertain: { t: 'स्पष्ट नहीं', d: 'फोटो से पक्का नहीं — पास से साफ़ फोटो लें' },
    },
  },
  en: {
    title: '📸 Leaf Symptom Check',
    subtitle: 'Helps you recognise blight lesions seen in the field',
    privacyLocal: '🔒 The photo stays on your phone. It is sent securely only if you ask for an AI opinion.',
    takePhoto: '📷 Take or Upload Leaf Photo',
    analyzing: 'AI is checking…',
    aiBtn: '✨ Get AI opinion (sends photo)',
    resultTitle: 'AI assessment:',
    guideTitle: 'Match symptoms — compare your leaf to these:',
    guideNote: 'This is guidance only. If sure, report it with “This is wrong”.',
    disclaimerTitle: '⚠️ Safety Invariant (§12):',
    disclaimer: 'A photo check never overrides the spray decision. Spray timing comes only from the weather/disease model.',
    close: 'Close',
    retake: 'Scan Another',
    symptoms: {
      late_blight: { t: 'Late Blight', d: 'Water-soaked dark spots, white mould at edges' },
      early_blight: { t: 'Early Blight', d: 'Concentric brown target-like rings' },
      healthy: { t: 'Healthy foliage', d: 'No lesions or necrosis' },
      uncertain: { t: 'Unclear', d: 'Photo not conclusive — take a closer, sharper shot' },
    },
  },
}

// Read a File as a base64 string (strip the data: prefix for the API).
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const s = String(reader.result)
      resolve(s.includes(',') ? s.split(',')[1] : s)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export function LeafScanModal({ lang, onClose }: { lang: Lang; onClose: () => void }) {
  const [imageSrc, setImageSrc] = useState<string | null>(null)
  const [imageB64, setImageB64] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [aiResult, setAiResult] = useState<{ symptom: LeafSymptom; confidence?: number; note?: string } | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const t = L[lang]

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setImageSrc(URL.createObjectURL(file))
    setAiResult(null)
    setImageB64(await fileToBase64(file))
  }

  async function handleAiOpinion() {
    if (!imageB64) return
    setAnalyzing(true)
    setAiResult(null)
    const res = await scanLeaf(imageB64, lang)
    if (res.source === 'ai' && res.symptom) {
      setAiResult({ symptom: res.symptom, confidence: res.confidence, note: res.note })
    }
    // On 'guide' (unconfigured/offline/failed) we simply leave the self-check guide visible —
    // no fabricated diagnosis, no invented confidence number.
    setAnalyzing(false)
  }

  const guideKeys: LeafSymptom[] = ['late_blight', 'early_blight', 'healthy']

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>{t.title}</h2>
          <p className="modal-desc">{t.subtitle}</p>
        </header>

        <input
          type="file"
          accept="image/*"
          capture="environment"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        {!imageSrc ? (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <button
              className="btn btn--primary"
              style={{ width: '100%', minHeight: '52px', fontSize: '1.1rem' }}
              onClick={() => fileInputRef.current?.click()}
            >
              {t.takePhoto}
            </button>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '12px' }}>{t.privacyLocal}</p>
          </div>
        ) : (
          <div>
            <div style={{ position: 'relative', width: '100%', maxHeight: '200px', overflow: 'hidden', borderRadius: '8px', marginBottom: '12px' }}>
              <img src={imageSrc} alt="Leaf" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            </div>

            {/* Real AI opinion — only offered when a server-side AI service is configured. */}
            {aiConfigured() && !aiResult && (
              <button className="btn btn--primary" style={{ width: '100%', marginBottom: '10px' }} onClick={handleAiOpinion} disabled={analyzing}>
                {analyzing ? t.analyzing : t.aiBtn}
              </button>
            )}

            {analyzing && (
              <div style={{ textAlign: 'center', padding: '8px' }}>
                <span className="spinner" />
              </div>
            )}

            {aiResult && (
              <div className="trust-card" style={{ marginTop: '4px', background: 'var(--surface-hover)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span style={{ fontSize: '1.2rem' }}>🌿</span>
                  <strong>{t.resultTitle}</strong>
                  {aiResult.confidence != null && (
                    <span className="badge badge--watch" style={{ marginLeft: 'auto' }}>{Math.round(aiResult.confidence * 100)}%</span>
                  )}
                </div>
                <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>
                  {t.symptoms[aiResult.symptom].t}
                </p>
                {aiResult.note && <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{aiResult.note}</p>}
              </div>
            )}

            {/* Self-check guide — always available, 100% local, no upload, no fabricated score. */}
            <div className="trust-card" style={{ marginTop: '8px' }}>
              <strong style={{ fontSize: '0.9rem' }}>{t.guideTitle}</strong>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '8px' }}>
                {guideKeys.map((k) => (
                  <div key={k} style={{ display: 'flex', gap: '8px', alignItems: 'baseline' }}>
                    <span className={`badge badge--${k === 'late_blight' ? 'act' : k === 'early_blight' ? 'watch' : 'safe'}`}>
                      {t.symptoms[k].t}
                    </span>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{t.symptoms[k].d}</span>
                  </div>
                ))}
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '8px' }}>{t.guideNote}</p>
            </div>

            <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '8px', marginTop: '10px' }}>
              <strong style={{ fontSize: '0.8rem', color: '#991b1b' }}>{t.disclaimerTitle}</strong>
              <p style={{ fontSize: '0.78rem', color: '#991b1b', margin: '4px 0 0' }}>{t.disclaimer}</p>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
              <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => fileInputRef.current?.click()}>
                {t.retake}
              </button>
              <button className="btn btn--primary" style={{ flex: 1 }} onClick={onClose}>
                {t.close}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
