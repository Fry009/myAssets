# Primer plano de la cara con rejilla de 1 cm (ortho 0.10, 500px => 5000 px/u, centro en (cx,cz)),
# neutro y con la shape key indicada. x=cx+(px-250)/5000, z=cz+(250-py)/5000
# blender -b --factory-startup --python pet_face_closeup.py -- fuegito1 0.05 0.15 <carpeta_salida> [blink]
import bpy, sys, math, os
a=sys.argv[sys.argv.index("--")+1:]; P=a[0]; cx,cz=float(a[1]),float(a[2]); OUT=a[3]; keyname=a[4] if len(a)>4 else "blink"
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pet_pipeline.py"),encoding="utf8").read().split("import sys\nif \"--\"")[0]
exec(src)
import re; m=re.fullmatch(r"([a-z]+)([0-3]?)",P); sc,rig_ob,ob=run(m[1],int(m[2] or 0),do_export=False)
cd=bpy.data.cameras.new("F"); cd.type='ORTHO'; cd.ortho_scale=0.10; cam=bpy.data.objects.new("F",cd); sc.collection.objects.link(cam); sc.camera=cam
cam.location=(cx,-1,cz); cam.rotation_euler=(math.radians(90),0,0)
wd=bpy.data.worlds.new("W"); wd.use_nodes=True; wd.node_tree.nodes["Background"].inputs[0].default_value=(1,1,1,1); sc.world=wd
# rejilla cada 0.01
mt=bpy.data.materials.new("G"); mt.use_nodes=True; nt=mt.node_tree; [nt.nodes.remove(n) for n in list(nt.nodes)]
e=nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value=(0,0.5,1,1); oo=nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0],oo.inputs[0])
for i in range(-5,6):
  for h in (0,1):
    me=bpy.data.meshes.new("g"); c=(cx,-0.5,cz+i*0.01) if h else (cx+i*0.01,-0.5,cz); s=(0.06,0.001,0.0002) if h else (0.0002,0.001,0.06)
    me.from_pydata([(c[0]+dx*s[0],c[1]+dy*s[1],c[2]+dz*s[2]) for dx in(-1,1) for dy in(-1,1) for dz in(-1,1)],[],[(0,1,3,2),(4,5,7,6),(0,1,5,4),(2,3,7,6),(0,2,6,4),(1,3,7,5)]); me.materials.append(mt)
    sc.collection.objects.link(bpy.data.objects.new("G",me))
sc.render.engine='BLENDER_EEVEE'; sc.view_settings.view_transform='Standard'; sc.render.resolution_x=sc.render.resolution_y=500
for v in (0,1):
  ob.data.shape_keys.key_blocks[keyname].value=v; sc.render.filepath=os.path.join(OUT, "face_%s_%d.png"%(P,v))
  with override(sc): bpy.ops.render.render(write_still=True)
