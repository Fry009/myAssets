import { Suspense, useEffect, useMemo, useRef } from 'react'
import { Canvas, useFrame, useLoader } from '@react-three/fiber'
import { Bounds, Grid, OrbitControls, useAnimations, useGLTF, useProgress } from '@react-three/drei'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js'
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js'

// Parpadeo: cada 2–5 s cierra los ojos ~0.16 s
const BLINK_TIME = 0.16

function GltfModel({ src, clip, morphs, autoBlink, onRig }) {
  const { scene, animations } = useGLTF(src)
  const { actions, names } = useAnimations(animations, scene)
  const morphMeshes = useMemo(() => {
    const list = []
    scene.traverse((o) => o.morphTargetDictionary && list.push(o))
    return list
  }, [scene])
  const blink = useRef({ next: 1.5, start: -1 })

  useEffect(() => {
    onRig?.({
      clips: names,
      morphs: Object.keys(morphMeshes[0]?.morphTargetDictionary || {}),
    })
  }, [names, morphMeshes, onRig])

  useEffect(() => {
    const action = clip && actions[clip]
    if (!action) return
    action.reset().fadeIn(0.25).play()
    return () => action.fadeOut(0.25)
  }, [clip, actions])

  useFrame(({ clock }, dt) => {
    if (!morphMeshes.length) return
    const t = clock.elapsedTime
    let blinkValue = 0
    if (autoBlink) {
      const b = blink.current
      if (b.start < 0 && t >= b.next) b.start = t
      if (b.start >= 0) {
        const p = (t - b.start) / BLINK_TIME
        blinkValue = p < 0.5 ? p * 2 : Math.max(0, 2 - p * 2)
        if (p >= 1) {
          b.start = -1
          b.next = t + 2 + Math.random() * 3
        }
      }
    }
    const k = Math.min(1, dt * 12)
    for (const mesh of morphMeshes) {
      const dict = mesh.morphTargetDictionary
      const inf = mesh.morphTargetInfluences
      for (const name in dict) {
        let target = morphs?.[name] || 0
        if (name === 'blink') target = Math.max(target, blinkValue)
        const i = dict[name]
        inf[i] += (target - inf[i]) * (name === 'blink' && blinkValue ? 1 : k)
      }
    }
  })

  return <primitive object={scene} />
}

function MeshInner({ src, ext, ...rig }) {
  if (ext === 'obj') {
    const obj = useLoader(OBJLoader, src)
    return <primitive object={obj} />
  }
  if (ext === 'fbx') {
    const fbx = useLoader(FBXLoader, src)
    return <primitive object={fbx} />
  }
  return <GltfModel src={src} {...rig} />
}

function AutoRotate({ children, speed = 0.6 }) {
  const ref = useRef()
  useFrame((_, dt) => {
    if (ref.current) ref.current.rotation.y += dt * speed
  })
  return <group ref={ref}>{children}</group>
}

function LoadingOverlay() {
  const { active, progress } = useProgress()
  if (!active) return null
  return <div className="loading-overlay">{Math.round(progress)}%</div>
}

export default function ModelScene({
  src,
  ext,
  variant = 'modal',
  autoplay = false,
  clip,
  morphs,
  autoBlink = false,
  onRig,
}) {
  const rig = { clip, morphs, autoBlink, onRig }
  const isCard = variant === 'card'
  const cam = isCard ? [3.2, 2.4, 3.6] : [1.8, 1.5, 5]
  return (
    <>
      <Canvas
        dpr={[1, isCard ? 1.5 : 2]}
        camera={{ position: cam, fov: 45 }}
        style={{ width: '100%', height: '100%' }}
        gl={{ antialias: true, alpha: false }}
      >
        <color attach="background" args={['#0a0d1a']} />
        <ambientLight intensity={0.65} />
        <directionalLight position={[5, 7, 4]} intensity={1.6} />
        <directionalLight position={[-5, -2, -4]} intensity={0.5} color="#7aa2ff" />
        <spotLight position={[0, 6, 0]} intensity={0.6} angle={0.5} penumbra={1} />

        <Suspense fallback={null}>
          <Bounds fit clip margin={isCard ? 1.15 : 1.35}>
            {autoplay ? (
              <AutoRotate>
                <MeshInner src={src} ext={ext} {...rig} />
              </AutoRotate>
            ) : (
              <MeshInner src={src} ext={ext} {...rig} />
            )}
          </Bounds>
        </Suspense>

        {!isCard && (
          <>
            <OrbitControls
              makeDefault
              enableDamping
              dampingFactor={0.09}
              minDistance={0.5}
              maxDistance={60}
            />
            <Grid
              infiniteGrid
              fadeDistance={40}
              cellSize={0.5}
              cellColor="#233060"
              sectionSize={2.5}
              sectionColor="#3a4a86"
              position={[0, -2, 0]}
            />
          </>
        )}
        {isCard && (
          <OrbitControls
            enabled={false}
            enableZoom={false}
            enablePan={false}
            enableRotate={false}
          />
        )}
      </Canvas>
      <LoadingOverlay />
    </>
  )
}
