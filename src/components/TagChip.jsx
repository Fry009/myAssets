export function TagChip({ tag, onClick, active, removable, onRemove }) {
  return (
    <span
      className={`tag-pill ${active ? 'active' : ''}`}
      onClick={(e) => {
        e.stopPropagation()
        onClick?.(tag)
      }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick?.(tag)
        }
      }}
    >
      <span>{tag}</span>
      {removable && (
        <span
          className="x"
          onClick={(e) => {
            e.stopPropagation()
            onRemove?.(tag)
          }}
        >
          ✕
        </span>
      )}
    </span>
  )
}