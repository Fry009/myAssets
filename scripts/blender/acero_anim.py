import bpy, math
R=math.radians
sc=bpy.data.scenes["Acero_Rig"]; bpy.context.window.scene=sc
sc.render.fps=24
rig=bpy.data.objects["Acero_Rig"]
ad=rig.animation_data_create()
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
for a in list(bpy.data.actions):
    if a.name.startswith("acero_"): bpy.data.actions.remove(a)
pb=rig.pose.bones
for b in pb: b.rotation_mode='XYZ'
def reset():
    for b in pb: b.location=(0,0,0); b.rotation_euler=(0,0,0); b.scale=(1,1,1)
def key(f, **bones):
    # bones: name -> dict(rot=(x,y,z) deg, loc=(..), scl=(..))
    reset()
    for n,d in bones.items():
        b=pb[n]
        if 'rot' in d: b.rotation_euler=[R(v) for v in d['rot']]
        if 'loc' in d: b.location=d['loc']
        if 'scl' in d: b.scale=d['scl']
    for b in pb:
        b.keyframe_insert("location",frame=f); b.keyframe_insert("rotation_euler",frame=f); b.keyframe_insert("scale",frame=f)
def make(name, frames):
    act=bpy.data.actions.new("acero_"+name); act.use_fake_user=True
    ad.action=act
    for f,bones in frames: key(f,**bones)
    end=frames[-1][0]
    ad.action=None
    tr=ad.nla_tracks.new(); tr.name=name
    st=tr.strips.new(name,1,act); st.action_frame_end=end
    tr.mute=True
    return act
# ejes: hand.X local = sube la mano | hand.Z local = adelante/atrás
#       body.Z local = balanceo lateral | foot.X = punta adelante/atrás, foot loc Y(-)= levantar
make("idle",[
 (1,  dict(body=dict(scl=(1,1,1)), **{"hand.L":dict(rot=(5,0,0)),"hand.R":dict(rot=(5,0,0))})),
 (24, dict(body=dict(scl=(1.03,0.96,1.03)), **{"hand.L":dict(rot=(-3,0,0)),"hand.R":dict(rot=(-3,0,0))})),
 (48, dict(body=dict(scl=(1,1,1)), **{"hand.L":dict(rot=(5,0,0)),"hand.R":dict(rot=(5,0,0))})),
])
def walk(phase):
    s=1 if phase==0 else -1
    return dict(
        root=dict(loc=(0,0,0)),
        body=dict(rot=(0,0,6*s), loc=(0,0.004,0)),
        **{"foot.L":dict(rot=(25*s,0,0), loc=(0,-0.012 if s>0 else 0,0)),
           "foot.R":dict(rot=(-25*s,0,0), loc=(0,-0.012 if s<0 else 0,0)),
           "hand.L":dict(rot=(10,0,-25*s)), "hand.R":dict(rot=(10,0,-25*s))})
mid=lambda: dict(body=dict(loc=(0,0.009,0)), **{"hand.L":dict(rot=(10,0,0)),"hand.R":dict(rot=(10,0,0))})
make("walk",[(1,walk(0)),(7,mid()),(13,walk(1)),(19,mid()),(25,walk(0))])
wave_up=lambda a: dict(body=dict(rot=(0,0,-6)), **{"hand.L":dict(rot=(a,0,0)),"hand.R":dict(rot=(5,0,0))})
make("wave",[(1,dict()),(6,wave_up(55)),(10,wave_up(35)),(14,wave_up(58)),(18,wave_up(35)),(22,wave_up(58)),(26,wave_up(35)),(32,dict())])
make("jump",[
 (1,dict()),
 (6,dict(body=dict(scl=(1.12,0.8,1.12)), **{"hand.L":dict(rot=(-15,0,0)),"hand.R":dict(rot=(-15,0,0))})),
 (11,dict(root=dict(loc=(0,0,0.06)), body=dict(scl=(0.92,1.15,0.92)), **{"hand.L":dict(rot=(55,0,0)),"hand.R":dict(rot=(55,0,0)),"foot.L":dict(rot=(-15,0,0)),"foot.R":dict(rot=(-15,0,0))})),
 (16,dict(root=dict(loc=(0,0,0.07)), **{"hand.L":dict(rot=(45,0,0)),"hand.R":dict(rot=(45,0,0))})),
 (21,dict(root=dict(loc=(0,0,0)), body=dict(scl=(1.1,0.85,1.1)))),
 (26,dict()),
])
# root bone: loc en espacio local (Y=+Y mundo? root apunta a +Y => su Z local = +Z mundo)
reset()
print([ (t.name, t.strips[0].frame_end) for t in ad.nla_tracks])
