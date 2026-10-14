import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  X,
  ChevronLeft,
  ChevronRight,
  Download,
  Heart,
  Copy,
  Check,
  Plus,
  FileBox,
} from 'lucide-react'
import {
  IMAGE_EXT,
  AUDIO_EXT,
  PREVIEWABLE_3D,
  humanSize,
  humanDate,
  downloadFile,
} from '../lib/assets.js'
import { ModelViewer } from './ModelViewer.jsx'
import { ImageViewer } from './ImageViewer.jsx'
import { AudioPlayer } from './AudioPlayer.jsx'
import { TagChip } from './TagChip.jsx'

function Viewer({ asset }) {
  if (PREVIEWABLE_3D.has(asset.ext)) return <ModelViewer src={asset.src} ext={asset.ext} />
  if (AUDIO_EXT.has(asset.ext)) return <AudioPlayer src={asset.src} name={asset.name} />
  if (IMAGE_EXT.has(asset.ext)) return <ImageViewer src={asset.src} />
  const Icon = asset.icon || FileBox
  return (
    <div className="generic-viewer">
      <div>
        <div className="big-icon">
          <Icon size={46} />
        </div>
        <h3>{asset.title}</h3>
        <p>
          Este tipo de archivo (<b>.{asset.ext}</b>) no se puede previsualizar aquí.
          Descárgalo para verlo en tu editor.
        </p>
      </div>
    </div>
  )
}

export function PreviewModal({
  asset,
  total,
  pos,
  onClose,
  onPrev,
  onNext,
  onToggleFav,
  onTagClick,
  onTagRemove,
  onAddTag,
  onUpdate,
  allTags,
}) {
  const [tagInput, setTagInput] = useState('')
  const [dlState, setDlState] = useState('idle')
  const [copyState, setCopyState] = useState('idle')
  const Icon = asset.icon || FileBox

  useEffect(() => {
    setTagInput('')
    setDlState('idle')
    setCopyState('idle')
  }, [asset.url])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'ArrowLeft') onPrev()
      if (e.key === 'ArrowRight') onNext()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onPrev, onNext])

  const doDownload = () => {
    setDlState('busy')
    downloadFile(asset.src, asset.name)
      .then(() => setDlState('ok'))
      .catch(() => setDlState('idle'))
    setTimeout(() => setDlState((s) => (s === 'ok' ? 'idle' : s)), 1800)
  }

  const doCopy = () => {
    navigator.clipboard?.writeText(asset.src)
    setCopyState('ok')
    setTimeout(() => setCopyState('idle'), 1400)
  }

  const commitTag = () => {
    const t = tagInput.trim()
    if (t) {
      onAddTag(asset.url, t.replace(/\s+/g, '-'))
      setTagInput('')
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <motion.div
        className="modal"
        onClick={(e) => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 10 }}
        transition={{ duration: 0.22, ease: 'easeOut' }}
      >
        <div className="modal-head">
          <div className="modal-breadcrumb">
            <Icon size={15} />
            <strong>{asset.catLabel}</strong>
            <span>·</span>
            <span className="name">{asset.name}</span>
          </div>
          <div className="spacer" />
          <button
            className={`icon-btn gold ${asset.fav ? 'on' : ''}`}
            onClick={onToggleFav}
            title={asset.fav ? 'Quitar favorito' : 'Marcar favorito'}
          >
            <Heart size={17} fill={asset.fav ? 'currentColor' : 'none'} />
          </button>
          <button className="icon-btn" onClick={doCopy} title="Copiar ruta">
            {copyState === 'ok' ? <Check size={17} /> : <Copy size={17} />}
          </button>
          <button className="icon-btn" onClick={onClose} title="Cerrar (Esc)">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <div className="viewer-area">
            <Viewer asset={asset} />
          </div>

          <aside className="side-panel">
            <div>
              <input
                className="side-title-input"
                value={asset.title}
                onChange={(e) => onUpdate(asset.url, { title: e.target.value })}
                placeholder="Título sin nombre…"
              />
              <p className="sub">
                {asset.catLabel} · .{asset.ext} · {humanSize(asset.size)}
              </p>
            </div>

            <textarea
              className="side-desc side-desc-edit"
              value={asset.desc}
              onChange={(e) => onUpdate(asset.url, { desc: e.target.value })}
              placeholder="Añade una descripción…"
            />

            <div>
              <div className="side-label">Etiquetas</div>
              <div className="card-tags" style={{ marginTop: 6 }}>
                {asset.tags.map((t) => (
                  <TagChip
                    key={t}
                    tag={t}
                    onClick={onTagClick}
                    removable
                    onRemove={() => onTagRemove(asset.url, t)}
                  />
                ))}
                {asset.tags.length === 0 && (
                  <span style={{ fontSize: 12, color: 'var(--dim)' }}>Sin etiquetas aún</span>
                )}
              </div>
              <div className="tag-editor" style={{ marginTop: 8 }}>
                <input
                  list="tag-suggestions"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') commitTag()
                  }}
                  placeholder="Nueva etiqueta…"
                />
                <button className="icon-btn" onClick={commitTag} title="Añadir etiqueta">
                  <Plus size={16} />
                </button>
              </div>
              <datalist id="tag-suggestions">
                {allTags.map((t) => (
                  <option key={t} value={t} />
                ))}
              </datalist>
            </div>

            <div className="info-rows">
              <div className="info-row">
                <span>Archivo</span>
                <b>{asset.name}</b>
              </div>
              <div className="info-row">
                <span>Tipo</span>
                <b>.{asset.ext}</b>
              </div>
              <div className="info-row">
                <span>Peso</span>
                <b>{humanSize(asset.size)}</b>
              </div>
              <div className="info-row">
                <span>Modificado</span>
                <b>{humanDate(asset.mtime)}</b>
              </div>
              <div className="info-row">
                <span>Ruta</span>
                <b style={{ maxWidth: 220 }}>{asset.url}</b>
              </div>
            </div>

            <button className="download-btn primary" onClick={doDownload}>
              <Download size={15} />
              {dlState === 'ok' ? 'Descargado ✓' : 'Descargar'}
            </button>
          </aside>
        </div>

        <div className="modal-foot">
          <button className="icon-btn" onClick={onPrev} disabled={total < 2} title="Anterior (←)">
            <ChevronLeft size={18} />
          </button>
          <span className="count-pos">
            {total > 0 ? `${pos} / ${total}` : '1 / 1'}
          </span>
          <button className="icon-btn" onClick={onNext} disabled={total < 2} title="Siguiente (→)">
            <ChevronRight size={18} />
          </button>
        </div>
      </motion.div>
    </div>
  )
}