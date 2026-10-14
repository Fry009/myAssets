import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Heart, Download, Music, FileBox, Star } from 'lucide-react'
import { IMAGE_EXT, AUDIO_EXT, PREVIEWABLE_3D, humanSize, downloadFile } from '../lib/assets.js'
import { MiniModel } from './MiniModel.jsx'
import { TagChip } from './TagChip.jsx'

function useInView(ref, rootMargin = '240px') {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return null
    if (typeof IntersectionObserver === 'undefined') {
      setVisible(true)
      return undefined
    }
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setVisible(true)
          io.disconnect()
        }
      },
      { rootMargin },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [ref, rootMargin])
  return visible
}

// Cada miniatura 3D en vivo abre su propio contexto WebGL y carga el modelo entero;
// con modelos pesados el navegador se queda sin memoria, así que solo los ligeros van en vivo.
const LIVE_3D_MAX_BYTES = 8 * 1024 * 1024

function Thumb({ asset }) {
  if (asset.thumb) {
    return (
      <img
        className="thumb-render"
        src={asset.thumb}
        alt={asset.name}
        loading="lazy"
        decoding="async"
      />
    )
  }
  if (IMAGE_EXT.has(asset.ext)) {
    return <img src={asset.src} alt={asset.name} loading="lazy" decoding="async" />
  }
  if (PREVIEWABLE_3D.has(asset.ext) && asset.size <= LIVE_3D_MAX_BYTES) {
    return <Mini3D asset={asset} />
  }
  if (AUDIO_EXT.has(asset.ext)) {
    return (
      <div className="thumb-pattern thumb-icon">
        <div style={{ textAlign: 'center' }}>
          <Music size={34} style={{ opacity: 0.85 }} />
          <div className="eq" style={{ marginTop: 10 }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <i key={i} style={{ height: 6 + (i % 3) * 5 }} />
            ))}
          </div>
        </div>
      </div>
    )
  }
  return (
    <div className="thumb-pattern thumb-icon">
      <div style={{ textAlign: 'center' }}>
        <FileBox size={38} style={{ opacity: 0.8 }} />
      </div>
    </div>
  )
}

function Mini3D({ asset }) {
  const ref = useRef(null)
  const visible = useInView(ref)
  return (
    <div ref={ref} className="mini-model">
      {visible ? (
        <MiniModel src={asset.src} ext={asset.ext} />
      ) : (
        <div className="thumb-pattern thumb-icon">
          <Star size={24} style={{ opacity: 0.5 }} />
        </div>
      )}
    </div>
  )
}

export function AssetCard({ asset, onSelect, onToggleFav, onTagClick, isTagActive }) {
  const Icon = asset.icon
  return (
    <motion.div
      className="card"
      onClick={() => onSelect(asset)}
      whileHover={{ y: -4 }}
      transition={{ type: 'spring', stiffness: 380, damping: 26 }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onSelect(asset)
      }}
    >
      <div className="thumb">
        <Thumb asset={asset} />
        <span className="ext-badge">{asset.ext || 'file'}</span>
        <button
          className={`fav-btn ${asset.fav ? 'on' : ''}`}
          onClick={(e) => {
            e.stopPropagation()
            onToggleFav(asset)
          }}
          title={asset.fav ? 'Quitar de favoritos' : 'Guardar en favoritos'}
        >
          <Heart size={15} fill={asset.fav ? 'currentColor' : 'none'} />
        </button>
      </div>
      <div className="card-body">
        <div className="card-title">{asset.title}</div>
        <div className="card-meta">
          <span className="cat-pill">
            <Icon size={12} />
            {asset.catLabel}
          </span>
          <span className="dot">·</span>
          <span>{humanSize(asset.size)}</span>
          <span className="dot">·</span>
          <span>.{asset.ext}</span>
        </div>
        {asset.tags.length > 0 && (
          <div className="card-tags">
            {asset.tags.slice(0, 4).map((t) => (
              <TagChip key={t} tag={t} onClick={onTagClick} active={isTagActive(t)} />
            ))}
            {asset.tags.length > 4 && <span className="tag-pill">+{asset.tags.length - 4}</span>}
          </div>
        )}
        <button
          className="download-btn primary"
          style={{ marginTop: 2 }}
          onClick={(e) => {
            e.stopPropagation()
            downloadFile(asset.src, asset.name).catch(() => {})
          }}
        >
          <Download size={13} /> Descargar
        </button>
      </div>
    </motion.div>
  )
}
