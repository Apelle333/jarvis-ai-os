'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sparkles } from '@react-three/drei';
import type { Group } from 'three';
import type { JarvisVisualState } from '@/lib/jarvisState';
import { STATE_COLOR } from '@/lib/jarvisState';

interface Props {
  state: JarvisVisualState;
}

/**
 * Ambient particle field that reacts to JARVIS state:
 * calm motes while idle, dense spinning motes while thinking/executing.
 */
export default function StatusParticles({ state }: Props) {
  const groupRef = useRef<Group>(null);

  useFrame((clockState) => {
    if (!groupRef.current) return;
    const t = clockState.clock.elapsedTime;
    const targetSpeed = state === 'EXECUTING' ? 2.2 : state === 'THINKING' ? 1.4 : 0.25;
    groupRef.current.rotation.y = THREE_LERP(groupRef.current.rotation.y, t * targetSpeed, 0.05);
  });

  const density = state === 'EXECUTING' ? 220 : state === 'THINKING' ? 160 : 90;

  return (
    <group ref={groupRef}>
      <Sparkles
        count={density}
        scale={14}
        size={2.4}
        speed={state === 'EXECUTING' ? 1.6 : state === 'THINKING' ? 0.9 : 0.3}
        opacity={state === 'IDLE' ? 0.35 : 0.7}
        color={STATE_COLOR[state]}
        noise={0.4}
      />
      <Sparkles count={40} scale={9} size={4} speed={0.5} color="#67e8f9" opacity={0.25} />
    </group>
  );
}

// tiny inline lerp to avoid importing maath
function THREE_LERP(a: number, b: number, t: number) {
  return a + (b - a) * t;
}
