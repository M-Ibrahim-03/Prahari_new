import { useState } from 'react'
import type { Lang } from '../lib/types'
import { queueFeedback } from '../lib/outbox'

const L = {
  hi: {
    title: '⚠️ क्या गलत लग रहा है?',
    subtitle: 'आपकी राय से मौसम व रोग मॉडल को बेहतर बनाया जाता है।',
    types: {
      false_alarm: 'खेत बिलकुल ठीक है, छिड़काव की सलाह गलत है (False Alarm)',
      missed_symptom: 'खेत में झुलसा/रोग दिख रहा है, पर ऐप "सब ठीक" बता रहा है (Missed Outbreak)',
      weather_mismatch: 'यहाँ मौसम का अनुमान गलत है (बारिश/धूप का अंतर)',
      timing_bad: 'छिड़काव का समय अनुकूल नहीं है',
      other: 'अन्य कोई समस्या',
    },
    commentPlaceholder: 'विस्तार से बताएं (वैकल्पिक)…',
    submit: 'प्रतिक्रिया भेजें',
    submitting: 'सहेजा जा रहा है…',
    successTitle: '✓ धन्यवाद!',
    successBody: 'आपकी प्रतिक्रिया सहेज ली गई है। इंटरनेट उपलब्ध होने पर यह अधिकारी और मॉडल तक पहुँच जाएगी।',
    close: 'बंद करें',
    cancel: 'रद्द करें',
  },
  en: {
    title: '⚠️ What looks wrong?',
    subtitle: 'Your ground observation helps calibrate and audit disease models.',
    types: {
      false_alarm: 'Crop is healthy; spray warning seems unnecessary (False Alarm)',
      missed_symptom: 'Blight symptoms visible, but app says All Clear (Missed Outbreak)',
      weather_mismatch: 'Local weather estimate is inaccurate (rain/temperature)',
      timing_bad: 'Spray timing window is impractical',
      other: 'Other observation',
    },
    commentPlaceholder: 'Add any details (optional)…',
    submit: 'Submit Feedback',
    submitting: 'Saving…',
    successTitle: '✓ Thank you!',
    successBody: 'Your feedback has been saved locally and will sync to researchers automatically.',
    close: 'Close',
    cancel: 'Cancel',
  },
}

export function FeedbackModal({
  lang,
  district,
  runId,
  cellId,
  fieldName,
  fieldRef,
  onClose,
}: {
  lang: Lang
  district: string
  runId: string
  cellId?: string | null
  fieldName?: string // 🔴 DISPLAY ONLY — the farmer's own label is PII (§33.1) and never sent.
  fieldRef?: string | null // opaque field id, safe to send for officer correlation
  onClose: () => void
}) {
  const [feedbackType, setFeedbackType] = useState<string>('false_alarm')
  const [comment, setComment] = useState<string>('')
  const [submitted, setSubmitted] = useState<boolean>(false)
  const t = L[lang]

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    // 🔴 Send the opaque cell/field id, NOT fieldName — a farmer's field label must not leave the device.
    queueFeedback(district, runId, feedbackType, cellId, fieldRef ?? null, { comment })
    setSubmitted(true)
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {!submitted ? (
          <form onSubmit={handleSubmit}>
            <header className="modal-header">
              <h2>{t.title}</h2>
              {fieldName && <p className="modal-subtitle">खेत: <strong>{fieldName}</strong> {cellId ? `(${cellId})` : ''}</p>}
              <p className="modal-desc">{t.subtitle}</p>
            </header>

            <div className="feedback-options">
              {Object.entries(t.types).map(([key, label]) => (
                <label key={key} className={`feedback-radio-card ${feedbackType === key ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="feedbackType"
                    value={key}
                    checked={feedbackType === key}
                    onChange={() => setFeedbackType(key)}
                  />
                  <span>{label}</span>
                </label>
              ))}
            </div>

            <div className="modal-form-group">
              <textarea
                className="feedback-textarea"
                rows={3}
                placeholder={t.commentPlaceholder}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
            </div>

            <footer className="modal-footer">
              <button type="button" className="btn btn--secondary" onClick={onClose}>
                {t.cancel}
              </button>
              <button type="submit" className="btn btn--primary">
                {t.submit}
              </button>
            </footer>
          </form>
        ) : (
          <div className="feedback-success">
            <h3>{t.successTitle}</h3>
            <p>{t.successBody}</p>
            <button className="btn btn--primary" onClick={onClose}>
              {t.close}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
