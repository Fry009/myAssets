import { motion } from 'framer-motion'
import { AssetCard } from './AssetCard.jsx'

export function AssetGrid({ assets, onSelect, onToggleFav, onTagClick, tagFilter }) {
  return (
    <div className="card-grid">
      {assets.map((a) => (
        <motion.div
          key={a.url}
          layout
          initial={{ opacity: 0, y: 16, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.28, ease: 'easeOut' }}
        >
          <AssetCard
            asset={a}
            onSelect={onSelect}
            onToggleFav={onToggleFav}
            onTagClick={onTagClick}
            isTagActive={(t) => tagFilter.includes(t)}
          />
        </motion.div>
      ))}
    </div>
  )
}