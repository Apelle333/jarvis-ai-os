'use client';

import { useSystemPoll } from './useSystemPoll';

interface Module {
  name?: string;
  category?: string;
  status?: string;
  detail?: string;
}

interface ModulesResponse {
  modules?: Module[];
  summary?: {
    total?: number;
    online?: number;
    offline?: number;
  };
}

const statusDot = (status?: string) => {
  switch (status) {
    case 'ONLINE':
      return 'bg-green-500 shadow-[0_0_6px_2px_rgba(34,197,94,0.6)]';
    case 'ERROR':
      return 'bg-red-500 shadow-[0_0_6px_2px_rgba(239,68,68,0.6)]';
    case 'NOT_CONFIGURED':
      return 'bg-gray-500';
    default:
      return 'bg-red-400 shadow-[0_0_6px_2px_rgba(248,113,113,0.5)]';
  }
};

export default function ModuleGrid() {
  const { data } = useSystemPoll<ModulesResponse>('/api/system/modules', 15000);

  const modules = data?.modules ?? [];
  const categories = Array.from(new Set(modules.map((m) => m.category ?? 'Other')));

  return (
    <div className="glass-card p-4 rounded-lg space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-jarvis-800 dark:text-jarvis-200">Modules</h3>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {data?.summary?.online ?? 0}/{data?.summary?.total ?? 0} online
        </span>
      </div>

      {modules.length === 0 && (
        <p className="text-sm text-gray-500 dark:text-gray-400">No module data available.</p>
      )}

      {categories.map((cat) => (
        <div key={cat}>
          <p className="text-[10px] uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">{cat}</p>
          <div className="grid grid-cols-2 gap-2">
            {modules
              .filter((m) => (m.category ?? 'Other') === cat)
              .map((m, i) => (
                <div
                  key={`${m.name}-${i}`}
                  className="rounded-md bg-gray-100 dark:bg-gray-800/60 p-2 flex items-start space-x-2"
                >
                  <span className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${statusDot(m.status)}`}></span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-jarvis-800 dark:text-jarvis-200 truncate">{m.name ?? '—'}</p>
                    <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate">{m.detail ?? m.status ?? ''}</p>
                  </div>
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
