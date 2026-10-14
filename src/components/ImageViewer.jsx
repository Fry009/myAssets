import { useEffect, useRef, useState } from 'react'
import { ZoomIn, ZoomOut, Maximize2, MousePointer2 } from 'lucide-react'

const MIN = 0.2
const MAX = 8

export function ImageViewer({ src }) {
  const wrapRef = useRef(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [dragging, setDragging] = useState(false)
  const drag = useRef({ sx: 0, sy: 0, px: 0, py: 0, zoom: 1 })

  const clampZoom = (z) => Math.max(MIN, Math.min(MAX, z))

  const applyZoomAt = (factor, cx, cy) => {
    const el = wrapRef.current
    const z = clampZoom(zoom * factor)
    if (!el) return
    const rect = el.getBoundingClientRect()
    const px = cx - rect.left
    const py = cy - rect.top
    setPan((p) => {
      const worldX = (px - p.x) / zoom
      const worldY = (py - p.y) / zoom
      return { x: px - worldX * z, y: py - worldY * z }
    })
    setZoom(z)
  }

  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const onWheel = (e) => {
      e.preventDefault()
      const rect = el.getBoundingClientRect()
      const cx = e.clientX - rect.left
      const cy = e.clientY - rect.top
      applyZoomAt(e.deltaY < 0 ? 1.18 : 1 / 1.18, cx, cy)
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoom])

  const onPointerDown = (e) => {
    if (e.target.closest?.('.zoom-bar')) return
    const el = wrapRef.current
    el.setPointerCapture(e.pointerId)
    drag.current = { sx: e.clientX, sy: e.clientY, px: pan.x, py: pan.y, zoom }
    setDragging(true)
  }
  const onPointerMove = (e) => {
    if (!dragging) return
    setPan({
      x: drag.current.px + (e.clientX - drag.current.sx),
      y: drag.current.py + (e.clientY - drag.current.sy),
    })
  }
  const onPointerUp = () => setDragging(false)

  const zoomAtCenter = (factor) => {
    const el = wrapRef.current
    const rect = el?.getBoundingClientRect()
    applyZoomAt(factor, rect ? rect.width / 2 : 0, rect ? rect.height / 2 : 0)
  }

  const reset = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

  const onDoubleClick = (e) => {
    const el = wrapRef.current
    const rect = el.getBoundingClientRect()
    if (zoom > 1.01) reset()
    else applyZoomAt(2, e.clientX - rect.left, e.clientY - rect.top)
  }

  return (
    <div
      className={`image-viewer ${dragging ? 'dragging' : ''}`}
      ref={wrapRef}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={() => setDragging(false)}
      onDoubleClick={onDoubleClick}
    >
      <img
        src={src}
        alt="preview"
        draggable={false}
        style={{
          '--zoom': zoom,
          '--px': `${pan.x}px`,
          '--py': `${pan.y}px`,
        }}
      />
      <div className="zoom-bar">
        <button className="icon-btn" onClick={() => zoomAtCenter(1 / 1.25)} title="Alejar">
          <ZoomOut size={15} />
        </button>
        <span>{Math.round(zoom * 100)}%</span>
        <button className="icon-btn" onClick={() => zoomAtCenter(1.25)} title="Acercar">
          <ZoomIn size={15} />
        </button>
        <button className="icon-btn" onClick={reset} title="Restablecer">
          <Maximize2 size={15} />
        </button>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11 }}>
          <MousePointer2 size={12} /> arrastra / rueda
        </span>
      </div>
    </div>
  )
}