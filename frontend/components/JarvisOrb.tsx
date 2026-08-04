'use client';

import { useMemo } from 'react';
import { useJarvis } from '@/context/JarvisContext';

type OrbState = 'idle' | 'listening' | 'processing' | 'speaking' | 'executing';

const PARTICLE_COUNT = 8;

export default function JarvisOrb({ className = '' }: { className?: string }) {
  const { isListening, isProcessing, isSpeaking, backendOnline } = useJarvis();

  const state: OrbState = isProcessing
    ? 'processing'
    : isSpeaking
      ? 'speaking'
      : isListening
        ? 'listening'
        : backendOnline
          ? 'idle'
          : 'executing';

  const particles = useMemo(
    () =>
      Array.from({ length: PARTICLE_COUNT }, () => ({
        left: Math.random() * 100,
        top: Math.random() * 100,
        delay: Math.random() * 3,
        duration: Math.random() * 2 + 2
      })),
    []
  );

  const orbClassName = state === 'processing' ? 'animate-spin' : state !== 'idle' ? 'animate-pulse' : '';
  const ringColor = {
    idle: 'border-jarvis-500/30',
    listening: 'border-jarvis-400/60',
    processing: 'border-jarvis-300/80',
    speaking: 'border-green-400/70',
    executing: 'border-amber-500/60'
  }[state];

  return (
    <div className={`relative w-20 h-20 mx-auto ${className}`}>
      <div className="absolute inset-0 flex items-center justify-center">
        <div
          className={`w-full h-full rounded-full bg-jarvis-500/20 backdrop-blur-sm flex items-center justify-center border-2 ${ringColor} ${orbClassName}`}
        >
          <div className="w-12 h-12 rounded-full bg-jarvis-500/60 flex items-center justify-center">
            <div className="w-8 h-8 rounded-full bg-white/80 flex items-center justify-center">
              <span className="text-xs font-bold text-jarvis-900">J</span>
            </div>
          </div>
        </div>
      </div>

      <div className="absolute inset-0 pointer-events-none">
        {particles.map((p, i) => (
          <div
            key={i}
            className="absolute w-2 h-2 bg-jarvis-500/50 rounded-full"
            style={{
              left: `${p.left}%`,
              top: `${p.top}%`,
              animationDelay: `${p.delay}s`,
              animationDuration: `${p.duration}s`
            }}
          />
        ))}
      </div>
    </div>
  );
}
