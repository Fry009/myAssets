import bpy, os
D=r"C:\Users\Fran\Desktop\Fran\myAssets\public\assets\blender-3d\pokecodes\pets\acero"
sc=bpy.data.scenes["Acero_Rig"]; bpy.context.window.scene=sc
rig=bpy.data.objects["Acero_Rig"]; ob=bpy.data.objects["acero_evo0"]
rig.animation_data.action=None; sc.frame_set(1)
for b in rig.pose.bones: b.location=(0,0,0); b.rotation_euler=(0,0,0); b.scale=(1,1,1)
for o in bpy.context.view_layer.objects: o.select_set(False)
rig.select_set(True); ob.select_set(True); bpy.context.view_layer.objects.active=rig
for t in rig.animation_data.nla_tracks: t.mute=False
out=os.path.join(D,"evo0_rig.glb")
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB',
    export_animations=True, export_animation_mode='NLA_TRACKS', export_morph=True,
    export_skins=True, export_force_sampling=True, export_yup=True, use_active_scene=True)
for t in rig.animation_data.nla_tracks: t.mute=True
blend=os.path.join(D,"acero_rig.blend")
cam=sc.objects.get("AceroCam")
bpy.data.libraries.write(blend,{sc,rig,ob,*[a for a in bpy.data.actions if a.name.startswith("acero_")]},fake_user=True,compress=True)
print(out, os.path.getsize(out)); print(blend, os.path.getsize(blend))
