'use client';

import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Group, Mesh } from 'three';
import type { JarvisVisualState } from '@/lib/jarvisState';
import { STATE_COLOR } from '@/lib/jarvisState';

interface Props {
  state: JarvisVisualState;
}

const BAR_COUNT = 56;
const RING_RADIUS = 2.6;

/**
 * Holographic audio ring. Rises around the core while listening/speaking,
 * with per-bar amplitude driven by a pseudo waveform.
 */
export default function VoiceRing({ state }: Props) {
  const groupRef = useRef<Group>(null);
  const barRefs = useRef<(Mesh | null)[]>([]);
  const phase = useRef(0);

  const bars = useMemo(
    () =>
      Array.from({ length: BAR_COUNT }, (_, i) => {
        const angle = (i / BAR_COUNT) * Math.PI * 2;
        return {
          angle,
          x: Math.cos(angle) * RING_RADIUS,
          z: Math.sin(angle) * RING_RADIUS
        };
      }),
    []
  );

  const active = state === 'LISTENING' || state === 'SPEAKING';

  useFrame((clockState) => {
    if (!groupRef.current) return;
    const t = clockState.clock.elapsedTime;

    if (!active) {
      groupRef.current.visible = false;
      return;
    }
    groupRef.current.visible = true;
    phase.current = t;
    groupRef.current.rotation.y = t * 0.4;

    bars.forEach((bar, i) => {
      const mesh = barRefs.current[i];
      if (!mesh) return;
      const wave =
        Math.sin(t * 6 + i * 0.35) * 0.5 +
        Math.sin(t * 12 + i * 0.7) * 0.3 +
        Math.sin(t * 3 + i * 0.15) * 0.2;
      const amp = 0.06 + Math.max(0, wave) * 0.34;
      mesh.scale.y = THREE.MathUtils.lerp(mesh.scale.y, amp, 0.25);
      mesh.position.y = amp / 2;
      const mat = mesh.material as THREE.MeshBasicMaterial;
      mat.opacity = 0.35 + amp * 1.6;
    });
  });

  return (
    <group ref={groupRef} visible={false}>
      {bars.map((bar, i) => (
        <mesh
          key={i}
          ref={(el) => {
            barRefs.current[i] = el;
          }}
          position={[bar.x, 0, bar.z]}
        >
          <boxGeometry args={[0.05, 1, 0.05]} />
          <meshBasicMaterial
            color={STATE_COLOR[state]}
            transparent
            opacity={0.4}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>
      ))}
    </group>
  );
}
