import { useEffect, useRef, useState } from 'react'
import { estimateSeconds, playAdvisory, speechAvailable, stopAudio, type AudioMode } from '../lib/audio'
import type { Advisory, Lang } from '../lib/types'

const L = {
  hi: { listen: 'सुनें', stop: 'रोकें', playing: 'चल रहा है', sec: 'सेकंड', noVoice: 'आवाज़ उपलब्ध नहीं' },
  en: { listen: 'Listen', stop: 'Stop', playing: 'Playing', sec: 'sec', noVoice: 'Voice unavailable' },
}

export function PlayButton({
  advisory,
  lang,
  primary,
  onMode,
}: {
  advisory: Advisory
  lang: Lang
  primary: boolean
  onMode?: (m: AudioMode) => void
}) {
  const [playing, setPlaying] = useState(false)
  const t = L[lang]
  const mounted = useRef(true)
  useEffect(() => () => { mounted.current = false; stopAudio() }, [])

  const secs = estimateSeconds(advisory.text)
  const canSpeak = speechAvailable()

  async function toggle() {
    if (playing) {
      stopAudio()
      setPlaying(false)
      return
    }
    setPlaying(true)
    const mode = await playAdvisory(advisory.audio_segments, advisory.text, lang)
    onMode?.(mode)
    if (mounted.current) setPlaying(false)
  }

  return (
    <button
      className={primary ? 'play play--primary' : 'play'}
      onClick={toggle}
      // Text is always available alongside audio (FR-8.9); this label keeps the control
      // meaningful to a screen reader even when no voice engine exists.
      aria-label={`${playing ? t.stop : t.listen}: ${advisory.text}`}
      disabled={!canSpeak && advisory.audio_segments.length === 0}
    >
      <span className="play__icon" aria-hidden="true">{playing ? '⏸' : '🔊'}</span>
      <span className="play__label">
        {playing ? t.playing : t.listen}
        {!playing && <span className="play__dur"> · {secs} {t.sec}</span>}
      </span>
    </button>
  )
}
