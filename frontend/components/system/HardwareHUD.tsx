'use client';

import { useSystemPoll } from './useSystemPoll';

interface HardwareInfo {
  cpu?: {
    usage_percent?: number;
    cores?: number;
    frequency_mhz?: number;
  };
  gpu?: {
    available?: boolean;
  };
  gpu_summary?: {
    name?: string;
    utilization_percent?: number;
    memory_used_mb?: number;
    memory_total_mb?: number;
    temperature_c?: number;
  };
  memory?: {
    percent?: number;
    used_human?: string;
    total_human?: string;
  };
  disk?: {
    percent?: number;
    free_human?: string;
  };
}

function Meter({ label, value, colorClass }: { label: string; value: number; colorClass: string }) {
  return (
    <div>
      <div className="flex items-center justify-between text-sm mb-1">
        <span className="text-gray-500 dark:text-gray-400">{label}</span>
        <span className="font-medium text-jarvis-800 dark:text-jarvis-200">{Math.round(value)}%</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
        <div
          className={`h-full ${colorClass} rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={100}
        ></div>
      </div>
    </div>
  );
}

export default function HardwareHUD() {
  const { data, error } = useSystemPoll<HardwareInfo>('/api/system/hardware', 3000);

  const cpu = data?.cpu;
  const mem = data?.memory;
  const disk = data?.disk;
  const gpu = data?.gpu_summary;

  return (
    <div className="glass-card p-4 rounded-lg space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-jarvis-800 dark:text-jarvis-200">Hardware</h3>
        <span className={`text-xs ${error ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'}`}>
          {error ? 'Unavailable' : 'Live'}
        </span>
      </div>

      <div className="space-y-3">
        <Meter label={`CPU (${cpu?.cores ?? '—'} cores @ ${Math.round(cpu?.frequency_mhz ?? 0)} MHz)`} value={cpu?.usage_percent ?? 0} colorClass="bg-jarvis-500" />
        <Meter label={`RAM (${mem?.used_human ?? '—'} / ${mem?.total_human ?? '—'})`} value={mem?.percent ?? 0} colorClass="bg-jarvis-400" />
        <Meter label={`Disk (${disk?.free_human ?? '—'} free)`} value={disk?.percent ?? 0} colorClass="bg-jarvis-300" />
      </div>

      {gpu ? (
        <div className="rounded-md bg-gray-100 dark:bg-gray-800/60 p-3 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-jarvis-800 dark:text-jarvis-200">{gpu.name ?? 'GPU'}</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">{gpu.temperature_c?.toFixed(0)}°C</span>
          </div>
          <Meter label="GPU Utilization" value={gpu.utilization_percent ?? 0} colorClass="bg-jarvis-600" />
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {Math.round(gpu.memory_used_mb ?? 0)} / {Math.round(gpu.memory_total_mb ?? 0)} MB VRAM
          </p>
        </div>
      ) : (
        <p className="text-sm text-gray-500 dark:text-gray-400">GPU: not detected</p>
      )}
    </div>
  );
}
