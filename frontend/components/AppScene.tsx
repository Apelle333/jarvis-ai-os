'use client';

import { Canvas } from '@react-three/fiber';
import { useReducedMotion } from 'framer-motion';
import { useEffect, useState } from 'react';
import * as THREE from 'three';
import HologramBackground from '@/components/HologramBackground';
import StatusParticles from '@/components/StatusParticles';
import NeuralNetwork from '@/components/NeuralNetwork';
import JarvisCore from '@/components/JarvisCore';
import VoiceRing from '@/components/VoiceRing';
import { useJarvisVisualState } from '@/lib/jarvisState';

/**
 * Single transparent WebGL canvas hosting the whole holographic scene.
 * One context = one draw loop = high FPS on the RTX 4060 Ti.
 */
export default function AppScene() {
  const state = useJarvisVisualState();
  const reduceMotion = useReducedMotion();
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const updateVisibility = () => setVisible(!document.hidden);
    updateVisibility();
    document.addEventListener('visibilitychange', updateVisibility);
    return () => document.removeEventListener('visibilitychange', updateVisibility);
  }, []);

  if (reduceMotion) {
    return <div className="hud-static-core absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" />;
  }

  return (
    <div className="absolute inset-0 pointer-events-none">
      <Canvas
        dpr={[1, 1.75]}
        frameloop={visible ? 'always' : 'demand'}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance'
        }}
        onCreated={({ gl }) => {
          gl.outputColorSpace = THREE.SRGBColorSpace;
        }}
        camera={{ position: [0, 0, 9], fov: 55 }}
        style={{ pointerEvents: 'none' }}
      >
        <fog attach="fog" args={['#05080f', 18, 42]} />
        <ambientLight intensity={0.4} />
        <pointLight position={[4, 4, 4]} intensity={60} color="#22d3ee" />
        <pointLight position={[-4, -3, 2]} intensity={35} color="#3b82f6" />

        <HologramBackground />
        <NeuralNetwork state={state} />
        <StatusParticles state={state} />
        <VoiceRing state={state} />
        <JarvisCore state={state} />
      </Canvas>
    </div>
  );
}
