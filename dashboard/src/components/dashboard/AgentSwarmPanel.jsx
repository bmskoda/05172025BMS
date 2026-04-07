import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import GlowCard from '../ui/GlowCard';
import AnimatedCounter from '../ui/AnimatedCounter';
import { agentsByRole, lifecycleEvents } from '../../data/agentSwarm';

export default function AgentSwarmPanel() {
  const totalAgents = agentsByRole.reduce((s, r) => s + r.agents, 0);
  const totalTasks = agentsByRole.reduce((s, r) => s + r.tasks, 0);
  return (
    <section id="agents" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Agent Swarm Dashboard</h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <GlowCard><p className="text-xs text-gray-500">Active Agents</p><AnimatedCounter value={totalAgents} className="text-2xl font-bold text-cyan-400" /></GlowCard>
        <GlowCard><p className="text-xs text-gray-500">Total Tasks</p><AnimatedCounter value={totalTasks} className="text-2xl font-bold text-white" /></GlowCard>
        <GlowCard><p className="text-xs text-gray-500">Replications</p><AnimatedCounter value={agentsByRole.reduce((s, r) => s + r.replications, 0)} className="text-2xl font-bold text-purple-400" /></GlowCard>
        <GlowCard><p className="text-xs text-gray-500">Merges</p><AnimatedCounter value={agentsByRole.reduce((s, r) => s + r.merges, 0)} className="text-2xl font-bold text-amber-400" /></GlowCard>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Agents by Role</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart><Pie data={agentsByRole} cx="50%" cy="50%" innerRadius={50} outerRadius={100} dataKey="agents" nameKey="role" label={({ role }) => role.split(' ')[0]}>
              {agentsByRole.map((e, i) => <Cell key={i} fill={e.color} />)}
            </Pie><Tooltip contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} /></PieChart>
          </ResponsiveContainer>
        </GlowCard>
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Tasks Completed by Role</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={agentsByRole} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis type="number" stroke="#64748b" fontSize={11} />
              <YAxis type="category" dataKey="code" stroke="#64748b" fontSize={10} width={80} />
              <Tooltip contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Bar dataKey="tasks" name="Tasks">{agentsByRole.map((e, i) => <Cell key={i} fill={e.color} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </GlowCard>
      </div>
      <GlowCard>
        <h3 className="mb-3 text-sm font-semibold text-gray-400">Lifecycle Event Log</h3>
        <div className="space-y-2">
          {lifecycleEvents.map((e, i) => (
            <div key={i} className="flex items-center gap-3 text-sm">
              <span className="shrink-0 font-mono text-xs text-gray-600 w-20">{e.time}</span>
              <span className={`h-2 w-2 shrink-0 rounded-full ${e.type === 'deploy' ? 'bg-cyan-500' : e.type === 'replicate' ? 'bg-purple-500' : e.type === 'merge' ? 'bg-amber-500' : e.type === 'master_merge' ? 'bg-red-500' : 'bg-emerald-500'}`} />
              <span className="text-gray-300">{e.event}</span>
            </div>
          ))}
        </div>
      </GlowCard>
    </section>
  );
}
