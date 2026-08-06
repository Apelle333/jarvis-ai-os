'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useJarvis } from '@/context/JarvisContext';

interface ShortTerm {
  conversations_count?: number;
  conversations_active?: number;
  events_count?: number;
  tasks_count?: number;
  preferences_count?: number;
  database_size_mb?: number;
}

interface LongTerm {
  total_count?: number;
}

interface MemoryStatus {
  is_initialized?: boolean;
  short_term?: ShortTerm;
  long_term?: LongTerm;
  last_consolidation?: string | null;
}

type FeedKind = 'MEM' | 'EVT' | 'TASK' | 'VEC' | 'SYNC' | 'PREFS';

interface FeedEntry {
  id: number;
  kind: FeedKind;
  text: string;
  time: string;
}

const KIND_LABEL: Record<FeedKind, string> = {
  MEM: 'MEMORY',
  EVT: 'EVENT',
  TASK: 'TASK',
  VEC: 'VECTOR',
  SYNC: 'SYNC',
  PREFS: 'PREF'
};

const KIND_COLOR: Record<FeedKind, string> = {
  MEM: '#22d3ee',
  EVT: '#60a5fa',
  TASK: '#818cf8',
  VEC: '#34d399',
  SYNC: '#94a3b8',
  PREFS: '#fbbf24'
};

const now = (): string =>
  new Date().toLocaleTimeString('en-GB', { hour12: false });

const timeAgo = (iso?: string | null): string => {
  if (!iso) return 'NEVER';
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s AGO`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m AGO`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h AGO`;
};

/**
 * Memory activity feed. Polls the real memory subsystem and turns the observed
 * deltas into a scrolling holographic log stream.
 */
export default function MemoryFeed() {
  const { backendUrl, memoryState } = useJarvis();
  const [memory, setMemory] = useState<MemoryStatus | null>(memoryState ?? null);
  const [feed, setFeed] = useState<FeedEntry[]>([]);
  const seq = useRef(0);
  const prev = useRef<ShortTerm | null>(null);
  const prevLong = useRef<number | null>(null);

  useEffect(() => {
    let disposed = false;

    const push = (kind: FeedKind, text: string) => {
      if (disposed) return;
      seq.current += 1;
      setFeed((entries) =>
        [{ id: seq.current, kind, text, time: now() }, ...entries].slice(0, 9)
      );
    };

    const poll = async () => {
      try {
        // If websocket provided memoryState, use it and skip HTTP poll
        if (memoryState) {
          setMemory(memoryState);
          return;
        }
        const res = await fetch(`${backendUrl}/api/system/memory`);
        if (!res.ok) throw new Error(`Backend returned ${res.status}`);
        const json: MemoryStatus = await res.json();
        if (disposed) return;
        setMemory(json);

        const st = json.short_term ?? {};
        const ltTotal = json.long_term?.total_count ?? null;

        if (prev.current) {
          if ((st.conversations_count ?? 0) > (prev.current.conversations_count ?? 0)) {
            push('MEM', 'CONVERSATION PERSISTED');
          }
          if ((st.events_count ?? 0) > (prev.current.events_count ?? 0)) {
            push('EVT', 'EVENT RECORDED');
          }
          if ((st.tasks_count ?? 0) > (prev.current.tasks_count ?? 0)) {
            push('TASK', 'TASK LOGGED');
          }
          if ((st.preferences_count ?? 0) > (prev.current.preferences_count ?? 0)) {
            push('PREFS', 'PREFERENCE UPDATED');
          }
        }
        if (prevLong.current !== null && ltTotal !== null && ltTotal > prevLong.current) {
          push('VEC', `VECTOR INDEX +${ltTotal - prevLong.current}`);
        }
        if (prev.current === null) {
          push('SYNC', 'MEMORY CORE LINKED');
        }

        prev.current = st;
        prevLong.current = ltTotal;
      } catch {
        if (!disposed) push('SYNC', 'MEMORY LINK OFFLINE');
      }
    };

    poll();
    const id = setInterval(poll, 8000);
    return () => {
      disposed = true;
      clearInterval(id);
    };
  }, [backendUrl]);

  const st = memory?.short_term ?? {};

  return (
    <motion.aside
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: 'easeOut', delay: 0.15 }}
      className="fixed bottom-6 left-4 z-30 w-60 hidden lg:block"
    >
      <div className="hud-panel p-3.5">
        <div className="flex items-center justify-between mb-2.5">
          <h2 className="hud-panel-title">MEMORY ACTIVITY</h2>
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{
              background: memory ? '#34d399' : 'rgba(248,113,113,0.6)',
              boxShadow: memory ? '0 0 8px rgba(52,211,153,0.9)' : 'none'
            }}
          />
        </div>

        {/* Memory cores */}
        <div className="grid grid-cols-2 gap-2 mb-2.5">
          <div className="hud-mini-cell">
            <span className="hud-label">SHORT-TERM</span>
            <span className="hud-value text-[10px]">{st.conversations_count ?? 0} CONV</span>
            <span className="hud-micro">
              {st.database_size_mb ?? 0}MB · {st.events_count ?? 0} EVT · {st.tasks_count ?? 0} TSK
            </span>
          </div>
          <div className="hud-mini-cell">
            <span className="hud-label">VECTOR</span>
            <span className="hud-value text-[10px]">{memory?.long_term?.total_count ?? 0} VEC</span>
            <span className="hud-micro">CONSOL {timeAgo(memory?.last_consolidation)}</span>
          </div>
        </div>

        {/* Activity stream */}
        <div className="relative h-28 overflow-hidden">
          <div className="absolute left-0 top-0 bottom-0 w-px bg-gradient-to-b from-cyan-400/50 via-cyan-400/15 to-transparent" />
          <AnimatePresence initial={false}>
            {feed.map((entry, i) => (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: i * 0.02 }}
                className="flex items-center gap-2 pl-3 py-0.5"
              >
                <span
                  className="w-1 h-1 rounded-full flex-shrink-0"
                  style={{ background: KIND_COLOR[entry.kind], boxShadow: `0 0 6px ${KIND_COLOR[entry.kind]}` }}
                />
                <span
                  className="text-[8px] tracking-[0.25em] flex-shrink-0"
                  style={{ color: KIND_COLOR[entry.kind] }}
                >
                  {KIND_LABEL[entry.kind]}
                </span>
                <span className="text-[9px] tracking-wider text-cyan-100/80 truncate flex-1">
                  {entry.text}
                </span>
                <span className="text-[8px] tracking-widest text-cyan-300/40 flex-shrink-0">
                  {entry.time}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
          {feed.length === 0 && (
            <p className="text-[9px] tracking-[0.3em] text-cyan-300/40 pl-3 pt-1">AWAITING TELEMETRY...</p>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
