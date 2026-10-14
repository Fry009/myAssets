# Rehace las animaciones de Acero evo0 con las de pet_pipeline.py (mismos huesos y ejes) y reexporta.
# blender -b public/assets/blender-3d/pokecodes/pets/acero/acero_rig.blend --python scripts/blender/acero_reanim.py
import bpy, os
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pet_pipeline.py"), encoding="utf8").read()
exec(src.split("import sys\nif \"--\"")[0])   # solo las definiciones
sc = bpy.data.scenes["Acero_Rig"]
rig_ob = bpy.data.objects["Acero_Rig"]; ob = bpy.data.objects["acero_evo0"]
override(sc)
animate("acero", rig_ob)
export("acero", 0, sc, rig_ob, ob)
