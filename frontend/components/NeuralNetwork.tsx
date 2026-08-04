'use client';

import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Group, Points, LineSegments } from 'three';
import type { JarvisVisualState } from '@/lib/jarvisState';
import { STATE_COLOR } from '@/lib/jarvisState';

interface Props {
  state: JarvisVisualState;
}

const NODE_COUNT = 54;
const RADIUS = 5.2;
const LINK_DIST = 2.1;

/**
 * Rotating neural network field rendered around the core.
 * Accelerates + brightens while JARVIS is thinking/executing.
 */
export default function NeuralNetwork({ state }: Props) {
  const groupRef = useRef<Group>(null);
  const pointsRef = useRef<Points>(null);
  const linksRef = useRef<LineSegments>(null);

  const { nodePositions, edgePositions } = useMemo(() => {
    const positions: number[] = [];
    for (let i = 0; i < NODE_COUNT; i += 1) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = RADIUS * (0.35 + Math.random() * 0.65);
      positions.push(
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi)
      );
    }

    const edges: number[] = [];
    for (let i = 0; i < NODE_COUNT; i += 1) {
      for (let j = i + 1; j < NODE_COUNT; j += 1) {
        const dx = positions[i * 3] - positions[j * 3];
        const dy = positions[i * 3 + 1] - positions[j * 3 + 1];
        const dz = positions[i * 3 + 2] - positions[j * 3 + 2];
        const d = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (d < LINK_DIST) {
          edges.push(positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2]);
          edges.push(positions[j * 3], positions[j * 3 + 1], positions[j * 3 + 2]);
        }
      }
    }

    const edgeGeometry = new THREE.BufferGeometry();
    edgeGeometry.setAttribute(
      'position',
      new THREE.Float32BufferAttribute(edges, 3)
    );

    const nodeGeometry = new THREE.BufferGeometry();
    nodeGeometry.setAttribute(
      'position',
      new THREE.Float32BufferAttribute(positions, 3)
    );

    return { nodePositions: nodeGeometry, edgePositions: edgeGeometry };
  }, []);

  useFrame((clockState) => {
    if (!groupRef.current) return;
    const t = clockState.clock.elapsedTime;

    const speed =
      state === 'EXECUTING' ? 0.6 : state === 'THINKING' ? 0.4 : state === 'SPEAKING' ? 0.25 : 0.12;
    groupRef.current.rotation.y = t * speed;
    groupRef.current.rotation.x = Math.sin(t * 0.1) * 0.08;

    const intensity = state === 'EXECUTING' || state === 'THINKING' ? 1 : 0.45;
    if (linksRef.current) {
      const mat = linksRef.current.material as THREE.LineBasicMaterial;
      mat.opacity = THREE.MathUtils.lerp(mat.opacity, intensity, 0.05);
    }
    if (pointsRef.current) {
      const mat = pointsRef.current.material as THREE.PointsMaterial;
      const targetSize = state === 'EXECUTING' ? 0.16 : state === 'THINKING' ? 0.13 : 0.09;
      mat.size = THREE.MathUtils.lerp(mat.size, targetSize, 0.05);
    }
  });

  return (
    <group ref={groupRef}>
      <points ref={pointsRef} geometry={nodePositions}>
        <pointsMaterial
          color={STATE_COLOR[state]}
          size={0.1}
          sizeAttenuation
          transparent
          opacity={0.9}
          depthWrite={false}
        />
      </points>
      <lineSegments ref={linksRef} geometry={edgePositions}>
        <lineBasicMaterial
          color={STATE_COLOR[state]}
          transparent
          opacity={0.3}
          depthWrite={false}
        />
      </lineSegments>
    </group>
  );
}
