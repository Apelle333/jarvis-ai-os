'use client';

import { useSystemPoll } from './useSystemPoll';

interface OllamaStatus {
  server_running?: boolean;
  server_url?: string;
  model_names?: string[];
  loaded_models?: string[];
  error?: string | null;
}

export default function ModelMonitor() {
  const { data } = useSystemPoll<OllamaStatus>('/api/system/ollama', 15000);

  const running = data?.server_running;
  const loaded = data?.loaded_models ?? [];

  return (
    <div className="glass-card p-4 rounded-lg space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-jarvis-800 dark:text-jarvis-200">AI Models</h3>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full animate-pulse ${running ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-xs text-gray-500 dark:text-gray-400">{running ? 'Ollama Online' : 'Offline'}</span>
        </div>
      </div>

      {!running && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {data?.error ?? 'Ollama server not reachable'}
        </p>
      )}

      {running && (
        <>
          <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate">{data?.server_url}</p>

          {loaded.length > 0 && (
            <div className="rounded-md bg-green-50 dark:bg-green-900/20 p-2">
              <p className="text-[10px] uppercase tracking-wider text-green-600 dark:text-green-400 mb-1">Loaded Now</p>
              <div className="flex flex-wrap gap-1">
                {loaded.map((m) => (
                  <span key={m} className="text-[11px] px-1.5 py-0.5 rounded bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300">
                    {m}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div>
            <p className="text-[10px] uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">
              Installed ({data?.model_names?.length ?? 0})
            </p>
            <div className="space-y-1">
              {(data?.model_names ?? []).map((name) => (
                <div key={name} className="flex items-center justify-between text-sm">
                  <span className="text-jarvis-800 dark:text-jarvis-200 truncate">{name}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
