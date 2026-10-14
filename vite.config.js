import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import fs from 'node:fs'

function scanAssets() {
  const root = path.resolve('public/assets')
  const files = []
  if (fs.existsSync(root)) {
    const walk = (dir, rel) => {
      for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
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
  return files
}

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'asset-dynamic-index',
      configureServer(server) {
        server.middlewares.use('/asset-index.json', (_req, res) => {
          res.setHeader('Content-Type', 'application/json; charset=utf-8')
          res.setHeader('Cache-Control', 'no-store')
          res.end(JSON.stringify({ files: scanAssets() }))
        })
      },
    },
  ],
})
