'use client';

import { motion } from 'framer-motion';
import { useSystemPoll, formatUptime } from '@/components/system/useSystemPoll';

interface Snapshot {
  brain_state?: string;
  cpu_percent?: number;
  memory_percent?: number;
  disk_percent?: number;
  gpu_available?: boolean;
  gpu?: {
    name?: string;
    utilization_percent?: number;
    memory_used_mb?: number;
    memory_total_mb?: number;
    temperature_c?: number;
  };
  processes_total?: number;
}

interface Status {
  uptime_seconds?: number;
  request_count?: number;
  error_count?: number;
}

function Meter({ label, value, suffix = '%' }: { label: string; value: number; suffix?: string }) {
  const v = Math.min(Math.max(value || 0, 0), 100);
  return (
    <div className="mb-2.5">
      <div className="flex justify-between items-baseline mb-1">
        <span className="hud-label">{label}</span>
        <span className="hud-value">
          {Math.round(v)}
          {suffix}
        </span>
      </div>
      <div className="h-1 bg-white/5 rounded overflow-hidden">
        <div
          className="h-full rounded"
          style={{
            width: `${v}%`,
            background: `linear-gradient(90deg, rgba(14,165,233,0.4), #22d3ee)`,
            boxShadow: '0 0 8px rgba(34,211,238,0.7)'
          }}
        />
      </div>
    </div>
  );
}

/**
 * Minimal left-hand system status HUD. Live numbers from the real backend.
 */
export default function SystemHUD() {
  const { data: snap, error: snapError } = useSystemPoll<Snapshot>('/api/system/snapshot', 3000);
  const { data: status } = useSystemPoll<Status>('/api/system/status', 10000);

  const gpu = snap?.gpu;
  const state = snap?.brain_state ?? 'idle';

  return (
    <motion.aside
      initial={{ opacity: 0, x: -24 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.7, ease: 'easeOut' }}
      className="fixed left-4 top-1/2 -translate-y-1/2 z-30 w-52 hidden md:block"
    >
      <div className="hud-panel p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="hud-panel-title">SYSTEM</h2>
          <span className={`hud-state-dot ${snapError ? 'hud-dot-off' : 'hud-dot-on'}`} />
        </div>

        <div className="flex justify-between items-baseline mb-3">
          <span className="hud-label">BRAIN</span>
          <span className="text-[10px] tracking-[0.25em] text-cyan-300/80 uppercase">{state}</span>
        </div>
        <div className="flex justify-between items-baseline mb-3">
          <span className="hud-label">UPTIME</span>
          <span className="hud-value">{formatUptime(status?.uptime_seconds ?? 0)}</span>
        </div>

        <div className="my-3 hud-divider" />

        <Meter label="CPU" value={snap?.cpu_percent ?? 0} />
        <Meter label="RAM" value={snap?.memory_percent ?? 0} />
        <Meter label="DISK" value={snap?.disk_percent ?? 0} />

        {gpu && (
          <div className="mt-1">
            <div className="flex justify-between items-baseline mb-1">
              <span className="hud-label truncate">{gpu.name || 'GPU'}</span>
              <span className="hud-value">{Math.round(gpu.utilization_percent ?? 0)}%</span>
            </div>
            <div className="h-1 bg-white/5 rounded overflow-hidden">
              <div
                className="h-full rounded"
                style={{
                  width: `${Math.min(gpu.utilization_percent ?? 0, 100)}%`,
                  background: 'linear-gradient(90deg, rgba(59,130,246,0.4), #60a5fa)',
                  boxShadow: '0 0 8px rgba(96,165,250,0.7)'
                }}
              />
            </div>
            <p className="text-[9px] text-cyan-300/50 mt-1 tracking-wider">
              {Math.round(gpu.memory_used_mb ?? 0)}/{Math.round(gpu.memory_total_mb ?? 0)}MB · {Math.round(gpu.temperature_c ?? 0)}°C
            </p>
          </div>
        )}

        <div className="my-3 hud-divider" />

        <div className="flex justify-between items-baseline mb-1">
          <span className="hud-label">REQUESTS</span>
          <span className="hud-value">{status?.request_count ?? 0}</span>
        </div>
        <div className="flex justify-between items-baseline mb-1">
          <span className="hud-label">ERRORS</span>
          <span className={`hud-value ${(status?.error_count ?? 0) > 0 ? 'text-rose-400' : ''}`}>{status?.error_count ?? 0}</span>
        </div>
        <div className="flex justify-between items-baseline">
          <span className="hud-label">PROCESSES</span>
          <span className="hud-value">{snap?.processes_total ?? 0}</span>
        </div>
      </div>
    </motion.aside>
  );
}
