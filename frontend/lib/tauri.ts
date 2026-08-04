'use client';

export const isTauri = (): boolean =>
  typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;

export function applyTauriClass() {
  if (typeof window === 'undefined') return;
  if (isTauri()) {
    document.documentElement.classList.add('tauri');
  }
}
