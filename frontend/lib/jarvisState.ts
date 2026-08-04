'use client';

import { useJarvis } from '@/context/JarvisContext';

export type JarvisVisualState =
  | 'IDLE'
  | 'LISTENING'
  | 'THINKING'
  | 'EXECUTING'
  | 'SPEAKING';

interface BrainStatus {
  brain?: {
    state?: string;
  };
}

export function useJarvisVisualState(): JarvisVisualState {
  const { isProcessing, isListening, isSpeaking, status } = useJarvis();

  const brainState = (status as BrainStatus | null)?.brain?.state;

  if (brainState === 'executing') return 'EXECUTING';
  if (isProcessing || brainState === 'processing') return 'THINKING';
  if (isSpeaking || brainState === 'speaking') return 'SPEAKING';
  if (isListening || brainState === 'listening') return 'LISTENING';
  return 'IDLE';
}

export const STATE_COLOR: Record<JarvisVisualState, string> = {
  IDLE: '#22d3ee',
  LISTENING: '#34d399',
  THINKING: '#818cf8',
  EXECUTING: '#fbbf24',
  SPEAKING: '#60a5fa'
};

export const STATE_LABEL: Record<JarvisVisualState, string> = {
  IDLE: 'STANDBY',
  LISTENING: 'LISTENING',
  THINKING: 'SYNTHESIZING',
  EXECUTING: 'EXECUTING',
  SPEAKING: 'SPEAKING'
};
