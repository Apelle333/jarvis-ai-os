'use client';

import { useSystemPoll } from './useSystemPoll';

interface Agent {
  name?: string;
  agent_type?: string;
  status?: string;
  detail?: string;
  specializations?: string[];
}

interface AgentsResponse {
  agents?: Agent[];
  active?: number;
}

const statusColor = (status?: string) => {
  switch (status) {
    case 'ONLINE':
      return 'text-green-500';
    case 'ERROR':
      return 'text-red-500';
    case 'NOT_CONFIGURED':
      return 'text-gray-400';
    default:
      return 'text-amber-500';
  }
};

export default function AgentMonitor() {
  const { data } = useSystemPoll<AgentsResponse>('/api/system/agents', 15000);

  const agents = data?.agents ?? [];
  const active = data?.active ?? 0;

  return (
    <div className="glass-card p-4 rounded-lg space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-jarvis-800 dark:text-jarvis-200">Agents</h3>
        <span className="text-xs text-gray-500 dark:text-gray-400">{active}/{agents.length} active</span>
      </div>

      {agents.length === 0 && (
        <p className="text-sm text-gray-500 dark:text-gray-400">No agents registered.</p>
      )}

      <div className="space-y-2">
        {agents.map((a) => (
          <div key={a.name ?? a.agent_type} className="rounded-md bg-gray-100 dark:bg-gray-800/60 p-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-jarvis-800 dark:text-jarvis-200">{a.name ?? 'Agent'}</span>
              <span className={`text-xs font-medium ${statusColor(a.status)}`}>{a.status ?? '—'}</span>
            </div>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">{a.agent_type ?? ''} · {a.detail ?? ''}</p>
            {a.specializations && a.specializations.length > 0 && (
              <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-1 truncate">
                {a.specializations.slice(0, 4).join(', ')}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
