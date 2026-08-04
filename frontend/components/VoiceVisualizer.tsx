'use client';

import { useState, useEffect, useRef } from 'react';
import { useJarvis } from '@/context/JarvisContext';

export default function VoiceVisualizer({ className = '' }: { className?: string }) {
  const { isListening, isSpeaking } = useJarvis();
  const [volume, setVolume] = useState(0);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    if (isListening) {
      const animate = () => {
        setVolume(Math.random());
        animationRef.current = requestAnimationFrame(animate);
      };

      animationRef.current = requestAnimationFrame(animate);
      return () => {
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
      };
    }

    setVolume(0);
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    return undefined;
  }, [isListening]);

  useEffect(() => {
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  const active = isListening || isSpeaking;
  const bars = Array.from({ length: 20 }, (_, i) => i);

  return (
    <div className={`${className} relative w-full h-16`}>
      <div className="absolute inset-0 pointer-events-none">
        <svg
          className="w-full h-full"
          viewBox="0 0 200 40"
          preserveAspectRatio="xMidYMid meet"
        >
          {bars.map((i) => {
            const x = i * 10 + 5;
            const height = Math.max(2, volume * 30 * (0.5 + Math.sin(i * 0.5) * 0.5));
            const y = 40 - height;

            return (
              <rect
                key={i}
                x={x}
                y={y}
                width={4}
                height={height}
                fill={i % 3 === 0 ? 'rgba(14, 165, 233, 0.8)' : 'rgba(14, 165, 233, 0.5)'}
                opacity={active ? 0.8 : 0.3}
              />
            );
          })}
        </svg>
      </div>

      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div
          className={`w-4 h-4 rounded-full transition-all duration-300 ${
            active ? 'bg-jarvis-500' : 'bg-jarvis-500/20'
          }`}
          style={{ transform: `scale(${active ? 1.2 : 1})` }}
        >
          {active && (
            <div className="absolute inset-0 rounded-full border-2 border-jarvis-500/50 animate-pulse" />
          )}
        </div>
      </div>

      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 mb-1 text-xs text-gray-500 dark:text-gray-400">
        {isListening ? 'Listening...' : isSpeaking ? 'Speaking...' : 'Voice Input'}
      </div>
    </div>
  );
}
