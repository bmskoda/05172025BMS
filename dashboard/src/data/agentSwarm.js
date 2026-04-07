export const agentsByRole = [
  { role: 'SEAL Team 6', code: 'SEAL', agents: 12, tasks: 4821, replications: 34, merges: 8, color: '#06b6d4' },
  { role: 'Delta Force', code: 'DELTA', agents: 9, tasks: 3912, replications: 28, merges: 6, color: '#ef4444' },
  { role: '75th Rangers', code: 'RANGER', agents: 11, tasks: 5234, replications: 41, merges: 11, color: '#10b981' },
  { role: 'Marine Recon', code: 'MARINE', agents: 8, tasks: 3456, replications: 22, merges: 5, color: '#f97316' },
  { role: 'Top Gun Strategy', code: 'TOP_GUN', agents: 7, tasks: 2891, replications: 19, merges: 4, color: '#eab308' },
  { role: 'CIA/DIA Intel', code: 'INTELLIGENCE', agents: 10, tasks: 6723, replications: 52, merges: 14, color: '#8b5cf6' },
  { role: 'USCYBERCOM', code: 'CYBER', agents: 9, tasks: 5891, replications: 45, merges: 12, color: '#ec4899' },
  { role: 'DOJ Prosecution', code: 'PROSECUTOR', agents: 8, tasks: 4123, replications: 31, merges: 7, color: '#14b8a6' },
  { role: 'Hollywood Crew', code: 'HOLLYWOOD', agents: 7, tasks: 2341, replications: 16, merges: 3, color: '#f59e0b' },
];

export const lifecycleEvents = [
  { time: '08:00:00', event: 'Initial 9 agents deployed', type: 'deploy' },
  { time: '08:15:23', event: 'INTEL agent replicated (context 33%)', type: 'replicate' },
  { time: '08:32:45', event: 'CYBER agent replicated (context 33%)', type: 'replicate' },
  { time: '09:01:12', event: '3 RANGER agents merged (context 66%)', type: 'merge' },
  { time: '09:45:33', event: 'Hollywood crew deployed (8 units)', type: 'deploy' },
  { time: '10:12:56', event: 'SEAL team replicated (high volume)', type: 'replicate' },
  { time: '11:30:01', event: 'Master merge: INTEL + CYBER → MASTER', type: 'master_merge' },
  { time: '12:00:00', event: 'Total active agents: 81', type: 'status' },
];
