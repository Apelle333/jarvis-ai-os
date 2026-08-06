'use client';

import { useMemo, useState } from 'react';
import { useJarvis } from '@/context/JarvisContext';

type OrbState = 'idle' | 'listening' | 'processing' | 'speaking' | 'executing' | 'error';

const PARTICLE_COUNT = 8;

export default function JarvisOrb({ className = '' }: { className?: string }) {
  const { isListening, isProcessing, isSpeaking, backendOnline, plannerState, agentState, systemState } = useJarvis();
  const [hovered, setHovered] = useState(false);

  // Enhanced state mapping using runtime telemetry
  let state: OrbState = 'idle';

  if (systemState && systemState.error) {
    state = 'error';
  } else if (isListening || (systemState && systemState.voice_state === 'listening')) {
    state = 'listening';
  } else if (agentState && agentState.active_task) {
    state = 'executing';
  } else if (isProcessing || (plannerState && (plannerState.last_plan_id || plannerState.current_step))) {
    state = 'processing';
  } else if (isSpeaking) {
    state = 'speaking';
  } else if (!backendOnline) {
    state = 'executing';
  } else {
    state = 'idle';
  }

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

  const ringStyle = {
    idle: { boxShadow: '0 0 18px rgba(34,211,238,0.12)', borderColor: 'rgba(34,211,238,0.18)' },
    listening: { boxShadow: '0 0 28px rgba(34,211,238,0.28)', borderColor: 'rgba(96,165,250,0.35)' },
    processing: { boxShadow: '0 0 30px rgba(99,102,241,0.32)', borderColor: 'rgba(99,102,241,0.45)' },
    speaking: { boxShadow: '0 0 26px rgba(34,197,94,0.28)', borderColor: 'rgba(34,197,94,0.45)' },
    executing: { boxShadow: '0 0 20px rgba(245,158,11,0.22)', borderColor: 'rgba(245,158,11,0.35)' }
  } as Record<OrbState, any>;

  const ring = ringStyle[state];

  return (
    <div
      className={`relative w-24 h-24 mx-auto ${className} transition-all duration-300`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      aria-label={`Jarvis Orb - state ${state}`}
      title={`JARVIS - ${state.toUpperCase()}`}
    >
      <div className="absolute inset-0 flex items-center justify-center">
        <div
          className="w-full h-full rounded-full backdrop-blur-md flex items-center justify-center border-2"
          style={{
            background: 'linear-gradient(180deg, rgba(255,255,255,0.02), rgba(8,10,12,0.18))',
            transform: hovered ? 'scale(1.025)' : 'scale(1.0)',
            transition: 'transform 260ms ease',
            borderColor: ring.borderColor,
            boxShadow: ring.boxShadow
          }}
        >
          <div
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-transform duration-400 ${
              isProcessing ? 'scale-95' : isSpeaking ? 'scale-105' : 'scale-100'
            }`}
            style={{
              background: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.06), rgba(8,12,16,0.6))',
              border: '1px solid rgba(255,255,255,0.03)'
            }}
          >
            <div className="w-10 h-10 rounded-full bg-white/90 flex items-center justify-center">
              <span className="text-xs font-bold text-jarvis-900">J</span>
            </div>
          </div>
        </div>
      </div>

      {/* ambient particles */}
      <div className="absolute inset-0 pointer-events-none">
        {particles.map((p, i) => (
          <div
            key={i}
            className="absolute w-1.5 h-1.5 rounded-full"
            style={{
              left: `${p.left}%`,
              top: `${p.top}%`,
              background: 'rgba(34,211,238,0.06)',
              boxShadow: '0 0 8px rgba(34,211,238,0.05)',
              animationDelay: `${p.delay}s`,
              animationDuration: `${p.duration}s`
            }}
          />
        ))}
      </div>

      {/* subtle ring */}
      <div
        className="absolute -inset-1 rounded-full pointer-events-none"
        style={{
          border: '1px solid transparent',
          boxShadow: isListening ? '0 0 36px rgba(34,211,238,0.18)' : isProcessing ? '0 0 32px rgba(99,102,241,0.15)' : 'none',
          transition: 'box-shadow 300ms ease'
        }}
      />
    </div>
  );
}
