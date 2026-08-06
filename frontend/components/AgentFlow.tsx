'use client';

import { motion } from 'framer-motion';
import { useSystemPoll } from '@/components/system/useSystemPoll';

interface Agent {
  name?: string;
  agent_type?: string;
  status?: string;
  detail?: string;
}

interface AgentsResponse {
  agents?: Agent[];
  active?: number;
}

/**
 * Right-hand agent matrix. Live agent roster from the real swarm.
 */
export default function AgentFlow() {
  const { data } = useSystemPoll<AgentsResponse>('/api/system/agents', 15000);
  const { agentState } = useJarvis();

  // Prefer live websocket agentState when available
  const agents = agentState?.agents ?? data?.agents ?? [];
  const active = agentState?.active ?? data?.active ?? 0;

  return (
    <motion.aside
      initial={{ opacity: 0, x: 24 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.7, ease: 'easeOut', delay: 0.1 }}
      className="fixed right-4 top-1/2 -translate-y-1/2 z-30 w-60 hidden md:block"
    >
      <div className="hud-panel p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="hud-panel-title">AGENT MATRIX</h2>
          <span className="text-[10px] tracking-widest text-cyan-300/70">
            {active}/{agents.length} <span className="text-cyan-300/40">ONLINE</span>
          </span>
        </div>

        <div className="relative">
          {/* flow spine */}
          <div className="absolute left-[3px] top-1 bottom-1 w-px bg-gradient-to-b from-cyan-400/60 via-cyan-400/20 to-cyan-400/60" />
          {/* traveling pulse */}
          <motion.div
            className="absolute left-[3px] w-px h-3 bg-cyan-300"
            animate={{ top: ['10%', '90%'] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
            style={{ boxShadow: '0 0 10px #22d3ee' }}
          />

          <div className="space-y-2.5">
            {agents.length === 0 && (
              <p className="text-[10px] tracking-widest text-cyan-300/40 pl-3">NO AGENTS REGISTERED</p>
            )}
            {agents.map((agent, i) => (
              <motion.div
                key={agent.name ?? i}
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15 + i * 0.08, duration: 0.4 }}
                className="flex items-start gap-3 pl-3 relative"
              >
                <span className="mt-1 w-1.5 h-1.5 rounded-full flex-shrink-0 hud-dot-on" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between gap-2">
                    <p className="text-[11px] font-medium tracking-wider text-white/90 truncate">
                      {agent.name ?? 'AGENT'}
                    </p>
                  </div>
                  <p className="text-[9px] tracking-widest text-cyan-300/50 uppercase truncate mt-0.5">
                    {(agent.agent_type ?? 'specialist').replace(/_/g, ' ')}
                  </p>
                </div>
                <span className="text-[9px] tracking-widest text-emerald-300/70 flex-shrink-0 mt-0.5">ACTIVE</span>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="my-3 hud-divider" />

        <div className="flex items-center justify-between">
          <span className="hud-label">SWARM</span>
          <span className="text-[10px] tracking-widest text-cyan-300/70">SYNCED</span>
        </div>
      </div>
    </motion.aside>
  );
}
