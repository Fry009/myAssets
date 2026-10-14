import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve('public/assets')
const out = path.resolve('public/asset-index.json')
const files = []

if (fs.existsSync(root)) {
  const walk = (dir, rel) => {
    const entries = fs.readdirSync(dir, { withFileTypes: true })
    entries.sort((a, b) => a.name.localeCompare(b.name, 'es', { numeric: true }))
    for (const e of entries) {
      if (e.name.startsWith('.')) continue
      const full = path.join(dir, e.name)
      const url = rel + '/' + e.name
      if (e.isDirectory()) {
        walk(full, url)
      } else {
        const ext = path.extname(e.name).slice(1).toLowerCase()
        const st = fs.statSync(full)
        // Miniatura pre-renderizada opcional: public/thumbs/<ruta>.png
        const thumb = fs.existsSync(path.resolve('public/thumbs' + url + '.png'))
          ? '/thumbs' + url + '.png'
          : undefined
        files.push({
          url,
          name: e.name,
          ext,
          size: st.size,
          mtime: st.mtimeMs,
          thumb,
        })
      }
    }
  }
  walk(root, '')
}

fs.mkdirSync(path.dirname(out), { recursive: true })
fs.writeFileSync(out, JSON.stringify({ files }, null, 2))
console.log(`✓ indexados ${files.length} archivos → public/asset-index.json`)
