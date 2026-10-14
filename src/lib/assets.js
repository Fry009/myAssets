import {
  Box,
  Image as ImageIcon,
  Images,
  LayoutGrid,
  Music,
  Package,
  FolderOpen,
  Shapes,
} from 'lucide-react'

export const CATEGORIES = [
  {
    key: 'blender-3d',
    label: '3D Models',
    icon: Shapes,
    hint: 'GLB · GLTF · OBJ · FBX · BLEND',
    quality: ['glb', 'gltf', 'obj', 'fbx', 'blend', '3ds', 'dae', 'stl'],
  },
  { key: 'images', label: 'Imágenes', icon: Images, hint: 'PNG · JPG · WEBP · GIF' },
  { key: 'backgrounds', label: 'Fondos', icon: Box, hint: 'Wallpapers · cielos · VA' },
  { key: 'tiles', label: 'Tiles', icon: LayoutGrid, hint: 'Seamless · patrones' },
  { key: 'music', label: 'Música', icon: Music, hint: 'WAV · MP3 · OGG · FLAC · M4A' },
  { key: 'resources', label: 'Recursos', icon: Package, hint: 'Otros archivos' },
]

export const FALLBACK_CATEGORY = 'resources'

export const IMAGE_EXT = new Set(['png', 'jpg', 'jpeg', 'webp', 'gif', 'svg', 'avif', 'bmp'])
export const AUDIO_EXT = new Set(['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac', 'opus'])
export const MODEL_EXT = new Set(['glb', 'gltf', 'obj', 'fbx', 'blend', '3ds', 'dae', 'stl'])
export const GLTF_EXT = new Set(['glb', 'gltf'])
export const PREVIEWABLE_3D = new Set(['glb', 'gltf', 'obj', 'fbx'])

export function categoryOf(url, ext) {
  const top = String(url).split('/')[1] || ''
  const found = CATEGORIES.find((c) => c.key === top)
  if (found) return found.key
  if (ext && MODEL_EXT.has(ext)) return 'blender-3d'
  if (ext && AUDIO_EXT.has(ext)) return 'music'
  if (ext && IMAGE_EXT.has(ext)) return 'images'
  return FALLBACK_CATEGORY
}

export function categoryConfig(url, ext) {
  const key = categoryOf(url, ext)
  return CATEGORIES.find((c) => c.key === key) || CATEGORIES[CATEGORIES.length - 1]
}

export function humanSize(bytes) {
  if (!bytes && bytes !== 0) return '—'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let n = bytes
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024
    i++
  }
  return `${n >= 100 || i === 0 ? Math.round(n) : n.toFixed(1)} ${units[i]}`
}

export function humanDate(ms) {
  if (!ms) return ''
  const d = new Date(ms)
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const yyyy = d.getFullYear()
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${dd}/${mm}/${yyyy} · ${hh}:${mi}`
}

export function downloadFile(url, name) {
  return fetch(url)
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      return r.blob()
    })
    .then((blob) => {
      const a = document.createElement('a')
      const href = URL.createObjectURL(blob)
      a.href = href
      a.download = name
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => URL.revokeObjectURL(href), 10000)
    })
}

export function searchFields(asset) {
  return [
    asset.name,
    asset.title,
    asset.desc,
    asset.ext,
    asset.category,
    ...asset.tags,
    asset.url,
  ]
    .join(' ')
    .toLowerCase()
}