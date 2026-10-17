# Pipeline genérico de rig para mascotas PokeCodes (evo0).
# Uso:  node scripts/blender/run-pet.mjs fresa [fuegito ...] [--no-export]
#   (lanza blender -b --factory-startup --python pet_pipeline.py -- <pet>, UN proceso por mascota:
#    en un mismo proceso el exportador glTF mezcla huesos/animaciones de escenas anteriores)
#   Vía MCP con Blender abierto: anteponer PETS=["fresa"]; EXPORT=False y ejecutar el fichero
#   (útil con pet_preview.py para revisar; exportar mejor en background).
# Hace: importar evoN.glb -> armature + pesos -> shape keys -> acciones NLA -> exportar
#       <pet>/evoN_rig.glb + <pet>/<pet>_rig.blend
# Coordenadas: modelo en el suelo (z=0), mirando a -Y. +X = izquierda del personaje (L).
# Medidas sacadas de renders ortográficos frontales (2500 px/unidad).
import bpy, numpy as np, math, os
R = math.radians
BASE = r"C:\Users\Fran\Desktop\Fran\myAssets\public\assets\blender-3d\pokecodes\pets"

# hands: {side: (cx, cz, rx, rz)} elipse frontal de la mano; hand_in: (a,b) corte interior en |x|
# feet: z_top (a,b) transición, split x entre pies, gap (a,b) en |x-split|; xout (a,b) límite exterior;
#   first=True -> las piernas tienen prioridad sobre las manos
# hand_ymax: (a,b) profundidad máxima de las manos (lo de detrás, p.ej. cristales de la espalda, es cuerpo)
# hand_z: (a,b) techo de las manos (lo de encima es cabeza/cuerpo)
# hand_exclude: elipses que nunca van a las manos (p.ej. rodilleras que se solapan con el puño en proyección)
# hand_exclude_y: (a,b) la exclusión solo actúa detrás (y>b); lo de delante (el puño) sigue siendo mano
# eyes: {L/R/C: (x,z)}, eye_r: (ERX,ERZ); mouth: (x,z,MRX,MRZ) o None
# front: (a,b) y -> 1 en y<a, 0 en y>b ; top: (a,b) z para bone "top" (hojas/llamas/antena) o None;
#   top="auto": lo que queda por encima del 55% entre los ojos y la punta de la cabeza (pelo, llamas, orejas)
# head: (a,b) z del cuello -> bone "head" (bípedos); shoulder: {L/R: (x,z)} pivote del brazo;
#   hand_in también puede ser {L: x, R: x} (borde interior con signo); hands admite lista de elipses
# tail: dict(ell=elipse(s), ymin=(a,b) opcional (solo lo de detrás), pivot=(x,z), tip=(x,z))
# front="auto": capa más frontal calculada por celdas xz (para modelos nuevos)
# Claves de CONFIG: "<pet>" = evo0, "<pet>N" = evoN
# arm_amp: escala de las rotaciones de brazos en las animaciones (modelos con brazos muy fusionados)
# smooth: iteraciones de suavizado de pesos sobre la malla (bordes más graduales; evo3)
# lid: radio (en unidades de ojo) hasta donde arrastra el párpado superior (def. 1.45; menor si hay cejas)
CONFIG = {
    "fresa": dict(
        hands={"L": (0.082, 0.051, 0.022, 0.022), "R": (-0.082, 0.051, 0.022, 0.022)}, hand_in=(0.058, 0.066),
        feet=dict(z=(0.024, 0.034), split=0.0, gap=(0.010, 0.020)),
        eyes={"L": (0.036, 0.097), "R": (-0.036, 0.096)}, eye_r=(0.021, 0.024),
        mouth=(-0.001, 0.079, 0.011, 0.009), front=(-0.022, -0.012), top=(0.160, 0.172), lid=1.22),
    "fuegito": dict(
        hands={"L": (0.090, 0.049, 0.024, 0.022), "R": (-0.080, 0.060, 0.032, 0.042)}, hand_in=(0.058, 0.068),
        feet=dict(z=(0.020, 0.030), split=0.010, gap=(0.006, 0.014)),
        eyes={"L": (0.053, 0.088), "R": (-0.022, 0.086)}, eye_r=(0.0225, 0.025),
        mouth=(0.014, 0.074, 0.011, 0.0095), front=(-0.024, -0.012), top=(0.135, 0.165)),
    "hielo": dict(
        hands={"L": (0.095, 0.064, 0.026, 0.030), "R": (-0.095, 0.064, 0.026, 0.030)}, hand_in=(0.068, 0.078),
        feet=dict(z=(0.038, 0.048), split=0.0, gap=(0.004, 0.012)),
        eyes={"L": (0.040, 0.110), "R": (-0.038, 0.110)}, eye_r=(0.020, 0.022),
        mouth=(-0.001, 0.089, 0.012, 0.0095), front=(-0.035, -0.020), top=None),
    "planta": dict(
        hands={"L": (0.094, 0.062, 0.024, 0.032), "R": (-0.092, 0.065, 0.024, 0.032)}, hand_in=(0.072, 0.082),
        feet=dict(z=(0.024, 0.034), split=0.0, gap=(0.004, 0.012)),
        eyes={"L": (0.041, 0.104), "R": (-0.041, 0.104)}, eye_r=(0.023, 0.023),
        mouth=(0.0, 0.080, 0.014, 0.012), front=(-0.024, -0.012), top=None, lid=1.18),
    "robot": dict(
        hands={"L": (0.072, 0.054, 0.030, 0.026), "R": (-0.075, 0.054, 0.030, 0.026)}, hand_in=(0.038, 0.046),
        feet=dict(z=(0.026, 0.036), split=0.0, gap=(0.004, 0.012)),
        eyes={"C": (0.0, 0.132)}, eye_r=(0.042, 0.029),
        mouth=None, front=(-0.030, -0.018), top=(0.195, 0.208)),

    # ---- evo1: bípedos con cabeza; medidas de renders ortho 0.40 (1875 px/u, x=(px-375)/1875, z=0.18+(375-py)/1875)
    "acero1": dict(
        head=(0.118, 0.130),
        hands={"L": (0.100, 0.100, 0.060, 0.050), "R": (-0.100, 0.100, 0.060, 0.050)}, hand_in={"L": 0.048, "R": -0.048},
        shoulder={"L": (0.050, 0.115), "R": (-0.050, 0.115)},
        feet=dict(z=(0.058, 0.072), split=0.0, gap=(0.006, 0.016), xout=(0.078, 0.088), first=True),
        eyes={"L": (0.033, 0.161), "R": (-0.027, 0.160)}, eye_r=(0.019, 0.021),
        mouth=(0.003, 0.141, 0.008, 0.007), front="auto"),
    "fresa1": dict(
        head=(0.092, 0.106),
        hands={"L": (0.100, 0.082, 0.050, 0.055), "R": (-0.100, 0.082, 0.050, 0.055)}, hand_in={"L": 0.055, "R": -0.055},
        shoulder={"L": (0.055, 0.095), "R": (-0.055, 0.095)},
        feet=dict(z=(0.055, 0.070), split=0.0, gap=(0.004, 0.012), xout=(0.060, 0.068), first=True),
        eyes={"L": (0.036, 0.150), "R": (-0.035, 0.148)}, eye_r=(0.018, 0.022),
        mouth=(-0.002, 0.130, 0.011, 0.010), front="auto", top="auto", lid=1.15),
    "fuegito1": dict(
        head=(0.100, 0.115),
        tail=dict(ell=(-0.080, 0.103, 0.053, 0.077), ymin=(-0.005, 0.008), pivot=(-0.025, 0.060), tip=(-0.070, 0.090)),
        hands={"L": (0.110, 0.084, 0.032, 0.036), "R": (-0.042, 0.083, 0.030, 0.036)}, hand_in={"L": 0.088, "R": -0.026},
        shoulder={"L": (0.085, 0.100), "R": (-0.026, 0.100)},
        feet=dict(z=(0.062, 0.076), split=0.024, gap=(0.008, 0.018)),
        eyes={"L": (0.084, 0.1465), "R": (0.015, 0.147)}, eye_r=(0.019, 0.0215),
        mouth=(0.049, 0.119, 0.008, 0.005), front="auto", top="auto", lid=1.15),
    "hielo1": dict(
        head=(0.095, 0.110),
        tail=dict(ell=(-0.093, 0.052, 0.032, 0.043), ymin=(-0.005, 0.008), pivot=(-0.050, 0.040), tip=(-0.090, 0.060)),
        feet=dict(z=(0.045, 0.060), split=0.007, gap=(0.010, 0.020)),
        eyes={"L": (0.045, 0.150), "R": (-0.030, 0.150)}, eye_r=(0.019, 0.023),
        mouth=(0.004, 0.127, 0.010, 0.010), front="auto", top="auto"),
    "planta1": dict(
        head=(0.112, 0.126),
        hands={"L": (0.101, 0.101, 0.043, 0.059), "R": (-0.103, 0.101, 0.043, 0.059)}, hand_in={"L": 0.060, "R": -0.060},
        shoulder={"L": (0.060, 0.130), "R": (-0.060, 0.130)},
        feet=dict(z=(0.062, 0.076), split=0.0, gap=(0.006, 0.016), xout=(0.068, 0.078), first=True),
        hand_exclude=[(0.078, 0.066, 0.020, 0.014), (-0.078, 0.066, 0.020, 0.014)], hand_exclude_y=(0.016, 0.024), arm_amp=0.75,
        eyes={"L": (0.032, 0.162), "R": (-0.042, 0.162)}, eye_r=(0.021, 0.024),
        mouth=(-0.003, 0.143, 0.012, 0.011), front="auto", lid=1.18),
    "robot1": dict(
        head=(0.118, 0.130),
        hands={"L": (0.084, 0.089, 0.029, 0.032), "R": (-0.083, 0.089, 0.029, 0.032)}, hand_in={"L": 0.055, "R": -0.055},
        shoulder={"L": (0.055, 0.115), "R": (-0.055, 0.115)},
        feet=dict(z=(0.058, 0.072), split=0.0, gap=(0.006, 0.016)),
        eyes={"L": (0.028, 0.160), "R": (-0.038, 0.160)}, eye_r=(0.021, 0.022),
        mouth=(-0.002, 0.145, 0.007, 0.004), front="auto", top=(0.215, 0.230)),

    # ---- evo2 (mismas medidas de render que evo1)
    "acero2": dict(
        head=(0.145, 0.157),
        hands={"L": (0.096, 0.119, 0.060, 0.085), "R": (-0.096, 0.119, 0.060, 0.085)}, hand_in={"L": 0.045, "R": -0.045},
        shoulder={"L": (0.050, 0.140), "R": (-0.050, 0.140)},
        feet=dict(z=(0.070, 0.082), split=0.0, gap=(0.006, 0.016), xout=(0.094, 0.102), first=True),
        eyes={"L": (0.0336, 0.190), "R": (-0.0276, 0.191)}, eye_r=(0.017, 0.0195),
        mouth=(0.008, 0.166, 0.006, 0.004), front="auto", lid=1.2),
    "fresa2": dict(
        head=(0.130, 0.145),
        tail=dict(ell=(-0.085, 0.129, 0.050, 0.085), ymin=(0.012, 0.022), pivot=(-0.030, 0.060), tip=(-0.080, 0.100)),
        hands={"L": (0.085, 0.084, 0.045, 0.058), "R": (-0.055, 0.084, 0.045, 0.058)}, hand_in={"L": 0.050, "R": -0.024},
        shoulder={"L": (0.050, 0.120), "R": (-0.024, 0.120)},
        feet=dict(z=(0.056, 0.070), split=0.013, gap=(0.006, 0.014), xout=(0.050, 0.058), first=True),
        eyes={"L": (0.0606, 0.179), "R": (-0.004, 0.181)}, eye_r=(0.016, 0.020),
        mouth=(0.029, 0.152, 0.009, 0.005), front="auto", top="auto", lid=1.15),
    "fuegito2": dict(
        head=(0.127, 0.140),
        tail=dict(ell=(-0.083, 0.100, 0.055, 0.080), ymin=(-0.005, 0.008), pivot=(-0.030, 0.070), tip=(-0.080, 0.110)),
        hands={"L": (0.112, 0.092, 0.045, 0.050), "R": (-0.045, 0.089, 0.040, 0.050)}, hand_in={"L": 0.090, "R": -0.030},
        shoulder={"L": (0.090, 0.125), "R": (-0.030, 0.125)},
        feet=dict(z=(0.070, 0.084), split=0.024, gap=(0.008, 0.018)),
        eyes={"L": (0.078, 0.180), "R": (0.009, 0.182)}, eye_r=(0.021, 0.020),
        mouth=(0.051, 0.150, 0.008, 0.004), front="auto", top="auto", lid=1.15),
    "hielo2": dict(
        head=(0.132, 0.145),
        hands={"L": (0.099, 0.129, 0.080, 0.100), "R": (-0.099, 0.129, 0.080, 0.100)}, hand_in={"L": 0.045, "R": -0.045}, hand_z=(0.138, 0.150),
        shoulder={"L": (0.045, 0.130), "R": (-0.045, 0.130)},
        feet=dict(z=(0.060, 0.075), split=0.0, gap=(0.006, 0.016), xout=(0.080, 0.090), first=True),
        eyes={"L": (0.040, 0.190), "R": (-0.032, 0.190)}, eye_r=(0.019, 0.022),
        mouth=(0.005, 0.164, 0.008, 0.006), front="auto", top="auto", lid=1.15),
    "planta2": dict(
        head=(0.132, 0.145),
        hands={"L": (0.112, 0.113, 0.060, 0.085), "R": (-0.112, 0.113, 0.060, 0.085)}, hand_in={"L": 0.070, "R": -0.070}, hand_z=(0.172, 0.188),
        shoulder={"L": (0.070, 0.140), "R": (-0.070, 0.140)},
        feet=dict(z=(0.070, 0.084), split=0.0, gap=(0.006, 0.016), xout=(0.085, 0.095), first=True),
        eyes={"L": (0.034, 0.1786), "R": (-0.0274, 0.1786)}, eye_r=(0.016, 0.018),
        mouth=(0.002, 0.152, 0.016, 0.005), front="auto", lid=1.1),
    "robot2": dict(
        head=(0.163, 0.175),
        hands={"L": (0.090, 0.119, 0.055, 0.070), "R": (-0.090, 0.119, 0.055, 0.070)}, hand_in={"L": 0.045, "R": -0.045},
        shoulder={"L": (0.050, 0.155), "R": (-0.050, 0.155)},
        feet=dict(z=(0.094, 0.106), split=0.0, gap=(0.006, 0.016), xout=(0.085, 0.092), first=True),
        eyes={"L": (0.0286, 0.215), "R": (-0.0436, 0.2154)}, eye_r=(0.012, 0.019),
        mouth=None, front="auto", lid=1.1),

    # ---- evo3 (mismas medidas de render que evo1)
    "acero3": dict(
        smooth=12,
        head=(0.188, 0.200),
        hands={"L": [(0.105, 0.225, 0.045, 0.065), (0.120, 0.120, 0.030, 0.060)],
               "R": [(-0.105, 0.225, 0.045, 0.065), (-0.120, 0.120, 0.030, 0.060)]},
        hand_in={"L": 0.064, "R": -0.064}, hand_z=(0.288, 0.300), arm_amp=0.6,
        shoulder={"L": (0.065, 0.200), "R": (-0.065, 0.200)},
        feet=dict(z=(0.110, 0.124), split=0.0, gap=(0.006, 0.016), xout=(0.098, 0.106), first=True),
        eyes={"L": (0.038, 0.232), "R": (-0.021, 0.232)}, eye_r=(0.017, 0.017),
        mouth=(0.010, 0.196, 0.006, 0.004), front="auto", lid=1.15),
    "fresa3": dict(
        smooth=12,
        head=(0.185, 0.198),
        tail=dict(ell=[(-0.100, 0.170, 0.042, 0.095), (-0.095, 0.060, 0.035, 0.035)], ymin=(0.005, 0.015),
                  pivot=(-0.040, 0.100), tip=(-0.100, 0.150)),
        hands={"L": (0.090, 0.115, 0.040, 0.050), "R": (-0.048, 0.112, 0.030, 0.045)}, hand_in={"L": 0.050, "R": -0.022},
        shoulder={"L": (0.055, 0.150), "R": (-0.022, 0.150)},
        feet=dict(z=(0.070, 0.084), split=0.016, gap=(0.008, 0.018)),
        eyes={"L": (0.055, 0.232), "R": (-0.001, 0.232)}, eye_r=(0.0155, 0.0155),
        mouth=(0.024, 0.207, 0.012, 0.005), front="auto", top="auto", lid=1.15),
    "fuegito3": dict(
        smooth=12,
        head=(0.188, 0.200),
        tail=dict(ell=[(-0.110, 0.200, 0.050, 0.110), (-0.100, 0.080, 0.045, 0.060)], ymin=(0.005, 0.015),
                  pivot=(-0.040, 0.110), tip=(-0.110, 0.180)),
        hands={"L": (0.120, 0.120, 0.035, 0.050), "R": (-0.052, 0.118, 0.030, 0.050)}, hand_in={"L": 0.085, "R": -0.034},
        hand_ymax={"L": (0.042, 0.045), "R": (0.040, 0.050)}, arm_amp=0.75,
        shoulder={"L": (0.085, 0.160), "R": (-0.028, 0.160)},
        feet=dict(z=(0.070, 0.084), split=0.019, gap=(0.008, 0.018)),
        eyes={"L": (0.081, 0.236), "R": (0.019, 0.237)}, eye_r=(0.015, 0.016),
        mouth=(0.055, 0.211, 0.012, 0.005), front="auto", top="auto", lid=1.15),
    "hielo3": dict(
        smooth=12,
        head=(0.186, 0.198),
        hands={"L": (0.085, 0.135, 0.040, 0.050), "R": (-0.080, 0.130, 0.045, 0.055)}, hand_in={"L": 0.045, "R": -0.040},
        hand_z=(0.180, 0.192), hand_ymax={"L": (0.015, 0.025), "R": (0.008, 0.018)}, arm_amp=0.6,
        shoulder={"L": (0.045, 0.172), "R": (-0.040, 0.172)},
        feet=dict(z=(0.075, 0.090), split=0.0, gap=(0.010, 0.022), xout=(0.092, 0.100), first=True),
        tail=dict(ell=(-0.112, 0.065, 0.035, 0.045), ymin=(0.010, 0.025), pivot=(-0.070, 0.070), tip=(-0.115, 0.050)),
        eyes={"L": (0.054, 0.240), "R": (-0.015, 0.241)}, eye_r=(0.0155, 0.017),
        mouth=(0.022, 0.215, 0.012, 0.005), front="auto", top="auto", lid=1.15),
    "planta3": dict(
        smooth=12,
        head=(0.170, 0.183),
        hands={"L": (0.110, 0.150, 0.055, 0.110), "R": (-0.110, 0.150, 0.055, 0.110)}, hand_in={"L": 0.050, "R": -0.050},
        hand_z=(0.235, 0.250),
        shoulder={"L": (0.066, 0.200), "R": (-0.066, 0.200)},
        feet=dict(z=(0.078, 0.092), split=-0.004, gap=(0.006, 0.016), xout=(0.110, 0.118), first=True),
        eyes={"L": (0.026, 0.217), "R": (-0.033, 0.219)}, eye_r=(0.0155, 0.015),
        mouth=(-0.001, 0.194, 0.012, 0.005), front="auto", lid=1.1),
    "robot3": dict(
        smooth=12,
        head=(0.196, 0.206),
        hands={"L": [(0.100, 0.230, 0.050, 0.080), (0.105, 0.120, 0.040, 0.060)],
               "R": [(-0.105, 0.230, 0.045, 0.075), (-0.110, 0.120, 0.040, 0.060)]},
        hand_in={"L": 0.050, "R": -0.050},
        shoulder={"L": (0.050, 0.200), "R": (-0.050, 0.200)},
        feet=dict(z=(0.115, 0.128), split=0.0, gap=(0.006, 0.016), xout=(0.098, 0.106), first=True),
        eyes={"L": (0.033, 0.246), "R": (-0.038, 0.246)}, eye_r=(0.011, 0.017),
        mouth=None, front="auto", lid=1.1),
}

TAIL_N = 3   # huesos de la cola

def ss(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def override(sc):
    # activa sc en la ventana (también existe una en blender -b) y devuelve un override para ops
    w = bpy.context.window_manager.windows[0]; w.scene = sc
    return bpy.context.temp_override(window=w, scene=sc, view_layer=sc.view_layers[0])

# ---------------------------------------------------------------- import
def import_pet(pet, evo):
    name = f"{pet.capitalize()}_Rig"
    old = bpy.data.scenes.get(name)
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.scenes.remove(old)
    sc = bpy.data.scenes.new(name)
    with override(sc):
        bpy.ops.import_scene.gltf(filepath=os.path.join(BASE, pet, f"evo{evo}.glb"))
    meshes = [o for o in sc.objects if o.type == 'MESH']
    assert len(meshes) == 1, meshes
    ob = meshes[0]; ob.name = f"{pet}_evo{evo}"; ob.data.name = ob.name
    sc.render.fps = 24
    return sc, ob

# ---------------------------------------------------------------- armature + pesos
def region(x, z, ells):
    # unión suave de elipses frontales (cx, cz, rx, rz); acepta una sola tupla
    if isinstance(ells[0], (int, float)): ells = [ells]
    w = np.zeros_like(x)
    for cx, cz, rx, rz in ells:
        d = np.sqrt(((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2)
        w = np.maximum(w, 1 - ss(1.0, 1.3, d))
    return w

def welded_graph(me, co):
    # vértices soldados por posición (los GLB parten la malla en las costuras UV) + aristas soldadas
    _, wid = np.unique(np.round(co / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    wid = wid.ravel()
    e = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get("vertices", e)
    return wid, wid[e.reshape(-1, 2)], int(wid.max()) + 1

def main_component(w, graph, keep_frac=0.5):
    # deja solo las componentes conexas grandes de la zona w>0.05 (quita trozos sueltos que caen dentro
    # de la elipse en proyección pero pertenecen a otra parte, p.ej. el muslo detrás de un puño)
    wid, we, nw = graph
    m = np.zeros(nw, bool); np.logical_or.at(m, wid, w > 0.05)
    ee = we[m[we[:, 0]] & m[we[:, 1]]]
    lab = np.arange(nw)
    while True:
        mn = np.minimum(lab[ee[:, 0]], lab[ee[:, 1]]); new = lab.copy()
        np.minimum.at(new, ee[:, 0], mn); np.minimum.at(new, ee[:, 1], mn); new = new[new]
        if np.array_equal(new, lab): break
        lab = new
    ids, cnt = np.unique(lab[m], return_counts=True)
    if not len(cnt): return w
    keep = np.isin(lab, ids[cnt >= keep_frac * cnt.max()]) & m
    return w * keep[wid]

def rig(pet, sc, ob, C):
    me = ob.data
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    x, y, z = co[:, 0], co[:, 1], co[:, 2]; ax = np.abs(x)
    H = float(z.max())
    # pesos crudos de cada parte; se reparten por prioridad: tail > manos > pies > top > head > body
    raw = {}
    F = C["feet"]; sp = F["split"]
    feet = (1 - ss(*F["z"], z)) * ss(*F["gap"], np.abs(x - sp))
    if F.get("xout"): feet = feet * (1 - ss(*F["xout"], np.abs(x - sp)))
    if F.get("first"):   # piernas antes que manos (puños que bajan junto a las piernas)
        raw["foot.L"] = feet * (x > sp); raw["foot.R"] = feet * (x <= sp)
    T = C.get("tail")
    if T:
        raw["tail"] = region(x, z, T["ell"]) * (ss(*T["ymin"], y) if T.get("ymin") else 1)
    for s, k in (("L", 1), ("R", -1)):
        if s not in C.get("hands", {}): continue
        hin = C["hand_in"]
        side = ss(0, 0.008, (x - hin[s]) * k) if isinstance(hin, dict) else ss(*hin, ax) * ((x * k) > 0)
        raw[f"hand.{s}"] = region(x, z, C["hands"][s]) * side
        if C.get("hand_exclude"):
            ex = region(x, z, C["hand_exclude"])
            if C.get("hand_exclude_y"): ex = ex * ss(*C["hand_exclude_y"], y)
            raw[f"hand.{s}"] *= 1 - ex
        if C.get("hand_z"): raw[f"hand.{s}"] *= 1 - ss(*C["hand_z"], z)
        if C.get("hand_ymax"):
            hy = C["hand_ymax"][s] if isinstance(C["hand_ymax"], dict) else C["hand_ymax"]
            raw[f"hand.{s}"] *= 1 - ss(*hy, y)
    if not F.get("first"):
        raw["foot.L"] = feet * (x > sp); raw["foot.R"] = feet * (x <= sp)
    top = C.get("top")
    if top == "auto":
        ez = float(np.mean([e[1] for e in C["eyes"].values()])); a = ez + 0.55 * (H - ez); top = (a, a + 0.012)
    if top: raw["top"] = ss(*top, z)
    if C.get("head"): raw["head"] = ss(*C["head"], z)
    if C.get("head"):   # solo en bípedos (evo0 se dejó como estaba)
        graph = welded_graph(me, co)
        for n in raw:
            if n != "head": raw[n] = main_component(raw[n], graph)
    groups = {}; remaining = np.ones_like(x)
    for n, w in raw.items():
        groups[n] = w * remaining; remaining = remaining - groups[n]
    groups = {"body": np.clip(remaining, 0, 1), **groups}
    if C.get("smooth"):   # difumina los bordes entre grupos (evita bandas estiradas en modelos grandes)
        wid, we, nw = graph if C.get("head") else welded_graph(me, co)
        ee = we[we[:, 0] != we[:, 1]]; deg = np.bincount(ee.ravel(), minlength=nw).astype(float)
        cnt = np.bincount(wid, minlength=nw).astype(float)
        for n in groups:
            w = np.bincount(wid, groups[n], minlength=nw) / cnt
            for _ in range(C["smooth"]):
                acc = np.zeros(nw); np.add.at(acc, ee[:, 0], w[ee[:, 1]]); np.add.at(acc, ee[:, 1], w[ee[:, 0]])
                w = np.where(deg > 0, 0.5 * w + 0.5 * acc / np.maximum(deg, 1), w)
            groups[n] = w[wid]
        tot = sum(groups.values()); groups = {n: w / tot for n, w in groups.items()}

    def centroid(w):
        m = w > 0.5; return co[m].mean(0) if m.any() else co[w > 0.01].mean(0)

    chain = None
    if T:   # cola en cadena de TAIL_N huesos: t = avance a lo largo de pivot->tip (plano xz)
        wt = groups["tail"]; m = wt > 0.5
        p0 = np.array(T["pivot"], float); u = np.array(T["tip"], float) - p0; u /= np.linalg.norm(u)
        t = (co[:, [0, 2]] - p0) @ u
        t0, tmax = (float(v) for v in np.percentile(t[m], [3, 97]))   # tramo real de la cola (puede empezar lejos del pivote)
        sk = np.clip((t - t0) / (tmax - t0), 0, 1) * TAIL_N - 0.5        # coordenada de hueso; reparto lineal entre vecinos
        names = ["tail"] + [f"tail{k + 1}" for k in range(1, TAIL_N)]
        tail_w = {n: wt * np.clip(1 - np.abs(np.clip(sk, 0, TAIL_N - 1) - k), 0, 1) for k, n in enumerate(names)}
        groups = {n: w for n, w in groups.items() if n != "tail"} | tail_w
        yc = float(np.median(y[m])); chain = []
        for k in range(TAIL_N + 1):   # articulaciones = centro de los vértices de la cola a esa altura de t
            tb = t0 + (tmax - t0) * k / TAIL_N; near = m & (np.abs(t - tb) < (tmax - t0) / (2 * TAIL_N))
            if k == 0 or not near.any(): pt = (p0[0] + u[0] * tb, yc, p0[1] + u[1] * tb)
            else: c = co[near].mean(0); pt = (float(c[0]), yc, float(c[2]))
            chain.append(pt)

    arm = bpy.data.armatures.new(f"{pet.capitalize()}_Armature"); arm.display_type = 'STICK'
    ao = bpy.data.objects.new(f"{pet.capitalize()}_Rig", arm); sc.collection.objects.link(ao); ao.show_in_front = True
    with override(sc):
        sc.view_layers[0].objects.active = ao
        bpy.ops.object.mode_set(mode='EDIT')
        eb = arm.edit_bones
        def bone(n, h, t, parent=None, deform=True):
            b = eb.new(n); b.head = h; b.tail = t; b.roll = 0
            if parent: b.parent = eb[parent]
            b.use_deform = deform; return b
        cy = float(np.median(y))
        bone("root", (0, 0, 0), (0, 0.04, 0), deform=False)
        if C.get("head"):   # bípedo: body de cadera a cuello, head de cuello hacia arriba
            h0 = C["head"][0]
            bone("body", (0, cy, F["z"][1]), (0, cy, h0), "root")
            hc = centroid(groups["head"])
            bone("head", (hc[0], cy, h0), (hc[0], cy, h0 + 0.6 * (H - h0)), "body")
        else:
            bone("body", (0, cy, 0.03), (0, cy, min(0.17, H * 0.8)), "root")
        for s, k in (("L", 1), ("R", -1)):
            if f"hand.{s}" in groups:
                c = centroid(groups[f"hand.{s}"])
                if C.get("shoulder"):   # hombro explícito (x, z): pivote del brazo
                    sx, sz = C["shoulder"][s]
                    bone(f"hand.{s}", (sx, c[1], sz), (sx + 0.036 * k, c[1], sz), "body")
                else:
                    hin = C["hand_in"][0] + 0.004
                    bone(f"hand.{s}", (hin * k, c[1], c[2]), ((hin + 0.036) * k, c[1], c[2]), "body")
            c = centroid(groups[f"foot.{s}"]); ft = F["z"][1] + 0.002
            bone(f"foot.{s}", (c[0], c[1], ft), (c[0], c[1], 0.002), "root")
        if "top" in groups:
            c = centroid(groups["top"])
            bone("top", (c[0], c[1], top[0]), (c[0], c[1], top[0] + 0.04), "head" if "head" in groups else "body")
        if chain:
            parent = "body"
            for k, n in enumerate(["tail"] + [f"tail{k + 1}" for k in range(1, TAIL_N)]):
                bone(n, chain[k], chain[k + 1], parent); parent = n
        bpy.ops.object.mode_set(mode='OBJECT')

    for n, w in groups.items():
        vg = ob.vertex_groups.new(name=n)
        for val in np.unique(np.round(w, 3)):
            if val <= 0.001: continue
            idx = np.nonzero(np.round(w, 3) == val)[0].tolist()
            vg.add(idx, float(val), 'REPLACE')
    ob.parent = ao
    mod = ob.modifiers.new("Armature", 'ARMATURE'); mod.object = ao
    tot = sum(groups.values())
    print(pet, "weights min/max", round(float(tot.min()), 3), round(float(tot.max()), 3),
          {n: int((w > 0.5).sum()) for n, w in groups.items()})
    return ao

# ---------------------------------------------------------------- shape keys
def shape_keys(ob, C):
    me = ob.data
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    EYES = C["eyes"]; ERX, ERZ = C["eye_r"]; LID = C.get("lid", 1.45)
    if C.get("front") == "auto":
        # capa más frontal: y respecto al mínimo y de su celda xz (3 mm, dilatado 1 celda)
        cell = 0.003; ix = ((x - x.min()) / cell).astype(int); iz = ((z - z.min()) / cell).astype(int)
        g = np.full((ix.max() + 3, iz.max() + 3), 9.0); np.minimum.at(g, (ix + 1, iz + 1), y)
        gd = g.copy()
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1): gd[1:-1, 1:-1] = np.minimum(gd[1:-1, 1:-1], g[1 + dx:g.shape[0] - 1 + dx, 1 + dz:g.shape[1] - 1 + dz])
        front = 1 - ss(0.004, 0.010, y - gd[ix + 1, iz + 1])
    else:
        front = 1 - ss(*C["front"], y)
    def ell(c, rx, rz): return np.sqrt(((x - c[0]) / rx) ** 2 + ((z - c[1]) / rz) ** 2)
    def fall(r, r0, r1): return (1 - ss(r0, r1, r)) * front
    Z = np.zeros_like(x); ONE = np.ones_like(x)
    if C["mouth"]:
        MC = C["mouth"][:2]; MRX, MRZ = C["mouth"][2:]
        MOUTH_MASK = ss(1.15, 2.0, ell(MC, MRX, MRZ))
        EYE_MASK = ONE.copy()
        for c in EYES.values(): EYE_MASK = np.minimum(EYE_MASK, ss(1.0, 1.35, ell(c, ERX, ERZ)))
    else:
        MOUTH_MASK = ONE
    def add(name, dx, dz):
        k = ob.shape_key_add(name=name, from_mix=False)
        new = co.copy(); new[:, 0] += dx; new[:, 2] += dz
        k.data.foreach_set("co", new.ravel()); return k
    ob.shape_key_add(name="Basis")
    def eye_ops(fn, sides=None):
        dx = Z.copy(); dz = Z.copy()
        for s in (sides or EYES.keys()):
            c = EYES[s]; a, b = fn(s, c, ell(c, ERX, ERZ)); dx += a; dz += b
        return dx, dz
    def blink(s, c, r):
        line = c[1] - 0.45 * ERZ; f = np.where(z < line, fall(r, 1.0, 1.18), fall(r, 1.02, LID)) * MOUTH_MASK
        return Z, (line - z) * 0.92 * f
    if "L" in EYES:
        for s in ("L", "R"): add(f"blink_{s}", *eye_ops(blink, (s,)))
    add("blink", *eye_ops(blink))
    def happy(s, c, r):
        u = np.clip((x - c[0]) / ERX, -1.2, 1.2)
        line = c[1] - 0.15 * ERZ + 0.45 * ERZ * (1 - u * u)
        f = np.where(z < line, fall(r, 1.0, 1.2), fall(r, 1.02, LID + 0.05)) * MOUTH_MASK
        return Z, (line + (z - c[1]) * 0.22 - z) * f
    add("eyes_happy", *eye_ops(happy))
    def wide(s, c, r):
        f = 0.22 * (1 - ss(1.0, 1.6, r)) * front * MOUTH_MASK
        return (x - c[0]) * f, (z - c[1]) * f
    add("eyes_wide", *eye_ops(wide))
    def tilt(ang, squash):
        def fn(s, c, r):
            sgn = {"R": 1, "L": -1, "C": 0}[s]
            a = R(ang) * sgn; ca, sa = math.cos(a), math.sin(a); px, pz = x - c[0], z - c[1]
            rx_ = ca * px - sa * pz; rz_ = sa * px + ca * pz
            rz_ = np.where(pz > 0, rz_ * squash, rz_)
            f = fall(r, 1.0, 1.5) * MOUTH_MASK
            return (rx_ - px) * f, (rz_ - pz) * f
        return fn
    add("eyes_sad", *eye_ops(tilt(16, 0.8)))
    add("eyes_angry", *eye_ops(tilt(-18, 0.72)))
    for n, (ddx, ddz) in {"look_left": (0.3 * ERX, 0), "look_right": (-0.3 * ERX, 0),
                          "look_up": (0, 0.22 * ERZ), "look_down": (0, -0.22 * ERZ)}.items():
        def lk(s, c, r, ddx=ddx, ddz=ddz):
            f = fall(r, 1.0, 1.6) * MOUTH_MASK; return ddx * f, ddz * f
        add(n, *eye_ops(lk))
    if C["mouth"]:
        rm = ell(MC, MRX, MRZ); pxm, pzm = x - MC[0], z - MC[1]
        f = fall(rm, 1.0, 2.0) * EYE_MASK
        add("mouth_open", pxm * 0.15 * f, (pzm - MRZ) * 0.9 * f)
        u = np.clip(pxm / MRX, -1.5, 1.5)
        add("mouth_smile", pxm * 0.4 * f, (0.45 * MRZ * u * u - 0.25 * MRZ) * f)
        add("mouth_sad", pxm * 0.1 * f, (-0.5 * MRZ * u * u + 0.25 * MRZ) * f)
        add("mouth_o", -pxm * 0.3 * f, pzm * 0.45 * f)
    for k in me.shape_keys.key_blocks[1:]: k.value = 0.0
    print("keys", [k.name for k in me.shape_keys.key_blocks])

# ---------------------------------------------------------------- animaciones (mismos ejes que Acero)
# hand.X local = sube la mano | hand.Z local = adelante/atrás | body.Z = balanceo lateral
# foot.X = punta adelante/atrás, foot loc Y(-) = levantar | top/head.X = cabeceo, .Z = lateral | tail.Z = menear
def animate(pet, rig_ob, arm_amp=1.0):
    ad = rig_ob.animation_data_create()
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    for a in list(bpy.data.actions):
        if a.name.startswith(pet + "_"): bpy.data.actions.remove(a)
    pb = rig_ob.pose.bones
    has_top = "top" in pb
    for b in pb: b.rotation_mode = 'XYZ'
    def reset():
        for b in pb: b.location = (0, 0, 0); b.rotation_euler = (0, 0, 0); b.scale = (1, 1, 1)
    def key(f, **bones):
        reset()
        for n, d in bones.items():
            if n not in pb: continue
            b = pb[n]
            amp = arm_amp if n.startswith("hand.") else 1.0
            if 'rot' in d: b.rotation_euler = [R(v * amp) for v in d['rot']]
            if 'loc' in d: b.location = d['loc']
            if 'scl' in d: b.scale = d['scl']
        for b in pb:
            b.keyframe_insert("location", frame=f); b.keyframe_insert("rotation_euler", frame=f); b.keyframe_insert("scale", frame=f)
    # Inercia: head/top/tail llegan LAG fotogramas tarde (la cola más). En clips cíclicos todas las curvas llevan
    # modificador Cycles (el bucle no salta y el retraso "da la vuelta"); en los demás el clip se alarga para
    # que la cola termine su movimiento.
    LAG = {"head": 2, "top": 3, **{n: 3 + 2 * k for k, n in enumerate(["tail"] + [f"tail{k + 1}" for k in range(1, TAIL_N)])}}
    def fcurves(act):
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags: yield from cb.fcurves
    def make(name, frames, cyclic=False, lag=None):   # lag: retrasos extra por hueso en este clip
        lags = {**LAG, **(lag or {})}
        act = bpy.data.actions.new(f"{pet}_{name}"); act.use_fake_user = True
        ad.action = act
        for f, bones in frames: key(f, **bones)
        end = frames[-1][0]; tail_end = end
        for fc in fcurves(act):
            bone = fc.data_path.split('"')[1] if fc.data_path.startswith("pose.bones") else ""
            lag = lags.get(bone, 0)
            if lag:
                for kp in fc.keyframe_points:
                    kp.co.x += lag; kp.handle_left.x += lag; kp.handle_right.x += lag
                if not cyclic: tail_end = max(tail_end, end + lag)
            if cyclic: fc.modifiers.new('CYCLES')
        ad.action = None
        tr = ad.nla_tracks.new(); tr.name = name
        st = tr.strips.new(name, 1, act); st.action_frame_end = tail_end; tr.mute = True
    # top/head/tail siguen el mismo "ritmo" secundario: rx = cabeceo, rz = lateral (la cola lo amplifica)
    tails = ["tail"] + [f"tail{k + 1}" for k in range(1, TAIL_N)]
    T = lambda rx, rz=0: {"top": dict(rot=(rx, 0, rz)), "head": dict(rot=(rx * 0.5, 0, rz * 0.6)),
                          **{n: dict(rot=(rx * 1.35 / TAIL_N, 0, rz * 2.7 / TAIL_N)) for n in tails}}
    def breath(f, inhale, sway):
        b = 0.03 * inhale
        return (f, dict(body=dict(scl=(1 + b, 1 - 1.3 * b, 1 + b), rot=(0, 0, sway)),
                        **{"hand.L": dict(rot=(5 - 8 * inhale, 0, 0)), "hand.R": dict(rot=(5 - 8 * inhale, 0, 0))},
                        **T(-6 * inhale, 4 - 3 * sway)))
    make("idle", [breath(1, 0, 2), breath(25, 1, 0), breath(49, 0, -2), breath(73, 1, 0), breath(97, 0, 2)], cyclic=True, lag={"hand.L": 3, "hand.R": 3})
    def walk(phase):   # contacto: pies abiertos en el suelo, cuerpo en lo más bajo
        s = 1 if phase == 0 else -1
        return dict(body=dict(rot=(0, -5 * s, 6 * s), loc=(0, 0.0, 0), scl=(1.02, 0.97, 1.02)),
                    **{"foot.L": dict(rot=(25 * s, 0, 0)), "foot.R": dict(rot=(-25 * s, 0, 0)),
                       "hand.L": dict(rot=(10, 0, -25 * s)), "hand.R": dict(rot=(10, 0, -25 * s))}, **T(5, -8 * s))
    def passing(s):    # paso: el pie que va hacia delante pasa levantado, cuerpo en lo más alto
        # en el contacto previo el pie atrasado es L si s > 0 (medido: foot.L +25 = pie atrás)
        lift = {("foot.L" if s > 0 else "foot.R"): dict(rot=(0, 0, 0), loc=(0, -0.014, 0))}
        return dict(body=dict(rot=(0, 0, 2 * s), loc=(0, 0.010, 0), scl=(0.99, 1.02, 0.99)),
                    **{"hand.L": dict(rot=(10, 0, 0)), "hand.R": dict(rot=(10, 0, 0))}, **lift, **T(-3, -2 * s))
    make("walk", [(1, walk(0)), (7, passing(1)), (13, walk(1)), (19, passing(-1)), (25, walk(0))], cyclic=True, lag={"hand.L": 2, "hand.R": 2})
    wave_up = lambda a, t: dict(body=dict(rot=(0, 0, -6)), **{"hand.L": dict(rot=(a, 0, 0)), "hand.R": dict(rot=(5, 0, 0))}, **T(0, t))
    make("wave", [(1, dict()), (6, wave_up(55, -6)), (10, wave_up(35, 4)), (14, wave_up(58, -6)), (18, wave_up(35, 4)),
                  (22, wave_up(58, -6)), (26, wave_up(35, 4)), (32, dict())])
    make("jump", [
        (1, dict()),
        (6, dict(body=dict(scl=(1.12, 0.8, 1.12)), **{"hand.L": dict(rot=(-15, 0, 0)), "hand.R": dict(rot=(-15, 0, 0))}, **T(10))),
        (11, dict(root=dict(loc=(0, 0, 0.06)), body=dict(scl=(0.92, 1.15, 0.92)),
                  **{"hand.L": dict(rot=(55, 0, 0)), "hand.R": dict(rot=(55, 0, 0)), "foot.L": dict(rot=(-15, 0, 0)), "foot.R": dict(rot=(-15, 0, 0))}, **T(-14))),
        (16, dict(root=dict(loc=(0, 0, 0.07)), **{"hand.L": dict(rot=(45, 0, 0)), "hand.R": dict(rot=(45, 0, 0))}, **T(-6))),
        (21, dict(root=dict(loc=(0, 0, 0)), body=dict(scl=(1.1, 0.85, 1.1)), **T(14))),
        (26, dict()),
    ])
    # FWD: signo de body.X que inclina hacia delante (-Y); PUNCH: signo de hand.Z que lleva la mano hacia delante
    FWD, PUNCH = 1, -1
    # lean: inclinación adelante (+) / atrás (-); side = lateral; twist = giro del torso (- adelanta el hombro L)
    lean = lambda a, **kw: dict(rot=(FWD * a, kw.get("twist", 0), kw.get("side", 0)), **({"scl": kw["scl"]} if "scl" in kw else {}))
    hands = lambda l, r=None: {"hand.L": dict(rot=l), "hand.R": dict(rot=r or l)}
    make("attack", [
        (1, dict()),
        (7, dict(root=dict(loc=(0, 0.010, 0)), body=lean(-10, twist=12, scl=(1.04, 0.94, 1.04)),
                 **hands((25, 0, -PUNCH * 35), (10, 0, PUNCH * 15)), **T(-6))),
        (11, dict(root=dict(loc=(0, -0.022, 0)), body=lean(14, twist=-16, scl=(0.97, 1.04, 0.97)),
                  **hands((45, 0, PUNCH * 55), (5, 0, -PUNCH * 20)), **T(10))),
        (15, dict(root=dict(loc=(0, -0.020, 0)), body=lean(12, twist=-14), **hands((42, 0, PUNCH * 50), (5, 0, -PUNCH * 18)), **T(8))),
        (24, dict()),
    ])
    make("hurt", [
        (1, dict()),
        (4, dict(root=dict(loc=(0, 0.020, 0)), body=lean(-14, scl=(1.05, 0.92, 1.05)), **hands((30, 0, 0)), **T(-12, 10))),
        (8, dict(root=dict(loc=(0, 0.016, 0)), body=lean(-6, side=-5), **hands((15, 0, 0)), **T(-4, -8))),
        (13, dict(root=dict(loc=(0, 0.008, 0)), body=lean(-2, side=3), **T(0, 4))),
        (20, dict()),
    ])
    hop = lambda z, a, h, s=1.0: dict(root=dict(loc=(0, 0, z)), body=dict(scl=(1 / s ** 0.5, s, 1 / s ** 0.5)),
                                      **hands((a, 0, 0)), **T(h, 0))
    make("celebrate", [
        (1, dict()),
        (5, hop(0, -10, 8, 0.88)),
        (10, dict(hop(0.04, 62, -10, 1.08), **{"foot.L": dict(rot=(-15, 0, 0)), "foot.R": dict(rot=(-15, 0, 0))})),
        (15, hop(0, 50, 6, 0.9)),
        (20, dict(hop(0.04, 65, -10, 1.08), **{"foot.L": dict(rot=(-15, 0, 0)), "foot.R": dict(rot=(-15, 0, 0))})),
        (25, hop(0, 50, 6, 0.9)),
        (30, dict(body=dict(rot=(0, 0, 8)), **hands((58, 0, 0)), **T(-4, 10))),
        (36, dict()),
    ])
    nap = lambda b: dict(body=lean(7, scl=(1 + 0.03 * b, 1 - 0.03 * b, 1 + 0.03 * b)), **hands((-8 + 3 * b, 0, 0)), **T(16 - 4 * b, 3))
    make("sleep", [(1, nap(0)), (36, nap(1)), (72, nap(0))], cyclic=True)
    # correr (16 f): inclinado, zancada larga, brazos doblados y fase en el aire en el paso
    def stride(phase):
        s = 1 if phase == 0 else -1
        return dict(body=lean(10, twist=-8 * s, side=5 * s, scl=(1.04, 0.94, 1.04)),
                    **{"foot.L": dict(rot=(38 * s, 0, 0)), "foot.R": dict(rot=(-38 * s, 0, 0)),
                       "hand.L": dict(rot=(25, 0, -40 * s)), "hand.R": dict(rot=(25, 0, -40 * s))}, **T(8, -6 * s))
    def flight(s):
        return dict(root=dict(loc=(0, 0, 0.012)), body=lean(10, side=2 * s, scl=(0.98, 1.04, 0.98)),
                    **{("foot.L" if s > 0 else "foot.R"): dict(rot=(-10 * s, 0, 0), loc=(0, -0.020, 0)),
                       "hand.L": dict(rot=(25, 0, 0)), "hand.R": dict(rot=(25, 0, 0))}, **T(2, -2 * s))
    make("run", [(1, stride(0)), (5, flight(1)), (9, stride(1)), (13, flight(-1)), (17, stride(0))], cyclic=True, lag={"hand.L": 1, "hand.R": 1})
    # desmayo: tambaleo y caída de espaldas girando todo sobre los pies (root.X - = hacia atrás); el pivote sube
    # BACK para que la espalda no atraviese el suelo. Termina tumbado (el visor lo reproduce una vez y se queda).
    BACK = float(np.percentile([v.co.y for v in rig_ob.children[0].data.vertices], 98)) + 0.014 if rig_ob.children else 0.065
    down = lambda a, z: dict(root=dict(rot=(a, 0, 0), loc=(0, 0, z)))
    make("faint", [
        (1, dict()),
        (6, dict(body=lean(-8, side=6), **hands((20, 0, 0)), **T(-10, 10))),
        (12, dict(body=lean(4, side=-8, scl=(1.03, 0.95, 1.03)), **hands((10, 0, 0)), **T(8, -12))),
        (18, dict(body=lean(-2, side=6), **hands((25, 0, 0)), **T(-6, 10))),
        (24, dict(down(-18, 0.016), body=lean(-6, scl=(1.05, 0.93, 1.05)), **hands((45, 0, 0)), **T(-14))),
        (30, dict(down(-84, BACK), body=dict(scl=(1.06, 0.92, 1.06)), **hands((30, 0, 0)), **T(12, 8),
                  **{"foot.L": dict(rot=(20, 0, 0)), "foot.R": dict(rot=(20, 0, 0))})),
        (34, dict(down(-76, BACK + 0.006), **hands((40, 0, 0)), **T(4, 10),
                  **{"foot.L": dict(rot=(30, 0, 0)), "foot.R": dict(rot=(25, 0, 0))})),
        (38, dict(down(-82, BACK), **hands((-10, 0, 0)), **T(14, 16), **{"foot.L": dict(rot=(15, 0, 0)), "foot.R": dict(rot=(15, 0, 0))})),
        (44, dict(down(-82, BACK), **hands((-12, 0, 0)), **T(16, 18), **{"foot.L": dict(rot=(15, 0, 0)), "foot.R": dict(rot=(15, 0, 0))})),
    ])
    # levantarse: empieza en la última pose del desmayo y se incorpora (se pueden encadenar)
    lying = lambda: dict(down(-82, BACK), **hands((-12, 0, 0)), **T(16, 18), **{"foot.L": dict(rot=(15, 0, 0)), "foot.R": dict(rot=(15, 0, 0))})
    make("getup", [
        (1, lying()),
        (8, dict(down(-80, BACK + 0.012), **hands((20, 0, 0)), **T(6, 0), **{"foot.L": dict(rot=(25, 0, 0)), "foot.R": dict(rot=(25, 0, 0))})),
        (16, dict(down(-40, BACK * 0.6), body=lean(20), **hands((30, 0, PUNCH * 30), (30, 0, -PUNCH * 30)), **T(10))),
        (24, dict(down(-10, 0.01), body=lean(12, scl=(1.06, 0.9, 1.06)), **hands((10, 0, 0)), **T(6))),
        (30, dict(body=lean(-3, scl=(0.97, 1.04, 0.97)), **T(-6))),
        (33, dict(**T(0, 10))),
        (36, dict(**T(0, -8))),
        (40, dict()),
    ])
    # ataque especial: carga con los dos brazos atrás y lanza con los dos hacia delante (manos espejadas: L +, R -)
    both = lambda a, z: hands((a, 0, PUNCH * z), (a, 0, -PUNCH * z))
    make("special", [
        (1, dict()),
        (8, dict(root=dict(loc=(0, 0.008, 0)), body=lean(-10, scl=(1.05, 0.92, 1.05)), **both(35, -40), **T(-8))),
        (10, dict(root=dict(loc=(0, 0.008, 0)), body=lean(-10, side=3, scl=(1.05, 0.92, 1.05)), **both(38, -42), **T(-8, 4))),
        (12, dict(root=dict(loc=(0, 0.008, 0)), body=lean(-11, side=-3, scl=(1.06, 0.91, 1.06)), **both(36, -44), **T(-9, -4))),
        (15, dict(root=dict(loc=(0, -0.018, 0)), body=lean(12, scl=(0.96, 1.05, 0.96)), **both(40, 60), **T(8))),
        (21, dict(root=dict(loc=(0, -0.012, 0)), body=lean(8), **both(36, 52), **T(5))),
        (32, dict()),
    ])
    # esquivar: salto lateral a la izquierda del personaje (+X) y vuelta al sitio
    side_hop = lambda x, z, sd, sq=1.0: dict(root=dict(loc=(x, 0, z)), body=lean(0, side=sd, scl=(1 / sq ** 0.5, sq, 1 / sq ** 0.5)))
    make("dodge", [
        (1, dict()),
        (4, dict(side_hop(0, 0, -6, 0.88), **hands((-10, 0, 0)), **T(6, 6))),
        (8, dict(side_hop(0.05, 0.025, 12, 1.05), **hands((35, 0, 0)), **T(-6, -12),
                 **{"foot.L": dict(rot=(-15, 0, 0)), "foot.R": dict(rot=(-15, 0, 0))})),
        (11, dict(side_hop(0.055, 0, 4, 0.9), **hands((15, 0, 0)), **T(6, 8))),
        (16, dict(side_hop(0.025, 0.018, -10, 1.04), **hands((30, 0, 0)), **T(-4, 10))),
        (20, dict(side_hop(0, 0, -3, 0.92), **T(4, -4))),
        (26, dict()),
    ])
    # defenderse: se encoge y se cubre con los brazos delante; encaja un golpe y baja la guardia
    guard = lambda dy=0, sh=0: dict(root=dict(loc=(0, dy, 0)), body=lean(6, side=sh, scl=(1.04, 0.93, 1.04)), **both(50, 45), **T(10))
    make("block", [(1, dict()), (5, guard()), (8, guard(0.007, 3)), (11, guard(0.002, -2)), (18, guard()), (24, dict())])
    # mirar alrededor (reposo alternativo): gira torso y cabeza a un lado y al otro
    look = lambda tw, hd, b=0: dict(body=dict(rot=(0, tw, 0), scl=(1 + 0.02 * b, 1 - 0.025 * b, 1 + 0.02 * b)),
                                    **hands((5 - 4 * b, 0, 0)), **{**T(-3 * b, -tw * 0.4), "head": dict(rot=(-2 * b, hd, 0))})
    make("look", [(1, look(0, 0)), (12, look(-10, -25, 1)), (24, look(-10, -25)), (32, look(0, 0, 1)),
                  (44, look(10, 25)), (56, look(10, 25, 1)), (64, look(0, 0)), (73, look(0, 0))], cyclic=True)
    reset()
    print("clips", [(t.name, t.strips[0].frame_end) for t in ad.nla_tracks], "top" if has_top else "")

# ---------------------------------------------------------------- exportar
def export(pet, evo, sc, rig_ob, ob):
    D = os.path.join(BASE, pet)
    rig_ob.animation_data.action = None; sc.frame_set(1)
    for b in rig_ob.pose.bones: b.location = (0, 0, 0); b.rotation_euler = (0, 0, 0); b.scale = (1, 1, 1)
    # sin temp_override: el exportador glTF evalúa el depsgraph y crashea con view_layer sobreescrito
    override(sc)
    for o in sc.view_layers[0].objects: o.select_set(False)
    rig_ob.select_set(True); ob.select_set(True); sc.view_layers[0].objects.active = rig_ob
    for t in rig_ob.animation_data.nla_tracks: t.mute = False
    out = os.path.join(D, f"evo{evo}_rig.glb")
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB',
        export_animations=True, export_animation_mode='NLA_TRACKS', export_morph=True,
        export_skins=True, export_force_sampling=True, export_yup=True, use_active_scene=True)
    for t in rig_ob.animation_data.nla_tracks: t.mute = True
    blend = os.path.join(D, f"{pet}_rig.blend" if evo == 0 else f"{pet}_evo{evo}_rig.blend")
    bpy.data.libraries.write(blend, {sc, rig_ob, ob, *[a for a in bpy.data.actions if a.name.startswith(pet + "_")]},
                             fake_user=True, compress=True)
    print(out, os.path.getsize(out)); print(blend, os.path.getsize(blend))

def run(pet, evo=0, do_export=True):
    C = CONFIG[pet if evo == 0 else f"{pet}{evo}"]
    sc, ob = import_pet(pet, evo)
    rig_ob = rig(pet, sc, ob, C)
    shape_keys(ob, C)
    animate(pet, rig_ob, C.get("arm_amp", 1.0))
    if do_export: export(pet, evo, sc, rig_ob, ob)
    return sc, rig_ob, ob

import sys
if "--" in sys.argv:   # blender -b --python pet_pipeline.py -- fresa robot [--no-export]
    _a = sys.argv[sys.argv.index("--") + 1:]
    PETS = [a for a in _a if not a.startswith("--")]; EXPORT = "--no-export" not in _a
import re
for _p in globals().get("PETS", []):   # "fresa" = evo0, "fresa2" = evo2
    _m = re.fullmatch(r"([a-z]+)([0-3]?)", _p)
    run(_m[1], int(_m[2] or 0), do_export=globals().get("EXPORT", True))
    _pv = [v for v in (_a if "--" in sys.argv else []) if v.startswith("--preview=")]
    if _pv:   # hoja de contacto: --preview=<carpeta>  -> <carpeta>/<pet><evo>_sheet.png
        _g = {"PET": _m[1], "OUT": os.path.join(_pv[0].split("=", 1)[1], f"{_p}_sheet.png")}
        exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else ".", "pet_preview.py"), encoding="utf8").read(), _g)
