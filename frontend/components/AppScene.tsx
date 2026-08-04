'use client';

import { Canvas } from '@react-three/fiber';
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

  return (
    <div className="absolute inset-0 pointer-events-none">
      <Canvas
        dpr={[1, 1.75]}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance'
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
