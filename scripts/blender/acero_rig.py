import bpy, numpy as np, math
sc=bpy.data.scenes["Acero_Rig"]; bpy.context.window.scene=sc
me_ob=bpy.data.objects["acero_evo0"]; me=me_ob.data
# clean previous runs
for o in list(sc.objects):
    if o.type=='ARMATURE': bpy.data.objects.remove(o, do_unlink=True)
me_ob.modifiers.clear(); me_ob.vertex_groups.clear(); me_ob.parent=None
if me.shape_keys:
    me_ob.shape_key_clear()

# ---------- ARMATURE ----------
arm=bpy.data.armatures.new("Acero_Armature"); arm.display_type='STICK'
ao=bpy.data.objects.new("Acero_Rig", arm); sc.collection.objects.link(ao); ao.show_in_front=True
bpy.context.view_layer.objects.active=ao
for o in bpy.context.view_layer.objects: o.select_set(False)
ao.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb=arm.edit_bones
def bone(n,h,t,parent=None,deform=True):
    b=eb.new(n); b.head=h; b.tail=t; b.roll=0
    if parent: b.parent=eb[parent]
    b.use_deform=deform; return b
bone("root",(0,0,0),(0,0.04,0),deform=False)
bone("body",(0,0.005,0.03),(0,0.005,0.17),"root")
for s,k in (("L",1),("R",-1)):
    bone(f"hand.{s}",(0.068*k,0.008,0.05),(0.104*k,0.008,0.05),"body")
    bone(f"foot.{s}",(0.035*k,0.018,0.036),(0.035*k,0.018,0.002),"root")
bpy.ops.object.mode_set(mode='OBJECT')

# ---------- WEIGHTS ----------
co=np.empty(len(me.vertices)*3,dtype=np.float64); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
x,y,z=co[:,0],co[:,1],co[:,2]; ax=np.abs(x)
def ss(a,b,v):
    t=np.clip((v-a)/(b-a),0,1); return t*t*(3-2*t)
hand=ss(0.063,0.073,ax)*(1-ss(0.068,0.082,z))*ss(0.018,0.028,z)
foot=(1-ss(0.024,0.038,z))*ss(0.008,0.02,ax)*(1-hand)
body=np.clip(1-hand-foot,0,1)
L=x>0
groups={"body":body,"hand.L":hand*L,"hand.R":hand*(~L),"foot.L":foot*L,"foot.R":foot*(~L)}
for n,w in groups.items():
    vg=me_ob.vertex_groups.new(name=n)
    for val in np.unique(np.round(w,3)):
        if val<=0.001: continue
        idx=np.nonzero(np.round(w,3)==val)[0].tolist()
        vg.add(idx,float(val),'REPLACE')
me_ob.parent=ao
mod=me_ob.modifiers.new("Armature",'ARMATURE'); mod.object=ao

# ---------- SHAPE KEYS (expresiones) ----------
EYES={"L":(0.0335,0.1055),"R":(-0.0275,0.1055)}   # L = izquierda del personaje (+X)
ERX,ERZ=0.0195,0.0225
MC=(0.003,0.083); MRX,MRZ=0.0088,0.0068
front=(y< -0.008).astype(float)*ss(-0.034,-0.029,y)
def fall(r,r0,r1): return (1-ss(r0,r1,r))*front
def _e(c,rx,rz): return np.sqrt(((x-c[0])/rx)**2+((z-c[1])/rz)**2)
MOUTH_MASK=ss(1.15,2.0,_e(MC,MRX,MRZ))
EYE_MASK=np.minimum(ss(1.0,1.35,_e(EYES["L"],ERX,ERZ)),ss(1.0,1.35,_e(EYES["R"],ERX,ERZ)))
def ell(c,rx,rz): return np.sqrt(((x-c[0])/rx)**2+((z-c[1])/rz)**2)
def add(name,dx,dz):
    k=me_ob.shape_key_add(name=name,from_mix=False)
    new=co.copy(); new[:,0]+=dx; new[:,2]+=dz
    k.data.foreach_set("co",new.ravel()); return k
me_ob.shape_key_add(name="Basis")
Z=np.zeros_like(x)
def eye_ops(fn, sides=("L","R")):
    dx=Z.copy(); dz=Z.copy()
    for s in sides:
        c=EYES[s]; r=ell(c,ERX,ERZ); a,b=fn(s,c,r); dx+=a; dz+=b
    return dx,dz
# parpadeo
def blink(s,c,r):
    line=c[1]-0.45*ERZ; f=np.where(z<line,fall(r,1.0,1.18),fall(r,1.05,1.45))*MOUTH_MASK
    return Z, (line-z)*0.92*f
for s in ("L","R"): add(f"blink_{s}",*eye_ops(blink,(s,)))
add("blink",*eye_ops(blink))
# ojos felices ^ ^
def happy(s,c,r):
    u=np.clip((x-c[0])/ERX,-1.2,1.2)
    line=c[1]-0.15*ERZ+0.45*ERZ*(1-u*u)
    f=np.where(z<line,fall(r,1.0,1.2),fall(r,1.05,1.5))*MOUTH_MASK
    return Z,(line+(z-c[1])*0.22-z)*f
add("eyes_happy",*eye_ops(happy))
# ojos sorprendidos
def wide(s,c,r):
    f=0.22*(1-ss(1.0,1.6,r))*front*MOUTH_MASK
    return (x-c[0])*f,(z-c[1])*f
add("eyes_wide",*eye_ops(wide))
# triste / enfadado: rotar ojo + aplastar desde arriba
def tilt(ang,squash):
    def fn(s,c,r):
        a=math.radians(ang)*(1 if s=="R" else -1)   # +: esquina interior arriba
        ca,sa=math.cos(a),math.sin(a); px,pz=x-c[0],z-c[1]
        rx_=ca*px-sa*pz; rz_=sa*px+ca*pz
        top=c[1]-ERZ; rz_=np.where(pz>0,(rz_)*squash,rz_)
        f=fall(r,1.0,1.5)*MOUTH_MASK
        return (rx_-px)*f,(rz_-pz)*f
    return fn
add("eyes_sad",*eye_ops(tilt(16,0.8)))
add("eyes_angry",*eye_ops(tilt(-18,0.72)))
# mirar
for n,(ddx,ddz) in {"look_left":(0.3*ERX,0),"look_right":(-0.3*ERX,0),"look_up":(0,0.22*ERZ),"look_down":(0,-0.22*ERZ)}.items():
    def lk(s,c,r,ddx=ddx,ddz=ddz):
        f=fall(r,1.0,1.6)*MOUTH_MASK; return ddx*f,ddz*f
    add(n,*eye_ops(lk))
# boca
rm=ell(MC,MRX,MRZ); pxm,pzm=x-MC[0],z-MC[1]
f=fall(rm,1.0,2.0)*EYE_MASK; top=MRZ
add("mouth_open",pxm*0.15*f,(pzm-top)*0.9*f)
u=np.clip(pxm/MRX,-1.5,1.5)
add("mouth_smile",pxm*0.4*f,(0.45*MRZ*u*u-0.25*MRZ)*f)
add("mouth_sad",pxm*0.1*f,(-0.5*MRZ*u*u+0.25*MRZ)*f)
add("mouth_o",-pxm*0.3*f,pzm*0.45*f)
print("bones",[b.name for b in arm.bones])
print("keys",[k.name for k in me.shape_keys.key_blocks])
print("weights sum check", float(np.min(body+hand+foot)), float(np.max(body+hand+foot)))
for k in me.shape_keys.key_blocks[1:]: k.value=0.0
