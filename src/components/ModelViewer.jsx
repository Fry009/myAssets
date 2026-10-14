import { lazy, Suspense, useCallback, useEffect, useState } from 'react'
import { Eye, Loader2, Play, RotateCcw, Smile, Square } from 'lucide-react'

const Scene = lazy(() => import('./three/ModelScene.jsx'))

const CLIP_LABELS = { idle: 'Reposo', walk: 'Andar', wave: 'Saludar', jump: 'Saltar' }

// Presets de cara: solo aparecen si el modelo tiene esas shape keys
const PRESETS = [
  { label: 'Feliz', morphs: { eyes_happy: 1, mouth_smile: 1 } },
  { label: 'Sorpresa', morphs: { eyes_wide: 1, mouth_o: 1 } },
  { label: 'Triste', morphs: { eyes_sad: 1, mouth_sad: 1 } },
  { label: 'Enfadado', morphs: { eyes_angry: 1, mouth_sad: 0.6 } },
  { label: 'Charla', morphs: { mouth_open: 0.8, mouth_smile: 0.4 } },
]

const GROUPS = [
  { key: 'eyes', label: 'Ojos', test: (n) => /^(blink|eyes)/.test(n) },
  { key: 'look', label: 'Mirada', test: (n) => n.startsWith('look') },
  { key: 'mouth', label: 'Boca', test: (n) => n.startsWith('mouth') },
]

function RigPanel({ rig, clip, setClip, morphs, setMorphs, autoBlink, setAutoBlink }) {
  // Sin boca (robots): el preset se queda con la parte de ojos que exista
  const presets = PRESETS.map((p) => ({
    ...p,
    morphs: Object.fromEntries(Object.entries(p.morphs).filter(([m]) => rig.morphs.includes(m))),
  })).filter((p, i) => {
    const names = Object.keys(p.morphs)
    return names.length === Object.keys(PRESETS[i].morphs).length || names.some((m) => m.startsWith('eyes'))
  })
  const grouped = GROUPS.map((g) => ({ ...g, names: rig.morphs.filter(g.test) }))
  const other = rig.morphs.filter((n) => !GROUPS.some((g) => g.test(n)))
  if (other.length) grouped.push({ key: 'other', label: 'Otras', names: other })

  return (
    <div className="rig-panel">
      {rig.clips.length > 0 && (
        <section>
          <h4>
            <Play size={13} /> Animación
          </h4>
          <div className="rig-chips">
            {rig.clips.map((c) => (
              <button
                key={c}
                className={clip === c ? 'active' : ''}
                onClick={() => setClip(clip === c ? null : c)}
              >
                {CLIP_LABELS[c] || c}
              </button>
            ))}
            <button onClick={() => setClip(null)} title="Parar" disabled={!clip}>
              <Square size={11} />
            </button>
          </div>
        </section>
      )}

      {rig.morphs.length > 0 && (
        <section>
          <h4>
            <Smile size={13} /> Expresión
            <button className="rig-reset" onClick={() => setMorphs({})} title="Cara neutra">
              <RotateCcw size={12} />
            </button>
          </h4>
          {presets.length > 0 && (
            <div className="rig-chips">
              {presets.map((p) => (
                <button key={p.label} onClick={() => setMorphs(p.morphs)}>
                  {p.label}
                </button>
              ))}
            </div>
          )}
          {rig.morphs.includes('blink') && (
            <label className="rig-toggle">
              <input
                type="checkbox"
                checked={autoBlink}
                onChange={(e) => setAutoBlink(e.target.checked)}
              />
              <Eye size={12} /> Parpadeo automático
            </label>
          )}
          {grouped
            .filter((g) => g.names.length)
            .map((g) => (
              <div key={g.key} className="rig-group">
                <span className="rig-group-label">{g.label}</span>
                {g.names.map((n) => (
                  <label key={n} className="rig-slider">
                    <span>{n}</span>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.01}
                      value={morphs[n] || 0}
                      onChange={(e) => setMorphs((m) => ({ ...m, [n]: +e.target.value }))}
                    />
                  </label>
                ))}
              </div>
            ))}
        </section>
      )}
    </div>
  )
}

export function ModelViewer({ src, ext }) {
  const [rig, setRig] = useState(null)
  const [clip, setClip] = useState(null)
  const [morphs, setMorphs] = useState({})
  const [autoBlink, setAutoBlink] = useState(true)

  useEffect(() => {
    setRig(null)
    setClip(null)
    setMorphs({})
  }, [src])

  const onRig = useCallback((r) => {
    setRig(r)
    setClip((c) => c ?? (r.clips.includes('idle') ? 'idle' : null))
  }, [])

  const hasRig = rig && (rig.clips.length > 0 || rig.morphs.length > 0)

  return (
    <div className={`model-viewer${hasRig ? ' has-rig' : ''}`}>
      <div className="model-stage">
        <Suspense
          fallback={
            <div className="viewer-loading">
              <Loader2 size={20} className="spin" />
              Cargando modelo {ext.toUpperCase()}…
            </div>
          }
        >
          <Scene
            src={src}
            ext={ext}
            variant="modal"
            clip={clip}
            morphs={morphs}
            autoBlink={autoBlink}
            onRig={onRig}
          />
        </Suspense>
      </div>
      {hasRig && (
        <RigPanel
          rig={rig}
          clip={clip}
          setClip={setClip}
          morphs={morphs}
          setMorphs={setMorphs}
          autoBlink={autoBlink}
          setAutoBlink={setAutoBlink}
        />
      )}
    </div>
  )
}
