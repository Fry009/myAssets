# Checkpoint — myAssets / criaturitas PokeCodes

_Última actualización: 2026-10-14 (sesión 3: evo3 hecho → las 24 criaturitas con rig)_

## Qué es esto
Galería Vite + React (`npm run dev`) de assets. `npm run scan` regenera `public/asset-index.json`
a partir de `public/assets/**` + metadatos de `public/asset-tags.json` + miniaturas en `public/thumbs/<ruta>.png`.
El visor 3D (`src/components/ModelViewer.jsx`, `three/ModelScene.jsx`) detecta animaciones y morph targets
de los GLB y muestra un panel de rig (clips, presets de cara, sliders, parpadeo automático).

## Criaturitas — `public/assets/blender-3d/pokecodes/pets/<pet>/`
Cada una tiene `evo0..evo3.glb` (mallas IA texturizadas, 1 malla, suelo z=0, mirando a -Y, +X = izquierda del personaje).
Salida del rig: `evoN_rig.glb` + `.blend` (`<pet>_rig.blend` para evo0, `<pet>_evoN_rig.blend` para N≥1).

| Mascota | evo0 | evo1 | evo2 | evo3 |
|---|---|---|---|---|
| acero   | ✅ (scripts `acero_*.py`; reexportado con `use_active_scene`, ya sin "CrestHalo") | ✅ head, manos-puño | ✅ garras grandes | ✅ brazos-escudo (2 elipses/mano), `arm_amp` 0.6 |
| fresa   | ✅ top=hojas | ✅ head, alas de hojas como manos | ✅ zorro, tail, cara girada a +X | ✅ tail (2 elipses) |
| fuegito | ✅ top=llamas | ✅ head, tail (cola de llamas) | ✅ head, tail | ✅ tail; `hand_ymax` (llama gris tras el puño L) |
| hielo   | ✅ | ✅ head, tail; **sin manos** (sentado) | ✅ brazos de cristal, `hand_z` | ✅ brazos ajustados + `hand_ymax` (cristales de la espalda), tail |
| planta  | ✅ `lid` bajo por cejas | ✅ head, puños; `hand_exclude` rodilleras de musgo | ✅ brazos de roca, `hand_z` | ✅ brazos de roca |
| robot   | ✅ visor único, 9 caras | ✅ head, top=antena, 2 ojos + boca | ✅ 2 ojos sin boca (11 caras) | ✅ 2 ojos sin boca (11 caras) |

Animaciones (todas): `idle`, `walk`, `wave`, `jump`. Huesos opcionales `head`/`top`/`tail` reciben el
mismo movimiento secundario (cabeceo, lateral, meneo). Expresiones: blink(_L/_R), eyes_happy/wide/sad/angry,
look_*, mouth_open/smile/sad/o (robot evo0 visor único sin boca → 9; robot2 sin boca → 11).
Galería: tags + miniaturas (copia de la del evoN sin rig) añadidos para evo0..evo3; índice regenerado (81 archivos).
Todos los evo3 llevan `smooth=12` (difuminado de pesos).

Defectos conocidos aceptados: el parpadeo estira un poco la textura de encima del ojo; en Planta1 al
saltar (brazos a 55°) hay un leve estiramiento bajo los puños; en Fuegito3 queda una tira gris pequeña bajo
el puño L al saludar/saltar.

## Pipeline (scripts/blender/)
- `pet_pipeline.py` — genérico. `CONFIG["<pet>"]` = evo0, `CONFIG["<pet>N"]` = evoN. Regiones de peso con
  prioridad: (feet si `first`) → tail → manos → feet → top → head → body. Claves documentadas al inicio del fichero
  (hands/hand_in/shoulder/hand_exclude/hand_z, feet z/split/gap/xout/first, head, tail, top, eyes/eye_r/lid, mouth, front="auto").
  En bípedos (con `head`) cada región se limpia por conectividad (`main_component`, sobre la malla soldada por
  posición): se descartan trozos sueltos que caen en la elipse pero son de otra parte (muslo tras el puño, etc.).
- `run-pet.mjs` — `node scripts/blender/run-pet.mjs fresa2 robot2 [--no-export] [--preview=<carpeta>]`.
  Blender 5.2 en background, **un proceso por modelo**. `--preview` escribe `<carpeta>/<pet><N>_sheet.png`
  (pesos coloreados + 7 caras + 4 poses) usando `pet_preview.py`.
- Medir modelos nuevos: `pet_front_grid.py -- <out> fresa2 ...` (render frontal con rejilla, ortho 0.40 ⇒
  `x=(px-375)/1875`, `z=0.18+(375-py)/1875`) y `pet_face_closeup.py -- fresa2 cx cz <out>` (primer plano de la
  cara neutra/parpadeo, rejilla 1 cm, 5000 px/u) para afinar ojos. Ambos con `blender -b --factory-startup --python`.
- `blender-mcp.mjs` — cliente del addon blender_mcp (puerto 9876). Solo para inspección; exportar en background.
- `acero_rig.py / acero_anim.py / acero_export.py` — versión original solo para Acero evo0.
- Diagnóstico de estiramientos (scripts sueltos de la sesión 3, no versionados): vista lateral con rejilla de media
  malla (borrar vértices con x·k < xmin, cámara ortho 0.40 desde ±X) para ver a qué profundidad y está el brazo frente
  a lo que hay detrás → `hand_ymax`. Con cámara en +X la derecha de la imagen es +Y (detrás); desde -X, al revés.

### Gotchas aprendidos
- Export glTF en Blender 5.2 **crashea** dentro de `temp_override(view_layer=...)` → exportar sin override.
- `use_active_scene=True` en el export (si no, mete otras escenas, p.ej. el Cube por defecto).
- Varios modelos en el mismo proceso → el exportador mezcla huesos/clips: un proceso por modelo.
- En `blender -b` sí existe `window_manager.windows[0]`.
- Las "islas" de los GLB son cortes de UV → pesos por posición, no por islas.
- Ojos/boca son textura: si el párpado arrastra cejas/pelo, bajar `lid`; si el ojo no cierra, el centro/radio está mal
  medido (hacer primer plano).
- Brazos: elipses generosas (más grandes que la silueta) para que al levantar el brazo no se estiren tiras;
  `hand_in` con signo corta el lado del cuerpo; `shoulder` = pivote.
- Zonas grises que se estiran al levantar un brazo = geometría de detrás (llamas, cristales de espalda) metida en la
  elipse de la mano en proyección frontal → recortar con `hand_ymax` y elipses más ajustadas al brazo real.
- Scripts con `--factory-startup` que importan un GLB: filtrar el "Cube" por defecto al buscar la malla.
- El addon MCP del Blender abierto se colgó una vez tras un timeout del cliente (300 s). Reiniciar Blender si pasa.

## Probar la galería sin manos (headless)
No hay enlace directo a un modelo: hay que buscar y pulsar la tarjeta. Receta usada: `npx vite --port 5179` en segundo plano
+ `puppeteer-core` (instalado aparte, fuera del proyecto) con el Chrome del sistema
(`C:/Program Files/Google/Chrome/Application/chrome.exe`, args `--enable-unsafe-swiftshader`), escribir `evoN_rig` en
`input[placeholder^="Busca"]`, pulsar la `.card` cuyo `.card-title` empieza por la mascota y no contiene `.blend`, esperar
`.rig-panel`. Pulsar los chips con `element.click()` vía DOM: el clic por coordenadas falla mientras el modal se anima.

## Próximos pasos
1. (hecho, sesión 3) Los 24 `evoN_rig.glb` probados en el visor web: cargan en ~3.5 s, sin errores de consola, 4 clips,
   15 expresiones (robot: 9/15/11/11) y la animación se ve. Los evo3_rig pesan 26–34 MB.
   Presets de cara: en modelos sin boca (robots evo0/2/3) se quedan con la parte de ojos (Feliz/Sorpresa/Triste/Enfadado).
2. (hecho) Acero evo0 reexportado desde `acero_rig.blend` con `acero_export.py` (ahora con `use_active_scene=True`):
   GLB con una sola escena. Copia previa en el scratchpad de la sesión 3.
3. **Commit pendiente**: 170 ficheros / 1.9 GB sin versionar (GLB/.blend de 20–40 MB), remoto GitHub. Decidir con el
   usuario: Git LFS, ignorar binarios grandes o subirlos tal cual.
4. (Opcional) pulir Fuegito3 (tira gris) y revisar de cerca Fresa3 (mano R pequeña).
