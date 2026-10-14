import { useCallback, useEffect, useMemo, useState } from 'react'
import { LayoutGrid, RefreshCw, X, Copy, Layers } from 'lucide-react'
import { Sidebar } from './components/Sidebar.jsx'
import { Toolbar } from './components/Toolbar.jsx'
import { AssetGrid } from './components/AssetGrid.jsx'
import { PreviewModal } from './components/PreviewModal.jsx'
import { categoryOf, categoryConfig, searchFields } from './lib/assets.js'

const OVERLAY_KEY = 'myassets-overlay-v1'

function loadOverlay() {
  try {
    return JSON.parse(localStorage.getItem(OVERLAY_KEY)) || {}
  } catch {
    return {}
  }
}

export default function App() {
  const [status, setStatus] = useState('loading')
  const [index, setIndex] = useState(null)
  const [manifest, setManifest] = useState({ title: '', subtitle: '', assets: {} })
  const [overlay, setOverlay] = useState(loadOverlay)
  const [activeCat, setActiveCat] = useState('all')
  const [query, setQuery] = useState('')
  const [tagFilter, setTagFilter] = useState([])
  const [favOnly, setFavOnly] = useState(false)
  const [sortBy, setSortBy] = useState('name')
  const [selected, setSelected] = useState(null)
  const [toast, setToast] = useState('')

  const reload = useCallback(async () => {
    setStatus('loading')
    try {
      const [i, t] = await Promise.all([
        fetch('/asset-index.json').then((r) => r.json()),
        fetch('/asset-tags.json')
          .then((r) => r.json())
          .catch(() => ({ title: '', subtitle: '', assets: {} })),
      ])
      setIndex(i)
      setManifest(t || { title: '', subtitle: '', assets: {} })
      const title = t?.title ? `${t.title} · ${t?.subtitle || ''}` : 'MyAsset Vault'
      document.title = title.replace(/\s+·\s*$/, '')
      setStatus('ready')
    } catch (e) {
      console.error(e)
      setStatus('error')
    }
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  useEffect(() => {
    try {
      localStorage.setItem(OVERLAY_KEY, JSON.stringify(overlay))
    } catch {
      /* noop */
    }
  }, [overlay])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') setSelected(null)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => {
    if (!toast) return
    const id = setTimeout(() => setToast(''), 2400)
    return () => clearTimeout(id)
  }, [toast])

  const all = useMemo(() => {
    if (!index) return { list: [], counts: new Map(), tagCounts: new Map() }
    const base = manifest.assets || {}
    const wantsFav = (a, ov, meta) => (ov.fav === undefined ? !!meta.fav : ov.fav)
    const list = index.files.map((f) => {
      const meta = base[f.url] || {}
      const ov = overlay[f.url] || {}
      const tags = [...new Set([...(meta.tags || []), ...(ov.tags || [])])]
      const category = categoryOf(f.url, f.ext)
      const cfg = categoryConfig(f.url, f.ext)
      return {
        ...f,
        src: '/assets' + f.url,
        category,
        catLabel: cfg.label,
        icon: cfg.icon,
        title:
          ov.title ||
          meta.title ||
          f.name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ').trim(),
        desc: ov.desc || meta.desc || '',
        tags,
        fav: wantsFav(f, ov, meta),
      }
    })
    const counts = new Map()
    const tagCounts = new Map()
    for (const a of list) {
      counts.set(a.category, (counts.get(a.category) || 0) + 1)
      for (const t of a.tags) tagCounts.set(t, (tagCounts.get(t) || 0) + 1)
    }
    return { list, counts, tagCounts }
  }, [index, manifest, overlay])

  const filtered = useMemo(() => {
    let out = all.list
    if (activeCat !== 'all') out = out.filter((a) => a.category === activeCat)
    if (tagFilter.length) out = out.filter((a) => tagFilter.every((t) => a.tags.includes(t)))
    if (favOnly) out = out.filter((a) => a.fav)
    const q = query.trim().toLowerCase()
    if (q) out = out.filter((a) => searchFields(a).includes(q))
    const arr = [...out]
    arr.sort((a, b) => {
      if (sortBy === 'size') return b.size - a.size
      if (sortBy === 'recent') return b.mtime - a.mtime
      return a.name.localeCompare(b.name, 'es', { numeric: true, sensitivity: 'base' })
    })
    return arr
  }, [all, activeCat, tagFilter, favOnly, query, sortBy])

  useEffect(() => {
    if (!selected) return
    const fresh = filtered.find((a) => a.url === selected.url)
    if (fresh) setSelected(fresh)
    else setSelected(null)
  }, [filtered, selected])

  const touchOverlay = useCallback((url, patch) => {
    setOverlay((ov) => {
      const cur = ov[url] || {}
      const next = { ...cur, ...patch }
      const copy = { ...ov }
      if (Object.keys(next).length && Object.values(next).some((v) => (Array.isArray(v) ? v.length : v))) copy[url] = next
      else delete copy[url]
      return copy
    })
  }, [])

  const toggleFav = useCallback(
    (asset) => touchOverlay(asset.url, { fav: !asset.fav }),
    [touchOverlay],
  )

  const toggleTag = useCallback((tag) => {
    setTagFilter((tf) => (tf.includes(tag) ? tf.filter((t) => t !== tag) : [...tf, tag]))
  }, [])

  const addTag = useCallback(
    (url, tag) => {
      const t = tag.trim().toLowerCase().replace(/\s+/g, '-')
      if (!t) return
      setOverlay((ov) => {
        const cur = ov[url] || {}
        const mods = cur.tags || []
        if (mods.includes(t)) return ov
        return { ...ov, [url]: { ...cur, tags: [...mods, t] } }
      })
    },
    [],
  )

  const removeTag = useCallback((url, tag) => {
    setOverlay((ov) => {
      const cur = ov[url]
      if (!cur) return ov
      const next = { ...cur }
      const tags = (cur.tags || []).filter((t) => t !== tag)
      if (tags.length) next.tags = tags
      else delete next.tags
      const hasContent =
        next.fav === true ||
        (next.tags || []).length > 0 ||
        Boolean(next.title) ||
        Boolean(next.desc)
      if (!hasContent) {
        const copy = { ...ov }
        delete copy[url]
        return copy
      }
      return { ...ov, [url]: next }
    })
  }, [])

  const clearFilters = useCallback(() => {
    setActiveCat('all')
    setTagFilter([])
    setFavOnly(false)
    setQuery('')
  }, [])

  const prevNext = useCallback(
    (dir) => {
      if (!selected || filtered.length < 2) return
      const i = filtered.findIndex((a) => a.url === selected.url)
      if (i === -1) return
      const next = filtered[(i + dir + filtered.length) % filtered.length]
      setSelected(next)
    },
    [selected, filtered],
  )

  const allCount = all.list.length
  const totalTags = all.tagCounts.size

  return (
    <div className="app">
      <div className="bg-fx" aria-hidden="true">
        <div className="blob blob-1" />
        <div className="blob blob-2" />
        <div className="blob blob-3" />
      </div>

      <header className="topbar">
        <div className="brand">
          <div className="logo">
            <Layers size={22} />
          </div>
          <div>
            <h1>{manifest.title || 'MyAsset Vault'}</h1>
            <p>
              {manifest.subtitle ||
                'Blender 3D · Imágenes · Fondos · Tiles · Música'}
            </p>
          </div>
        </div>
        <Toolbar
          query={query}
          setQuery={setQuery}
          favOnly={favOnly}
          setFavOnly={setFavOnly}
          sortBy={sortBy}
          setSortBy={setSortBy}
          onRescan={reload}
          resultCount={filtered.length}
          total={allCount}
          onShare={() => {
            navigator.clipboard?.writeText(window.location.href)
            setToast('Enlace copiado al portapapeles')
          }}
        />
      </header>

      <div className="layout">
        <Sidebar
          counts={all.counts}
          total={allCount}
          activeCat={activeCat}
          setActiveCat={setActiveCat}
        />

        <main className="content">
          {(favOnly || tagFilter.length > 0 || activeCat !== 'all') && (
            <div className="active-filters">
              <span className="label">Filtros:</span>
              {activeCat !== 'all' && (
                <button className="chip-btn" onClick={() => setActiveCat('all')}>
                  {all.list.length === 0
                    ? 'Categoría'
                    : all.list.find((a) => a.category === activeCat)?.catLabel ||
                      activeCat}
                  <X size={13} />
                </button>
              )}
              {tagFilter.map((t) => (
                <button key={t} className="tag-pill active" onClick={() => toggleTag(t)}>
                  <span>{t}</span>
                  <span className="x">
                    <X size={11} />
                  </span>
                </button>
              ))}
              {favOnly && (
                <button className="chip-btn active" onClick={() => setFavOnly(false)}>
                  ⭐ Favoritos <X size={13} />
                </button>
              )}
              <button className="tool-btn" onClick={clearFilters} style={{ marginLeft: 'auto' }}>
                <RefreshCw size={13} /> Limpiar todo
              </button>
            </div>
          )}

          {status === 'loading' && (
            <div className="state-box">
              <RefreshCw size={34} className="spin" />
              <h3>Escaneando tus assets…</h3>
            </div>
          )}

          {status === 'error' && (
            <div className="state-box">
              <div className="state-icon">
                <X size={34} />
              </div>
              <h3>No he podido leer el índice</h3>
              <p>
                Asegúrate de que el servidor está corriendo y que existe la carpeta{' '}
                <code>public/assets</code>.
              </p>
              <button className="chip-btn" onClick={reload}>
                <RefreshCw size={14} /> Reintentar
              </button>
            </div>
          )}

          {status === 'ready' && filtered.length === 0 && (
            <div className="state-box">
              <div className="state-icon">
                {allCount === 0 ? <LayoutGrid size={34} /> : <Copy size={34} />}
              </div>
              <h3>{allCount === 0 ? 'Tus assets aparecerán aquí' : 'Sin resultados'}</h3>
              <p>
                {allCount === 0
                  ? 'Mete archivos en public/assets (blender-3d, images, backgrounds, tiles, music, resources) y pulsa el botón de recargar. En dev se refrescan solos.'
                  : 'Prueba a quitar filtros o cambiar la búsqueda.'}
              </p>
              {allCount === 0 ? (
                <code>public/assets/images/mi-textura.png</code>
              ) : (
                <button className="chip-btn" onClick={clearFilters}>
                  Limpiar filtros
                </button>
              )}
            </div>
          )}

          {status === 'ready' && filtered.length > 0 && (
            <AssetGrid
              assets={filtered}
              onSelect={setSelected}
              onToggleFav={toggleFav}
              onTagClick={toggleTag}
              tagFilter={tagFilter}
            />
          )}
        </main>
      </div>

      {selected && (
        <PreviewModal
          asset={selected}
          total={filtered.length}
          pos={filtered.findIndex((a) => a.url === selected.url) + 1}
          onClose={() => setSelected(null)}
          onPrev={() => prevNext(-1)}
          onNext={() => prevNext(1)}
          onToggleFav={() => toggleFav(selected)}
          onTagClick={toggleTag}
          onTagRemove={removeTag}
          onAddTag={addTag}
          onUpdate={touchOverlay}
          allTags={[...all.tagCounts.keys()].sort((a, b) => a.localeCompare(b))}
        />
      )}

      {toast && (
        <div className="modal-backdrop" style={{ pointerEvents: 'none', zIndex: 200 }}>
          <div className="state-box" style={{ background: 'rgba(10,12,26,0.9)', padding: '18px 26px', borderRadius: 14, border: '1px solid var(--border-strong)' }}>
            <h3 style={{ fontSize: 14 }}>{toast}</h3>
          </div>
        </div>
      )}
    </div>
  )
}