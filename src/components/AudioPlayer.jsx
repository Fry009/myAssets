import { useEffect, useRef, useState } from 'react'
import { Play, Pause, Volume2, VolumeX, Disc3 } from 'lucide-react'

function fmt(s) {
  if (!Number.isFinite(s) || s < 0) return '0:00'
  const m = Math.floor(s / 60)
  const ss = Math.floor(s % 60)
  return `${m}:${String(ss).padStart(2, '0')}`
}

export function AudioPlayer({ src, name }) {
  const audioRef = useRef(null)
  const [playing, setPlaying] = useState(false)
  const [cur, setCur] = useState(0)
  const [dur, setDur] = useState(0)
  const [muted, setMuted] = useState(false)

  const toggle = () => {
    const a = audioRef.current
    if (!a) return
    if (a.paused) a.play().catch(() => {})
    else a.pause()
  }

  const seek = (v) => {
    const a = audioRef.current
    if (!a) return
    a.currentTime = Number(v)
    setCur(Number(v))
  }

  const audioOn = (fn) => () => {
    const a = audioRef.current
    if (a) fn(a)
  }

  return (
    <div className="audio-wrap">
      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        onTimeUpdate={audioOn((a) => setCur(a.currentTime))}
        onLoadedMetadata={audioOn((a) => setDur(a.duration))}
      />
      <div className={`audio-disk ${playing ? 'spinning' : ''}`}>
        <div className="core">
          <Disc3 size={26} />
        </div>
      </div>

      <div className="eq" style={{ height: 26 }}>
        {Array.from({ length: 10 }).map((_, i) => (
          <i key={i} style={{ animationDuration: `${0.7 + (i % 4) * 0.14}s` }} />
        ))}
      </div>

      <div className={`eq ${playing ? '' : 'paused'}`} style={{ height: 0 }} aria-hidden="true" />

      <button className="play-btn" onClick={toggle} title={playing ? 'Pausar' : 'Reproducir'}>
        {playing ? <Pause size={30} /> : <Play size={30} style={{ marginLeft: 4 }} />}
      </button>

      <div className="audio-times">
        <span>{fmt(cur)}</span>
        <span>{fmt(dur)}</span>
      </div>
      <input
        className="timeline"
        type="range"
        min={0}
        max={dur || 0}
        step={0.01}
        value={cur}
        onChange={(e) => seek(e.target.value)}
        style={{ '--fill': dur ? `${(cur / dur) * 100}%` : '0%' }}
      />

      <div className="audio-controls">
        <button
          className="icon-btn mute-btn"
          onClick={() => {
            const a = audioRef.current
            if (!a) return
            a.muted = !a.muted
            setMuted(a.muted)
          }}
          title={muted ? 'Activar sonido' : 'Silenciar'}
        >
          {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
        </button>
        <span style={{ fontSize: 12, color: 'var(--dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {name}
        </span>
      </div>
    </div>
  )
}