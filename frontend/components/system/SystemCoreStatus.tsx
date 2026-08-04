'use client';

import { useSystemPoll, formatUptime } from './useSystemPoll';

interface SystemStatus {
  application?: string;
  brain_state?: string;
  uptime_seconds?: number;
  request_count?: number;
  error_count?: number;
}

interface SystemHealth {
  status?: string;
  core?: string;
  ai?: string;
  online_modules?: number;
  total_modules?: number;
}

const statusColor = (status?: string) => {
  switch (status) {
    case 'ONLINE':
      return 'bg-green-500';
    case 'DEGRADED':
      return 'bg-amber-500';
    case 'OFFLINE':
      return 'bg-red-500';
    case 'ERROR':
      return 'bg-red-500';
    case 'NOT_CONFIGURED':
      return 'bg-gray-500';
    default:
      return 'bg-gray-400';
  }
};

export default function SystemCoreStatus() {
  const { data: status, error: statusError } = useSystemPoll<SystemStatus>('/api/system/status', 10000);
  const { data: health, error: healthError } = useSystemPoll<SystemHealth>('/api/system/health', 10000);

  const appStatus = status?.application ?? health?.status ?? 'OFFLINE';
  const offline = statusError || healthError;

  return (
    <div className="glass-card p-4 rounded-lg space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-jarvis-800 dark:text-jarvis-200">Core Status</h3>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full animate-pulse ${offline ? 'bg-red-500' : statusColor(appStatus)}`}></div>
          <span className="text-xs text-gray-500 dark:text-gray-400">{offline ? 'Offline' : appStatus}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="rounded-md bg-gray-100 dark:bg-gray-800/60 p-2">
          <p className="text-xs text-gray-500 dark:text-gray-400">Brain State</p>
          <p className="font-medium text-jarvis-800 dark:text-jarvis-200 capitalize">{status?.brain_state ?? '—'}</p>
        </div>
        <div className="rounded-md bg-gray-100 dark:bg-gray-800/60 p-2">
          <p className="text-xs text-gray-500 dark:text-gray-400">Uptime</p>
          <p className="font-medium text-jarvis-800 dark:text-jarvis-200">{formatUptime(status?.uptime_seconds ?? 0)}</p>
        </div>
        <div className="rounded-md bg-gray-100 dark:bg-gray-800/60 p-2">
          <p className="text-xs text-gray-500 dark:text-gray-400">Requests</p>
          <p className="font-medium text-jarvis-800 dark:text-jarvis-200">{status?.request_count ?? 0}</p>
        </div>
        <div className="rounded-md bg-gray-100 dark:bg-gray-800/60 p-2">
          <p className="text-xs text-gray-500 dark:text-gray-400">Errors</p>
          <p className={`font-medium ${(status?.error_count ?? 0) > 0 ? 'text-red-500' : 'text-jarvis-800 dark:text-jarvis-200'}`}>{status?.error_count ?? 0}</p>
        </div>
      </div>

      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
        <span className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${statusColor(health?.core)}`}></span> Core: {health?.core ?? '—'}
        </span>
        <span className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${statusColor(health?.ai)}`}></span> AI: {health?.ai ?? '—'}
        </span>
        <span>Modules: {health?.online_modules ?? 0}/{health?.total_modules ?? 0}</span>
      </div>
    </div>
  );
}
