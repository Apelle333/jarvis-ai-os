'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Grid, Stars } from '@react-three/drei';
import type { Group } from 'three';

/**
 * Holographic backdrop: a glowing perspective grid floor + faint starfield.
 * Purely ambient - never blocks the UI.
 */
export default function HologramBackground() {
  const gridRef = useRef<Group>(null);

  useFrame((state) => {
    if (gridRef.current) {
      // slow holographic drift so the grid feels alive
      gridRef.current.position.z = (Math.sin(state.clock.elapsedTime * 0.08) * 0.3);
    }
  });

  return (
    <group>
      <Stars
        radius={70}
        depth={40}
        count={1200}
        factor={2.5}
        saturation={0}
        fade
        speed={0.4}
      />

      <group ref={gridRef} position={[0, -2.6, 0]}>
        <Grid
          position={[0, 0, 0]}
          args={[80, 80]}
          cellSize={0.6}
          cellThickness={0.6}
          cellColor="#0e7490"
          sectionSize={3}
          sectionThickness={1}
          sectionColor="#22d3ee"
          fadeDistance={32}
          fadeStrength={2}
          infiniteGrid
          followCamera={false}
        />
      </group>
    </group>
  );
}
