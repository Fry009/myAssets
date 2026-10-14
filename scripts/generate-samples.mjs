import fs from 'node:fs'
import path from 'node:path'
import zlib from 'node:zlib'

const publicDir = path.resolve('public')
const A = (rel) => path.join(publicDir, rel)

/* ---------------------------------- PNG ---------------------------------- */
const crcTable = (() => {
  const t = []
  for (let n = 0; n < 256; n++) {
    let c = n
    for (let k = 0; k < 8; k++) c = (c & 1 ? 0xedb88320 : 0) ^ (c >>> 1)
    t[n] = c >>> 0
  }
  return t
})()
function crc32(buf) {
  let c = 0xffffffff
  for (const b of buf) c = crcTable[(c ^ b) & 0xff] ^ (c >>> 8)
  return (c ^ 0xffffffff) >>> 0
}
function pngChunk(type, data) {
  const len = Buffer.alloc(4)
  len.writeUInt32BE(data.length)
  const t = Buffer.from(type, 'ascii')
  const crc = Buffer.alloc(4)
  crc.writeUInt32BE(crc32(Buffer.concat([t, data])))
  return Buffer.concat([len, t, data, crc])
}
function encodePng(width, height, pixelFn) {
  const rowBytes = width * 3
  const raw = Buffer.alloc(height * (1 + rowBytes))
  for (let y = 0; y < height; y++) {
    const rowStart = y * (1 + rowBytes)
    raw[rowStart] = 0
    for (let x = 0; x < width; x++) {
      const [r, g, b] = pixelFn(x, y)
      const i = rowStart + 1 + x * 3
      raw[i] = r
      raw[i + 1] = g
      raw[i + 2] = b
    }
  }
  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(width, 0)
  ihdr.writeUInt32BE(height, 4)
  ihdr[8] = 8 // bit depth
  ihdr[9] = 2 // color type RGB
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])
  return Buffer.concat([
    sig,
    pngChunk('IHDR', ihdr),
    pngChunk('IDAT', zlib.deflateSync(raw, { level: 9 })),
    pngChunk('IEND', Buffer.alloc(0)),
  ])
}
const clamp = (v) => Math.max(0, Math.min(255, Math.round(v)))

/* -------------------------------- GRADIENTS ------------------------------- */
function gradient(w, h, a, b, kind = 'linear') {
  const a1 = [a[0] / 255, a[1] / 255, a[2] / 255]
  const b1 = [b[0] / 255, b[1] / 255, b[2] / 255]
  return encodePng(w, h, (x, y) => {
    const t =
      kind === 'radial'
        ? Math.min(1, Math.hypot(x / w - 0.5, y / h - 0.5) * Math.sqrt(2))
        : x / w
    return [
      clamp((a1[0] + (b1[0] - a1[0]) * t) * 255 + Math.sin(y * 0.05) * 6),
      clamp((a1[1] + (b1[1] - a1[1]) * t) * 255 + Math.cos(x * 0.05) * 6),
      clamp((a1[2] + (b1[2] - a1[2]) * t) * 255 + Math.sin((x + y) * 0.04) * 6),
    ]
  })
}

/* ---------------------------------- WAV ---------------------------------- */
function wav(samples) {
  const rate = 44100
  const data = Buffer.alloc(44 + samples.length * 2)
  data.write('RIFF', 0)
  data.writeUInt32LE(36 + samples.length * 2, 4)
  data.write('WAVE', 8)
  data.write('fmt ', 12)
  data.writeUInt32LE(16, 16)
  data.writeUInt16LE(1, 20)
  data.writeUInt16LE(1, 22)
  data.writeUInt32LE(rate, 24)
  data.writeUInt32LE(rate * 2, 28)
  data.writeUInt16LE(2, 32)
  data.writeUInt16LE(16, 34)
  data.write('data', 36)
  data.writeUInt32LE(samples.length * 2, 40)
  for (let i = 0; i < samples.length; i++)
    data.writeInt16LE(Math.max(-32768, Math.min(32767, samples[i] * 32767)), 44 + i * 2)
  return data
}

function sampleMusic(seconds = 2.4) {
  const rate = 44100
  const n = Math.floor(rate * seconds)
  const out = new Float32Array(n)
  const freqs = [261.63, 329.63, 392.0, 523.25] // C E G C
  for (let i = 0; i < n; i++) {
    const t = i / rate
    const seg = Math.min(freqs.length - 1, Math.floor(t / (seconds / freqs.length)))
    const f = freqs[seg]
    const env = Math.pow(1 - t / seconds, 1.6)
    const vib = 1 + 0.003 * Math.sin(2 * Math.PI * 5 * t)
    const s = Math.sin(2 * Math.PI * f * vib * t) + 0.4 * Math.sin(2 * Math.PI * f * 0.5 * t)
    out[i] = s * env * 0.55
  }
  return out
}

/* ---------------------------------- GLB ---------------------------------- */
function glb(jsonObj, binBuf) {
  const jsonBuf = Buffer.from(JSON.stringify(jsonObj))
  const pad = (b) => {
    const n = b.length % 4
    return n ? Buffer.concat([b, Buffer.alloc(4 - n)]) : b
  }
  const j = pad(jsonBuf)
  const b = pad(binBuf)
  const len = 12 + 8 + j.length + 8 + b.length
  const out = Buffer.alloc(len)
  out.writeUInt32LE(0x46546c67, 0)
  out.writeUInt32LE(2, 4)
  out.writeUInt32LE(len, 8)
  out.writeUInt32LE(j.length, 12)
  out.writeUInt32LE(0x4e4f534a, 16)
  j.copy(out, 20)
  const off = 20 + j.length
  out.writeUInt32LE(b.length, off)
  out.writeUInt32LE(0x004e4942, off + 4)
  b.copy(out, off + 8)
  return out
}

function tetrahedronGlb() {
  const v = [
    [0, 1, 0],
    [0, -0.35, -0.9],
    [0.85, -0.35, 0.5],
    [-0.85, -0.35, 0.5],
  ]
  const rgb = [
    [1.0, 0.45, 0.7],
    [0.3, 0.8, 1.0],
    [1.0, 0.9, 0.4],
    [0.55, 1.0, 0.5],
  ]
  const idx = [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3]
  const pos = new Float32Array(v.flat().map((n) => n.toFixed(5)))
  const col = new Float32Array(rgb.flatMap((c) => [...c.map((n) => n.toFixed(5)), 1]))
  const idxB = new Uint16Array(idx)
  const bin = Buffer.alloc(pos.byteLength + col.byteLength + idxB.byteLength)
  Buffer.from(pos.buffer).copy(bin, 0)
  Buffer.from(col.buffer).copy(bin, pos.byteLength)
  Buffer.from(idxB.buffer).copy(bin, pos.byteLength + col.byteLength)
  const json = {
    asset: { version: '2.0', generator: 'myassets-sample' },
    scene: 0,
    scenes: [{ nodes: [0] }],
    nodes: [{ mesh: 0, rotation: [0, 0, 0, 1] }],
    meshes: [{ primitives: [{ attributes: { POSITION: 0, COLOR_0: 1 }, indices: 2, mode: 4 }] }],
    accessors: [
      {
        bufferView: 0,
        componentType: 5126,
        count: 4,
        type: 'VEC3',
        min: [-0.85, -0.35, -0.9],
        max: [0.85, 1, 0.5],
      },
      { bufferView: 1, componentType: 5126, count: 4, type: 'VEC4' },
      { bufferView: 2, componentType: 5123, count: 12, type: 'SCALAR' },
    ],
    bufferViews: [
      { buffer: 0, byteOffset: 0, byteLength: pos.byteLength, target: 34962 },
      { buffer: 0, byteOffset: pos.byteLength, byteLength: col.byteLength, target: 34962 },
      { buffer: 0, byteOffset: pos.byteLength + col.byteLength, byteLength: idxB.byteLength, target: 34963 },
    ],
    buffers: [{ byteLength: bin.length }],
  }
  return glb(json, bin)
}

/* -------------------------------- ASSETS -------------------------------- */
const ops = [
  [A('assets/blender-3d/sample-tetrahedron.glb'), tetrahedronGlb()],
  [A('assets/images/sample-flowers.png'), gradient(640, 400, [28, 20, 60], [230, 120, 160])],
  [A('assets/backgrounds/sample-aurora.png'), gradient(640, 360, [5, 18, 40], [20, 200, 190], 'radial')],
  [
    A('assets/tiles/sample-tile.png'),
    encodePng(256, 256, (x, y) => {
      const bx = Math.floor(x / 64) % 2
      const by = Math.floor(y / 64) % 2
      const light = x % 64 < 58 && y % 64 < 58 && x % 8 > 0 && y % 8 > 0 ? 55 : 0
      const t = bx ^ by ? 210 : 120
      const v = clamp(t + light)
      return [v, v, v + 8]
    }),
  ],
  [A('assets/music/sample-chord.wav'), wav(sampleMusic())],
]

for (const [file, buf] of ops) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, buf)
  console.log(`✓ generado ${path.relative(publicDir, file)} (${buf.length} bytes)`)
}
console.log('\nBorra los ficheros “sample-*” cuando tengas tus propios assets.')