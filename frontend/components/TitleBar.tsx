'use client';

import { useEffect, useState } from 'react';
import { useJarvis } from '@/context/JarvisContext';
import { useJarvisVisualState, STATE_COLOR, STATE_LABEL } from '@/lib/jarvisState';
import { isTauri, applyTauriClass } from '@/lib/tauri';

type WindowApi = {
  minimize: () => Promise<void>;
  toggleMaximize: () => Promise<void>;
  close: () => Promise<void>;
  isMaximized: () => Promise<boolean>;
};

/**
 * Custom frameless title bar: JARVIS identity + live connection status on the
 * left/center, native window controls on the right. Doubles as the drag region.
 */
export default function TitleBar() {
  const { backendOnline, wsConnected } = useJarvis();
  const state = useJarvisVisualState();
  const [isMax, setIsMax] = useState(false);
  const [win, setWin] = useState<WindowApi | null>(null);

  useEffect(() => {
    applyTauriClass();
    if (isTauri()) {
      import('@tauri-apps/api/window')
        .then(({ getCurrentWindow }) => {
          const w = getCurrentWindow();
          setWin({
            minimize: () => w.minimize(),
            toggleMaximize: () => w.toggleMaximize(),
            close: () => w.close(),
            isMaximized: () => w.isMaximized()
          });
          w.onResized(() => {
            w.isMaximized().then(setIsMax).catch(() => {});
          });
          w.isMaximized().then(setIsMax).catch(() => {});
        })
        .catch(() => {});
    }
  }, []);

  const tauri = isTauri();
  const accent = STATE_COLOR[state];

  return (
    <header
      data-tauri-drag-region
      className="fixed top-0 inset-x-0 z-40 h-11 flex items-center px-3 select-none"
      style={{ background: 'rgba(5, 9, 16, 0.55)', backdropFilter: 'blur(14px)' }}
    >
      <div className="absolute inset-x-0 bottom-0 h-px hud-line" />

      {/* Identity */}
      <div data-tauri-drag-region className="flex items-center gap-3 min-w-0 flex-1">
        <div className="relative w-7 h-7 flex items-center justify-center">
          <div
            className="w-7 h-7 rounded-full"
            style={{
              background: `radial-gradient(circle at 35% 35%, #e0faff, ${accent} 45%, rgba(2,6,23,0.2) 75%)`,
              boxShadow: `0 0 14px 2px ${accent}66`,
              border: `1px solid ${accent}55`
            }}
          />
          <div className="absolute inset-0 rounded-full animate-pulse" style={{ boxShadow: `0 0 18px ${accent}44` }} />
        </div>
        <div className="leading-none">
          <p className="font-bold tracking-[0.22em] text-sm text-white" style={{ textShadow: `0 0 12px ${accent}` }}>
            J.A.R.V.I.S
          </p>
          <p className="text-[9px] tracking-[0.35em] text-cyan-300/60 mt-1" style={{ textShadow: '0 0 8px rgba(34,211,238,0.5)' }}>
            SYSTEM ONLINE
          </p>
        </div>
      </div>

      {/* Live state + connection */}
      <div className="hidden md:flex items-center gap-5 text-[10px] tracking-widest">
        <span className="hud-chip">
          <span
            className="w-1.5 h-1.5 rounded-full mr-1.5 inline-block"
            style={{ background: accent, boxShadow: `0 0 8px ${accent}` }}
          />
          {STATE_LABEL[state]}
        </span>
        <span className="hud-chip">
          <span className={`w-1.5 h-1.5 rounded-full mr-1.5 inline-block ${backendOnline ? 'hud-dot-on' : 'hud-dot-off'}`} />
          BACKEND {backendOnline ? 'ONLINE' : 'OFFLINE'}
        </span>
        <span className="hud-chip">
          <span className={`w-1.5 h-1.5 rounded-full mr-1.5 inline-block ${wsConnected ? 'hud-dot-on' : 'hud-dot-off'}`} />
          LINK {wsConnected ? 'UP' : 'DOWN'}
        </span>
        <LiveClock />
      </div>

      {/* Window controls */}
      <div className="flex items-center gap-1 pl-4 ml-auto" data-tauri-drag-region>
        {tauri && win ? (
          <>
            <button
              onClick={() => win.minimize()}
              className="hud-win-btn"
              aria-label="Minimize"
            >
              <svg width="10" height="10" viewBox="0 0 10 10"><line x1="1" y1="5" x2="9" y2="5" stroke="currentColor" strokeWidth="1.1" /></svg>
            </button>
            <button
              onClick={() => win.toggleMaximize().then(() => win.isMaximized().then(setIsMax).catch(() => {}))}
              className="hud-win-btn"
              aria-label="Maximize"
            >
              {isMax ? (
                <svg width="10" height="10" viewBox="0 0 10 10"><rect x="1.5" y="3.5" width="5" height="5" fill="none" stroke="currentColor" strokeWidth="1.1" /><path d="M3.5 3.5V1.5h5v5H6.5" stroke="currentColor" strokeWidth="1.1" fill="none" /></svg>
              ) : (
                <svg width="10" height="10" viewBox="0 0 10 10"><rect x="1.5" y="1.5" width="7" height="7" fill="none" stroke="currentColor" strokeWidth="1.1" /></svg>
              )}
            </button>
            <button
              onClick={() => win.close()}
              className="hud-win-btn hover:bg-red-500/80 hover:text-white"
              aria-label="Close"
            >
              <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 2l6 6M8 2l-6 6" stroke="currentColor" strokeWidth="1.1" /></svg>
            </button>
          </>
        ) : (
          <span className="text-[9px] tracking-[0.3em] text-cyan-300/40 mr-2">TAURI HOST</span>
        )}
      </div>
    </header>
  );
}

function LiveClock() {
  const [time, setTime] = useState('--:--:--');

  useEffect(() => {
    setTime(formatClock());
    const id = setInterval(() => setTime(formatClock()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <span className="hud-chip font-mono">
      <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mr-1.5 opacity-70">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 6v6l4 2" />
      </svg>
      {time}
    </span>
  );
}

function formatClock(): string {
  return new Date().toLocaleTimeString('en-GB', { hour12: false });
}
