'use client';

import { useState, useEffect } from 'react';
import { useJarvis } from '@/context/JarvisContext';

interface SystemInfo {
  cpu: number;
  memory: number;
  disk: number;
  uptime: string;
  temperature: number | null;
  network: {
    upload: number;
    download: number;
  };
}

const formatUptime = (seconds: number): string => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':');
};

export default function SystemPanel() {
  const { backendUrl, backendOnline } = useJarvis();
  const [systemInfo, setSystemInfo] = useState<SystemInfo>({
    cpu: 0,
    memory: 0,
    disk: 0,
    uptime: '00:00:00',
    temperature: null,
    network: {
      upload: 0,
      download: 0
    }
  });
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchSystemStats = async () => {
      try {
        const res = await fetch(`${backendUrl}/api/chat/status`);
        if (!res.ok) throw new Error(`Backend returned ${res.status}`);
        const data = await res.json();

        const stats = data?.brain?.system_stats?.data;
        const brain = data?.brain;

        setSystemInfo({
          cpu: Math.round(stats?.cpu?.usage ?? 0),
          memory: Math.round(stats?.memory?.percent ?? 0),
          disk: Math.round(stats?.disk?.percent ?? 0),
          uptime: formatUptime(brain?.uptime_seconds ?? 0),
          temperature: null,
          network: {
            upload: Math.round((stats?.network?.bytes_sent ?? 0) / (1024 * 1024)),
            download: Math.round((stats?.network?.bytes_recv ?? 0) / (1024 * 1024))
          }
        });
        setError(false);
      } catch (err) {
        console.error('Failed to fetch system stats:', err);
        setError(true);
      }
    };

    fetchSystemStats();
    const interval = setInterval(fetchSystemStats, 5000);

    return () => clearInterval(interval);
  }, [backendUrl]);

  return (
    <div className="glass-card p-4 rounded-lg space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold text-jarvis-800 dark:text-jarvis-200">System Status</h3>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full animate-pulse ${backendOnline && !error ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-xs text-gray-500 dark:text-gray-400">{backendOnline && !error ? 'Online' : 'Offline'}</span>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span>CPU Usage</span>
          <span className="font-medium">{systemInfo.cpu}%</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
          <div
            className="h-full bg-jarvis-500 rounded-full transition-all duration-500"
            style={{ width: `${systemInfo.cpu}%` }}
            role="progressbar"
            aria-valuenow={systemInfo.cpu}
            aria-valuemin={0}
            aria-valuemax={100}
          ></div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span>Memory Usage</span>
          <span className="font-medium">{systemInfo.memory}%</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
          <div
            className="h-full bg-jarvis-400 rounded-full transition-all duration-500"
            style={{ width: `${systemInfo.memory}%` }}
            role="progressbar"
            aria-valuenow={systemInfo.memory}
            aria-valuemin={0}
            aria-valuemax={100}
          ></div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span>Disk Usage</span>
          <span className="font-medium">{systemInfo.disk}%</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
          <div
            className="h-full bg-jarvis-300 rounded-full transition-all duration-500"
            style={{ width: `${systemInfo.disk}%` }}
            role="progressbar"
            aria-valuenow={systemInfo.disk}
            aria-valuemin={0}
            aria-valuemax={100}
          ></div>
        </div>

        {systemInfo.temperature !== null && (
          <div className="flex items-center justify-between text-sm">
            <span>Temperature</span>
            <span className="font-medium">{systemInfo.temperature}°C</span>
          </div>
        )}

        <div className="border-t border-gray-200 dark:border-gray-600 pt-3 mt-2 space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Network</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              ↑ {systemInfo.network.upload} MB ↓ {systemInfo.network.download} MB
            </span>
          </div>
          <div className="flex h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-jarvis-200"
              style={{ width: `${Math.min((systemInfo.network.upload / 1024) * 100, 100)}%` }}
            ></div>
          </div>
          <div className="flex h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mt-1">
            <div
              className="h-full bg-jarvis-400"
              style={{ width: `${Math.min((systemInfo.network.download / 4096) * 100, 100)}%` }}
            ></div>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
          <span>JARVIS Uptime</span>
          <span className="font-medium">{systemInfo.uptime}</span>
        </div>
      </div>
    </div>
  );
}
