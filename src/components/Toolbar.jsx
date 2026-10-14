import { Heart, Link2, RefreshCw, Search } from 'lucide-react'

export function Toolbar({
  query,
  setQuery,
  favOnly,
  setFavOnly,
  sortBy,
  setSortBy,
  onRescan,
  onShare,
  resultCount,
  total,
}) {
  return (
    <div className="toolbar">
      <div className="search">
        <Search size={16} />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Busca por nombre, etiqueta o tipo…"
        />
      </div>
      <span className="results-count hide-sm">
        {resultCount}<span style={{ opacity: 0.5 }}>/{total}</span>
      </span>
      <button
        className={`chip-btn ${favOnly ? 'active' : ''}`}
        onClick={() => setFavOnly((v) => !v)}
        title="Solo favoritos"
      >
        <Heart size={14} fill={favOnly ? 'currentColor' : 'none'} />
        <span className="hide-sm">Favoritos</span>
      </button>
      <select
        className="sort-select"
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value)}
        title="Ordenar"
      >
        <option value="name">Nombre</option>
        <option value="size">Por peso</option>
        <option value="recent">Más recientes</option>
      </select>
      <button className="tool-btn" onClick={onShare} title="Copiar enlace">
        <Link2 size={15} />
      </button>
      <button
        className="tool-btn"
        onClick={onRescan}
        title="Volver a escanear public/assets"
      >
        <RefreshCw size={15} />
        <span className="hide-sm">Recargar</span>
      </button>
    </div>
  )
}