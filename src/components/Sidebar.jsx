import { Star, Folder } from 'lucide-react'
import { CATEGORIES } from '../lib/assets.js'

export function Sidebar({ counts, total, activeCat, setActiveCat }) {
  return (
    <aside className="sidebar">
      <div className="side-label">Categorías</div>
      <button
        className={`cat-item ${activeCat === 'all' ? 'active' : ''}`}
        onClick={() => setActiveCat('all')}
      >
        <span className="cat-icon">
          <Folder size={15} />
        </span>
        <span className="cat-name">Todo</span>
        <span className="count">{total}</span>
      </button>
      {CATEGORIES.map((c) => {
        const Icon = c.icon
        const n = counts.get(c.key) || 0
        return (
          <button
            key={c.key}
            className={`cat-item ${activeCat === c.key ? 'active' : ''}`}
            onClick={() => setActiveCat(c.key)}
            title={`${c.label} — ${c.hint || ''}`.trim()}
          >
            <span className="cat-icon">
              <Icon size={15} />
            </span>
            <span className="cat-name">{c.label}</span>
            <span className="count">{n}</span>
          </button>
        )
      })}
      <div className="side-label" style={{ marginTop: 6 }}>
        Atajos
      </div>
      <button
        className="cat-item"
        onClick={() => undefined}
        style={{ cursor: 'default' }}
      >
        <span className="cat-icon">
          <Star size={15} />
        </span>
        <span className="cat-name">Doble clic · preview</span>
      </button>
    </aside>
  )
}