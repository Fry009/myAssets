# Render frontal ortográfico con rejilla para medir (ortho 0.40, 750px, cámara z=0.18):
#   x=(px-375)/1875, z=0.18+(375-py)/1875 ; líneas cada 0.02, gruesas cada 0.1
# blender -b --factory-startup --python pet_front_grid.py -- <carpeta_salida> fresa2 robot3 ...
import bpy, math, os, sys
B=r"C:\Users\Fran\Desktop\Fran\myAssets\public\assets\blender-3d\pokecodes\pets"
import sys
_a=sys.argv[sys.argv.index("--")+1:]; OUT=_a[0]; MODELS=[(m[:-1], int(m[-1])) for m in _a[1:]]
sc=bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o,do_unlink=True)
cd=bpy.data.cameras.new("C"); cd.type='ORTHO'; cd.ortho_scale=0.40
cam=bpy.data.objects.new("Cam",cd); sc.collection.objects.link(cam); sc.camera=cam
cam.location=(0,-1,0.18); cam.rotation_euler=(math.radians(90),0,0)
wd=bpy.data.worlds.new("W"); wd.use_nodes=True; bg=wd.node_tree.nodes["Background"]; bg.inputs[0].default_value=(1,1,1,1); sc.world=wd
m=bpy.data.materials.new("G"); m.use_nodes=True; nt=m.node_tree; [nt.nodes.remove(n) for n in list(nt.nodes)]
e=nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value=(0,0.5,1,1); oo=nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0],oo.inputs[0])
grid=[]
for i in range(-10,11):
    for horiz in (0,1):
        me=bpy.data.meshes.new("g"); v=i*0.02
        th=0.0015 if i%5==0 else 0.0006
        if horiz: c=(0,-0.5,0.18+v); s=(0.25,0.001,th)
        else: c=(v,-0.5,0.18); s=(th,0.001,0.25)
        verts=[(c[0]+dx*s[0],c[1]+dy*s[1],c[2]+dz*s[2]) for dx in(-1,1) for dy in(-1,1) for dz in(-1,1)]
        faces=[(0,1,3,2),(4,5,7,6),(0,1,5,4),(2,3,7,6),(0,2,6,4),(1,3,7,5)]
        me.from_pydata(verts,[],faces); me.materials.append(m)
        o=bpy.data.objects.new("G",me); sc.collection.objects.link(o)
sc.render.engine='BLENDER_EEVEE'; sc.view_settings.view_transform='Standard'
sc.render.resolution_x=sc.render.resolution_y=750
for pet, evo in MODELS:
    if True:
        for o in list(sc.objects):
            if o.type=='MESH' and o.name!="G" and not o.name.startswith("G."): bpy.data.objects.remove(o,do_unlink=True)
        bpy.ops.import_scene.gltf(filepath=os.path.join(B,pet,f"evo{evo}.glb"))
        sc.render.filepath=os.path.join(OUT,f"{pet}{evo}.png"); bpy.ops.render.render(write_still=True)
        print("R",pet,evo)
