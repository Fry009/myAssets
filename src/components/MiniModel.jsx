import { lazy, Suspense } from 'react'
import { Box } from 'lucide-react'

const Scene = lazy(() => import('./three/ModelScene.jsx'))

export function MiniModel({ src, ext }) {
  return (
    <Suspense
      fallback={
        <div className="thumb-pattern thumb-icon">
          <Box size={26} style={{ opacity: 0.55 }} />
        </div>
      }
    >
      <Scene src={src} ext={ext} variant="card" autoplay />
    </Suspense>
  )
}