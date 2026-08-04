'use client';

import { AnimatePresence, motion } from 'framer-motion';
import AppScene from '@/components/AppScene';
import TitleBar from '@/components/TitleBar';
import SystemHUD from '@/components/SystemHUD';
import AgentFlow from '@/components/AgentFlow';
import MemoryFeed from '@/components/MemoryFeed';
import FloatingCommandBar from '@/components/FloatingCommandBar';
import { useJarvisVisualState, STATE_COLOR, STATE_LABEL } from '@/lib/jarvisState';

export default function Home() {
  const state = useJarvisVisualState();
  const accent = STATE_COLOR[state];

  return (
    <div className="relative h-screen w-screen overflow-hidden hud-root">
      {/* CSS nebula backdrop (WebGL canvas sits transparent above it) */}
      <div className="hud-nebula fixed inset-0" />

      {/* Holographic WebGL scene */}
      <AppScene />

      {/* Scanlines + vignette */}
      <div className="hud-scanlines fixed inset-0 z-[5] pointer-events-none" />
      <div className="hud-vignette fixed inset-0 z-[6] pointer-events-none" />

      {/* Custom title bar / identity / connection */}
      <TitleBar />

      {/* Left: system status */}
      <SystemHUD />

      {/* Bottom-left: memory activity feed */}
      <MemoryFeed />

      {/* Right: agents */}
      <AgentFlow />

      {/* Core state readout */}
      <div className="fixed left-1/2 -translate-x-1/2 top-[63%] z-20 text-center pointer-events-none">
        <AnimatePresence mode="wait">
          <motion.div
            key={state}
            initial={{ opacity: 0, y: 8, filter: 'blur(6px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            exit={{ opacity: 0, y: -8, filter: 'blur(6px)' }}
            transition={{ duration: 0.35 }}
          >
            <p
              className="text-[11px] tracking-[0.5em] font-semibold"
              style={{ color: accent, textShadow: `0 0 16px ${accent}` }}
            >
              {STATE_LABEL[state]}
            </p>
            <p className="mt-1 text-[9px] tracking-[0.4em] text-cyan-200/40">
              CORE LINK ACTIVE
            </p>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Bottom: command interface */}
      <FloatingCommandBar />
    </div>
  );
}
