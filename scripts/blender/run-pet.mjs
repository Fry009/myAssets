// Ejecuta pet_pipeline.py en Blender background, un proceso por mascota
// (en un mismo proceso el exportador glTF mezcla datos de escenas anteriores).
// node scripts/blender/run-pet.mjs fresa fuegito2 [--no-export] [--preview=<carpeta>]  ("fuegito2" = evo2)
// BLENDER=<ruta a blender.exe> para usar otra versión.
import path from 'node:path'; import { spawnSync } from 'node:child_process'
const BLENDER = process.env.BLENDER || 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
const args = process.argv.slice(2)
const pets = args.filter((a) => !a.startsWith('--'))
const flags = args.filter((a) => a.startsWith('--'))
const script = path.join(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/, '$1')), 'pet_pipeline.py')
for (const pet of pets) {
  const r = spawnSync(BLENDER, ['-b', '--factory-startup', '--python', script, '--', pet, ...flags], { encoding: 'utf8' })
  const out = (r.stdout || '') + (r.stderr || '')
  console.log(out.split('\n').filter((l) => /weights|keys|clips|_rig\.|Error|EXCEPTION/.test(l)).join('\n'))
  if (r.status !== 0 || /EXCEPTION|Traceback/.test(out)) { console.error(`✗ ${pet} falló`); process.exitCode = 1 }
}
