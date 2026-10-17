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
| fuegito | ✅ top=llamas | ✅ head, tail (cola de llamas) | ✅ head, tail | ✅ tail; `hand_ymax`, `arm_amp` 0.75 |
| hielo   | ✅ | ✅ head, tail; **sin manos** (sentado) | ✅ brazos de cristal, `hand_z` | ✅ brazos ajustados + `hand_ymax` (cristales de la espalda), tail |
| planta  | ✅ `lid` bajo por cejas | ✅ head, puños; `hand_exclude` rodilleras (+`hand_exclude_y`), `arm_amp` 0.75 | ✅ brazos de roca, `hand_z` | ✅ brazos de roca |
| robot   | ✅ visor único, 9 caras | ✅ head, top=antena, 2 ojos + boca | ✅ 2 ojos sin boca (11 caras) | ✅ 2 ojos sin boca (11 caras) |

Animaciones (todas, 15): `getup` (empieza en la última pose de `faint`; ONE_SHOT), `special` (carga y lanza con
los dos brazos: manos espejadas L +PUNCH / R −PUNCH), `dodge` (salto lateral a +X y vuelta), `block` (guardia con los
dos brazos delante), `look` (73 f cíclico, gira torso y cabeza: head.Y = giro), `faint` (tambaleo y caída de espaldas girando `root` sobre los pies; el visor lo
reproduce una vez y se queda tumbado, `ONE_SHOT` en ModelScene.jsx), `idle`, `walk`, `run` (16 f, cíclico, fase en el aire), `wave`, `jump`, `attack` (golpe con L + giro de torso), `hurt` (retroceso),
`celebrate` (dos saltitos con brazos arriba), `sleep` (72 f, cabeceo + respiración). El visor pone una cara por clip
(`CLIP_FACES` en ModelViewer.jsx; vuelve a neutra al cambiar de clip si no la tocó el usuario). Acero evo0 usa las mismas
animaciones vía `acero_reanim.py` (abre su .blend, llama a `animate()` del pipeline y reexporta). Huesos opcionales `head`/`top`/`tail` reciben el
mismo movimiento secundario (cabeceo, lateral, meneo). Expresiones: blink(_L/_R), eyes_happy/wide/sad/angry,
look_*, mouth_open/smile/sad/o (robot evo0 visor único sin boca → 9; robot2 sin boca → 11).
Galería: tags + miniaturas (copia de la del evoN sin rig) añadidos para evo0..evo3; índice regenerado (81 archivos).
Todos los evo3 llevan `smooth=12` (difuminado de pesos).

Defectos conocidos aceptados: el parpadeo estira un poco la textura de encima del ojo (límite de ojos pintados
en textura). Lo gris que asoma en Planta1 (cara inferior del puño sin pintar) y Fuegito3 (pieza gris del propio
modelo tras el brazo L) al levantar los brazos no es deformación; el estiramiento real se redujo ~45% (sesión 3).
Repaso visual de las 24 en 3/4 (wave/jump): sin más defectos visibles.

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
- Medir estiramiento (sesión 3, script suelto `faces.py`): ejecutar el pipeline sin exportar, poner jump fr 11 y
  sumar el área añadida de los triángulos que crecen >4x, agrupada en celdas xz de 1 cm con sus pesos medios →
  dice qué frontera de pesos se estira. Contar aristas >2x no sirve: estas mallas tienen muchas aristas diminutas.
- Signos en `animate()`: `FWD=1` (body.X + = inclinarse hacia delante) y `PUNCH=-1` (hand.Z con ese signo = mano
  hacia delante); body.Y = giro del torso (− adelanta el hombro L). Verificados con vista lateral (cámara en +X).
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
3. (hecho) Commit en la rama `pokecodes-rigs` con Git LFS (`*.glb`, `*.blend`, `*.fbx` en .gitattributes; 77 ficheros,
   ~1.9 GB). **Sin push**: GitHub da 1 GB gratis de LFS → subirlo requiere ampliar la cuota. Decidir antes de `git push`.
4. (hecho) Pulido: Planta1 y Fuegito3 reajustados y reexportados.
5. (hecho) 4 animaciones nuevas en las 24 + caras por clip en el visor; verificado en navegador.
6. (hecho) Movimiento mejorado: inercia (head 2 f, top 3 f, tail 4 f de retraso), bucles con modificador Cycles en
   idle (97 f, 2 respiraciones + cambio de peso), walk (pie que pasa levantado, giro de cadera, rebote) y sleep;
   los clips de una vez se alargan 4 f. Verificado: bucles cierran exactos, pies/manos opuestos (bonepos).
7. (hecho) Clip `run`. Push: rama `pokecodes-rigs` subida hasta c28c170 (~5.9 GB LFS usados; cuota GitHub Free = 10 GiB
   almacenamiento + 10 GiB descarga/mes). Subir por tandas validadas y juntar antes los commits locales (`git reset --soft origin/pokecodes-rigs`) para
   no subir versiones intermedias de los GLB.
8. (hecho) Cola en cadena de 3 huesos (`TAIL_N`): tramos repartidos entre el inicio real y el final de la cola
   (percentiles 3–97 de t a lo largo de pivot→tip), articulaciones = centro de los vértices de cada corte, pesos
   lineales entre vecinos; en la animación cada tramo gira 1/3 con retraso 3/5/7 f (onda). Solo afecta a los 7
   modelos con cola (fuegito1, hielo1, fresa2, fuegito2, fresa3, fuegito3, hielo3), reexportados solo esos.
9. (hecho) Inercia de brazos por clip (`make(..., lag={...})`): idle 3 f, walk 2 f, run 1 f.
10. (hecho) `top="auto"` en fresa1-3, fuegito1-3, hielo1-3: puntas de orejas/llamas/hojas por encima del 55% entre
   ojos y punta de cabeza, con retraso 3 f. No en acero/planta/robot2-3 (metal/roca).
11. (hecho) 5 clips nuevos: getup, special, dodge, block, look. Suelo comprobado en getup (±0.4 cm).
Las caras se quedan como están (decisión del usuario: todo 3D, robots sin boca tal cual).
Ideas siguientes: animar también las shape keys dentro de los clips del GLB (para que un motor de juego reciba la cara
sin depender del visor), clips extra (p.ej. `faint`, `run`), y mejorar el parpadeo.
