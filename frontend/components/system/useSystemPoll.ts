'use client';

import { useState, useEffect, useCallback } from 'react';
import { useJarvis } from '@/context/JarvisContext';

export function useSystemPoll<T>(path: string, interval = 5000): { data: T | null; error: boolean } {
  const { backendUrl } = useJarvis();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${backendUrl}${path}`);
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const json: T = await res.json();
      setData(json);
      setError(false);
    } catch (err) {
      console.error(`Failed to fetch ${path}:`, err);
      setError(true);
    }
  }, [backendUrl, path]);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, interval);
    return () => clearInterval(id);
  }, [fetchData, interval]);

  return { data, error };
}

export const formatUptime = (seconds: number): string => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':');
};
