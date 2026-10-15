# Hoja de contacto para revisar un rig: pesos, expresiones y poses en un PNG.
# Requiere PET (y opcional OUT) definidos antes; la escena <Pet>_Rig debe existir (pet_pipeline.py).
import bpy, numpy as np, math, os
W = bpy.context.window_manager.windows[0]
sc = bpy.data.scenes[f"{PET.capitalize()}_Rig"]; W.scene = sc
rig = next(o for o in sc.objects if o.type == "ARMATURE"); ob = next(o for o in sc.objects if o.type == 'MESH')
OUT = globals().get("OUT", os.path.join(os.environ.get("TEMP", "."), f"{PET}_sheet.png"))
TMP = os.path.join(os.path.dirname(OUT), "_cell.png")
cam = sc.objects.get("PreviewCam")
if not cam:
    cd = bpy.data.cameras.new("PreviewCam"); cd.type = 'ORTHO'; cd.ortho_scale = 0.30
    cam = bpy.data.objects.new("PreviewCam", cd); sc.collection.objects.link(cam)
Hm = max(v.co.z for v in ob.data.vertices); cam.data.ortho_scale = max(0.30, Hm * 1.15)
cam.location = (0, -1, max(0.12, Hm * 0.5)); cam.rotation_euler = (math.radians(90), 0, 0); sc.camera = cam
wd = bpy.data.worlds.get("PreviewWorld") or bpy.data.worlds.new("PreviewWorld"); wd.use_nodes = True
bg = wd.node_tree.nodes["Background"]; bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 1.0
sc.world = wd; sc.render.resolution_x = sc.render.resolution_y = 360; sc.view_settings.view_transform = 'Standard'
keys = ob.data.shape_keys.key_blocks
ad = rig.animation_data

# color de pesos
me = ob.data; n = len(me.vertices)
cols = {"body": (0.8, 0.8, 0.8), "hand.L": (1, 0.1, 0.1), "hand.R": (1, 0.6, 0), "foot.L": (0.1, 0.3, 1), "foot.R": (0, 0.8, 1), "top": (0.1, 0.8, 0.1), "head": (0.75, 0.5, 1), "tail": (1, 0.3, 0.8), "tail2": (0.6, 0.2, 1), "tail3": (0.2, 0.9, 0.7)}
acc = np.zeros((n, 3))
for vg in ob.vertex_groups:
    w = np.zeros(n)
    for v in me.vertices:
        for g in v.groups:
            if g.group == vg.index: w[v.index] = g.weight
    acc += w[:, None] * np.array(cols.get(vg.name, (1, 0, 1)))
ca = me.color_attributes.get("_wviz") or me.color_attributes.new("_wviz", 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set("color", np.hstack([acc, np.ones((n, 1))]).astype(np.float32).ravel())

cells = []
def shot(label, engine='BLENDER_EEVEE'):
    sc.render.engine = engine; sc.render.filepath = TMP
    with bpy.context.temp_override(window=W, scene=sc): bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(TMP); px = np.array(im.pixels[:]).reshape(360, 360, 4).copy(); bpy.data.images.remove(im)
    cells.append(px)
def pose(clip=None, frame=1, **morphs):
    for k in keys[1:]: k.value = morphs.get(k.name, 0.0)
    for t in ad.nla_tracks: t.mute = True
    ad.action = None
    for b in rig.pose.bones: b.location = (0, 0, 0); b.rotation_euler = (0, 0, 0); b.scale = (1, 1, 1)
    if clip: ad.action = bpy.data.actions[f"{PET}_{clip}"]
    sc.frame_set(frame)
# 1 pesos (workbench con atributo de color)
pose()
sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'VERTEX'
me.color_attributes.active_color = ca
shot("weights", 'BLENDER_WORKBENCH')
pose(); shot("neutral")
pose(blink=1); shot("blink")
pose(eyes_happy=1, mouth_smile=1); shot("happy")
pose(eyes_wide=1, mouth_o=1); shot("surprise")
pose(eyes_sad=1, mouth_sad=1); shot("sad")
pose(eyes_angry=1, mouth_sad=0.6); shot("angry")
pose(look_left=1, mouth_open=0.8); shot("look+talk")
pose("wave", 14); shot("wave")
pose("jump", 6); shot("jump-crouch")
pose("jump", 11); shot("jump-up")
pose("walk", 1); shot("walk")
pose()
me.color_attributes.remove(ca)
# 4 columnas x 3 filas
rows = [np.concatenate(cells[i:i + 4], axis=1) for i in range(0, 12, 4)]
sheet = np.concatenate(rows[::-1], axis=0)   # pixels de Blender van de abajo a arriba
h, w = sheet.shape[:2]
im = bpy.data.images.new("_sheet", w, h); im.pixels.foreach_set(sheet.astype(np.float32).ravel()); im.filepath_raw = OUT; im.file_format = 'PNG'; im.save()
bpy.data.images.remove(im)
print("sheet", OUT)
