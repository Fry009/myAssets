import net from 'node:net'; import fs from 'node:fs'
const [type, arg] = process.argv.slice(2)
const params = type === 'execute_code' ? { code: fs.readFileSync(arg, 'utf8') } : {}
const s = net.connect(9876, '127.0.0.1', () => s.write(JSON.stringify({ type, params })))
let buf = ''
s.on('data', d => { buf += d; try { const r = JSON.parse(buf); console.log(r.status === 'success' ? (r.result?.result ?? JSON.stringify(r.result, null, 1)) : 'ERROR: ' + (r.message||buf)); s.end(); process.exit(0) } catch {} })
s.on('error', e => { console.log('SOCKET ERROR', e.message); process.exit(1) })
setTimeout(() => { console.log('TIMEOUT', buf.slice(0,500)); process.exit(1) }, 300000)
