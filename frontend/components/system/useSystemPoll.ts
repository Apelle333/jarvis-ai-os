'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useJarvis } from '@/context/JarvisContext';

export function useSystemPoll<T>(path: string, interval = 5000): { data: T | null; error: boolean } {
  const { backendUrl } = useJarvis();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState(false);
  const lastErrorRef = useRef<string | null>(null);

  const fetchData = useCallback(async () => {
    if (typeof document !== 'undefined' && document.hidden) return;

    try {
      const res = await fetch(`${backendUrl}${path}`);
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const json: T = await res.json();
      setData(json);
      setError(false);
      lastErrorRef.current = null;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      if (lastErrorRef.current !== message) {
        console.warn(`Failed to fetch ${path}: ${message}`);
        lastErrorRef.current = message;
      }
      setError(true);
    }
  }, [backendUrl, path]);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, interval);
    const onVisibilityChange = () => {
      if (!document.hidden) void fetchData();
    };

    document.addEventListener('visibilitychange', onVisibilityChange);

    return () => {
      clearInterval(id);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
  }, [fetchData, interval]);

  return { data, error };
}

export const formatUptime = (seconds: number): string => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':');
};
