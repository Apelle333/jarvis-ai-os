'use client';

import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';

export const DEFAULT_BACKEND_URL = 'http://localhost:8000';

export const getBackendUrl = () =>
  (process.env.NEXT_PUBLIC_BACKEND_URL || DEFAULT_BACKEND_URL).replace(/\/$/, '');

export const getWebSocketUrl = () => {
  const base = getBackendUrl().replace(/^http/, 'ws');
  const clientId = `web_${Math.random().toString(36).substr(2, 10)}`;
  return `${base}/ws/${clientId}`;
};

interface JarvisContextType {
  isListening: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  setListening: (state: boolean) => void;
  setProcessing: (state: boolean) => void;
  setSpeaking: (state: boolean) => void;
  voiceText: string;
  setVoiceText: (text: string) => void;
  backendUrl: string;
  backendOnline: boolean;
  wsConnected: boolean;
  status: Record<string, unknown> | null;
}

const JarvisContext = createContext<JarvisContextType | undefined>(undefined);

export const JarvisProvider = ({ children }: { children: React.ReactNode }) => {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceText, setVoiceText] = useState('');
  const [backendOnline, setBackendOnline] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const backendUrl = getBackendUrl();

  const setListening = useCallback((state: boolean) => {
    setIsListening(state);
  }, []);

  const setProcessing = useCallback((state: boolean) => {
    setIsProcessing(state);
  }, []);

  const setSpeaking = useCallback((state: boolean) => {
    setIsSpeaking(state);
  }, []);

  useEffect(() => {
    let disposed = false;

    const checkHealth = async () => {
      try {
        const res = await fetch(`${backendUrl}/health`);
        const data = await res.json();
        if (!disposed) setBackendOnline(data?.status === 'healthy');
      } catch {
        if (!disposed) setBackendOnline(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);

    return () => {
      disposed = true;
      clearInterval(interval);
    };
  }, [backendUrl]);

  useEffect(() => {
    let disposed = false;
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      if (disposed) return;
      try {
        ws = new WebSocket(getWebSocketUrl());
        wsRef.current = ws;

        ws.onopen = () => {
          if (!disposed) setWsConnected(true);
          ws?.send(JSON.stringify({ type: 'get_status' }));
        };

        ws.onmessage = (event) => {
          if (disposed) return;
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'status') setStatus(msg);
          } catch {
            // ignore non-JSON frames
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          wsRef.current = null;
          if (!disposed) {
            reconnectTimer = setTimeout(connect, 5000);
          }
        };

        ws.onerror = () => {
          ws?.close();
        };
      } catch {
        if (!disposed) reconnectTimer = setTimeout(connect, 5000);
      }
    };

    connect();

    return () => {
      disposed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      ws?.close();
      wsRef.current = null;
    };
  }, [backendUrl]);

  return (
    <JarvisContext.Provider
      value={{
        isListening,
        isProcessing,
        isSpeaking,
        setListening,
        setProcessing,
        setSpeaking,
        voiceText,
        setVoiceText,
        backendUrl,
        backendOnline,
        wsConnected,
        status
      }}
    >
      {children}
    </JarvisContext.Provider>
  );
};

export const useJarvis = () => {
  const context = useContext(JarvisContext);
  if (context === undefined) {
    throw new Error('useJarvis must be used within a JarvisProvider');
  }
  return context;
};
