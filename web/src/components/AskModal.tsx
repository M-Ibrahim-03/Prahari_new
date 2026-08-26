import { useState } from 'react'
import type { FieldEntry, Lang } from '../lib/types'
import { askAssistant, aiConfigured, type AskSource } from '../lib/ai'

const L = {
  hi: {
    title: '🎤 प्रहरी सहायक से पूछें',
    subtitle: 'रोग स्थिति, मौसम व छिड़काव समय के बारे में सवाल पूछें',
    placeholder: 'जैसे: क्या आज आलू में छिड़काव करना सही रहेगा?…',
    askBtn: 'पूछें',
    listening: 'सुन रहे हैं… (बोलिए)',
    voiceBtn: '🎙️ बोलकर पूछें',
    suggestTitle: 'आम सवाल:',
    suggestions: [
      'क्या आज मेरे खेत में छिड़काव करना चाहिए?',
      'छिड़काव का सबसे अच्छा समय क्या है?',
      'रोग का कितना जोखिम है?',
    ],
    answering: 'उत्तर तैयार हो रहा है…',
    close: 'बंद करें',
    srcAi: 'AI द्वारा शब्दों में',
    srcEngine: 'इंजन के आँकड़ों से',
    l4Note: 'सुरक्षा नियम (§27.5): उत्तर केवल इंजन के आँकड़े दोहराता है — कोई रासायनिक दवा, खुराक या नई संख्या नहीं जोड़ी जाती।',
  },
  en: {
    title: '🎤 Ask PRAHARI Assistant',
    subtitle: 'Ask questions about disease risk, weather, and spray timing',
    placeholder: 'e.g. Is it safe to spray my potato field today?…',
    askBtn: 'Ask',
    listening: 'Listening… (speak now)',
    voiceBtn: '🎙️ Ask by Voice',
    suggestTitle: 'Common questions:',
    suggestions: [
      'Should I spray my field today?',
      'What is the best spray timing window?',
      'How high is the disease risk?',
    ],
    answering: 'Preparing answer…',
    close: 'Close',
    srcAi: 'AI-phrased',
    srcEngine: 'From engine readings',
    l4Note: 'Safety Gate (§27.5): the answer only restates engine readings — it never adds a chemical, dose, or new number.',
  },
}

export function AskModal({
  lang,
  fields,
  onClose,
}: {
  lang: Lang
  fields: FieldEntry[]
  onClose: () => void
}) {
  const [query, setQuery] = useState('')
  const [selectedFieldId, setSelectedFieldId] = useState<string>(fields[0]?.id || '')
  const [isListening, setIsListening] = useState(false)
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState<string | null>(null)
  const [answerSource, setAnswerSource] = useState<AskSource>('engine')
  const t = L[lang]

  const activeField = fields.find((f) => f.id === selectedFieldId) || fields[0]

  function handleVoiceInput() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert(lang === 'hi' ? 'इस ब्राउज़र में आवाज़ पहचान उपलब्ध नहीं है' : 'Speech recognition not supported in this browser')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onstart = () => setIsListening(true)
    recognition.onend = () => setIsListening(false)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript
      setQuery(transcript)
      handleAsk(transcript)
    }

    recognition.start()
  }

  async function handleAsk(q: string) {
    if (!q.trim() || !activeField) return
    setLoading(true)
    setAnswer(null)
    // Real answer: server-side Gemini when configured+online, else a deterministic
    // rephrasing of this field's own engine numbers (lib/ai.ts). Never a fake timeout.
    const res = await askAssistant(activeField, q, lang)
    setAnswer(res.text)
    setAnswerSource(res.source)
    setLoading(false)
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>{t.title}</h2>
          <p className="modal-desc">{t.subtitle}</p>
        </header>

        {fields.length > 1 && (
          <div className="modal-form-group" style={{ marginBottom: '12px' }}>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {lang === 'hi' ? 'खेत चुनें:' : 'Select Field:'}
            </label>
            <select
              className="topbar__view"
              style={{ width: '100%', marginTop: '4px' }}
              value={selectedFieldId}
              onChange={(e) => setSelectedFieldId(e.target.value)}
            >
              {fields.map((f) => (
                <option key={f.id} value={f.id}>
                  {lang === 'hi' ? f.name_hi : f.name_en} ({f.band.toUpperCase()})
                </option>
              ))}
            </select>
          </div>
        )}

        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <input
            type="text"
            className="feedback-textarea"
            style={{ resize: 'none', height: '44px' }}
            placeholder={t.placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAsk(query)}
          />
          <button
            className="btn btn--primary"
            onClick={() => handleAsk(query)}
            disabled={loading || !query.trim()}
          >
            {t.askBtn}
          </button>
        </div>

        <button
          className="btn btn--secondary"
          style={{ width: '100%', marginBottom: '16px' }}
          onClick={handleVoiceInput}
        >
          {isListening ? t.listening : t.voiceBtn}
        </button>

        {/* Suggestion Chips */}
        {!answer && !loading && (
          <div style={{ marginBottom: '16px' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
              {t.suggestTitle}
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {t.suggestions.map((s, i) => (
                <button
                  key={i}
                  className="feedback-radio-card"
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    setQuery(s)
                    handleAsk(s)
                  }}
                >
                  💬 {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: 'center', padding: '16px' }}>
            <span className="spinner" />
            <p className="muted">{t.answering}</p>
          </div>
        )}

        {answer && (
          <div className="trust-card" style={{ marginTop: '8px', background: 'var(--surface-hover)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: '1.2rem' }}>🌾</span>
              <strong>{lang === 'hi' ? 'प्रहरी सलाह' : 'PRAHARI Advice'}</strong>
              <span className="badge badge--safe" style={{ marginLeft: 'auto' }}>
                {answerSource === 'ai' ? `✨ ${t.srcAi}` : `📊 ${t.srcEngine}`}
              </span>
            </div>
            <p style={{ fontSize: '1rem', lineHeight: '1.6', color: 'var(--text)' }}>{answer}</p>
          </div>
        )}

        {!aiConfigured() && (
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '10px' }}>
            {lang === 'hi'
              ? 'ℹ️ AI सेवा जुड़ी नहीं है — उत्तर सीधे इस खेत के इंजन आँकड़ों से बनाया गया है।'
              : 'ℹ️ AI service not connected — answers are built directly from this field’s engine readings.'}
          </p>
        )}

        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>
          🛡️ {t.l4Note}
        </p>

        <footer className="modal-footer">
          <button className="btn btn--secondary" onClick={onClose}>
            {t.close}
          </button>
        </footer>
      </div>
    </div>
  )
}
