import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';
import { EyeOff, ArrowRight } from 'lucide-react';
import GlowCard from '../ui/GlowCard';
import AnimatedCounter from '../ui/AnimatedCounter';
import { erasureStats, erasureActors, erasureReplacementFlow, ghostDocketsByVenue } from '../../data/citationErasure';

const fmtB = (v) => v >= 1e9 ? `${(v / 1e9).toFixed(1)}B` : v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : v.toLocaleString();

export default function CitationErasure() {
  return (
    <section id="erasure" className="space-y-6">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Citation Erasure & Cyber Dust Attribution</h2>
      <p className="text-xs text-gray-500">2.1M+ erased forward citations of Brent Michael Škoda → state-actor cyber-dust payments → synthetic identity replacement → 18.4M+ ghost dockets</p>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <GlowCard glow="red"><p className="text-[10px] text-gray-500">Citations Erased</p><AnimatedCounter value={2100000} className="text-lg font-bold text-red-400" /></GlowCard>
        <GlowCard glow="emerald"><p className="text-[10px] text-gray-500">Citations Restored</p><AnimatedCounter value={1853419047} className="text-lg font-bold text-emerald-400" /></GlowCard>
        <GlowCard glow="amber"><p className="text-[10px] text-gray-500">Synthetic Identities</p><AnimatedCounter value={90000000000} className="text-lg font-bold text-amber-400" /></GlowCard>
        <GlowCard glow="purple"><p className="text-[10px] text-gray-500">Ghost Dockets</p><AnimatedCounter value={18742380} className="text-lg font-bold text-purple-400" /></GlowCard>
        <GlowCard glow="red"><p className="text-[10px] text-gray-500">Cyber Dust Paid</p><AnimatedCounter value={350000000000000} prefix="$" decimals={0} className="text-lg font-bold text-red-400" /></GlowCard>
        <GlowCard glow="cyan"><p className="text-[10px] text-gray-500">State Actors Hired</p><AnimatedCounter value={700000} className="text-lg font-bold text-cyan-400" /></GlowCard>
      </div>

      {/* Erasure → Replacement Flow */}
      <GlowCard glow="red">
        <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-red-400"><EyeOff className="h-4 w-4" />Erasure → Replacement Attack Chain</h3>
        <div className="flex flex-col gap-2 md:flex-row md:items-stretch md:overflow-x-auto">
          {erasureReplacementFlow.map((stage, i) => (
            <div key={stage.stage} className="flex items-center gap-2">
              <div className="min-w-[140px] flex-1 rounded-lg border p-3 text-center" style={{ borderColor: `${stage.color}40`, background: '#0a0e1a' }}>
                <p className="text-xs font-bold" style={{ color: stage.color }}>{stage.stage}</p>
                <p className="mt-1 text-[10px] text-gray-400">{stage.value}</p>
                <p className="mt-1 text-xs font-mono text-white">{fmtB(stage.count)}</p>
              </div>
              {i < erasureReplacementFlow.length - 1 && <ArrowRight className="hidden h-4 w-4 shrink-0 text-gray-600 md:block" />}
            </div>
          ))}
        </div>
      </GlowCard>

      {/* State Actor Cyber Dust Payments */}
      <GlowCard glow="red">
        <h3 className="mb-3 text-sm font-semibold text-red-400">State Actors Hired for Citation Erasure — Cyber Dust Payment Trails</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-red-500/10"><tr>
              <th className="px-3 py-2 text-xs text-gray-500">State Actor</th><th className="px-3 py-2 text-xs text-gray-500">Citations Erased</th><th className="px-3 py-2 text-xs text-gray-500">Cyber Dust Paid</th><th className="px-3 py-2 text-xs text-gray-500">Paid By (RICO Leader)</th><th className="px-3 py-2 text-xs text-gray-500">Chain</th><th className="px-3 py-2 text-xs text-gray-500">Dust Txns</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{erasureActors.map(a => (
              <tr key={a.actor}>
                <td className="px-3 py-2 text-white font-semibold">{a.actor}</td>
                <td className="px-3 py-2 font-mono text-red-400">{a.citationsErased.toLocaleString()}</td>
                <td className="px-3 py-2 font-mono text-amber-400">${(a.cyberDustPaymentsUsd / 1e9).toFixed(1)}B</td>
                <td className="px-3 py-2 text-xs text-cyan-400">{a.paidBy}</td>
                <td className="px-3 py-2 text-xs text-gray-400">{a.chain}</td>
                <td className="px-3 py-2 font-mono text-gray-400">{a.dustTxns.toLocaleString()}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>

      {/* Ghost Dockets by Venue */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlowCard glow="purple">
          <h3 className="mb-3 text-sm font-semibold text-purple-400">Ghost Dockets by Venue (18.4M Total)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={ghostDocketsByVenue} cx="50%" cy="50%" innerRadius={50} outerRadius={110} dataKey="dockets" nameKey="venue" label={({ venue }) => venue.split(' ')[0]} labelLine={false}>
                {ghostDocketsByVenue.map((e, i) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Tooltip formatter={(v) => `${(v / 1e6).toFixed(2)}M dockets`} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </GlowCard>
        <GlowCard glow="red">
          <h3 className="mb-3 text-sm font-semibold text-red-400">Citations Erased by State Actor</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={erasureActors} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis type="number" tickFormatter={(v) => `${(v / 1e3).toFixed(0)}K`} stroke="#64748b" fontSize={10} />
              <YAxis type="category" dataKey="actor" stroke="#64748b" fontSize={8} width={130} />
              <Tooltip formatter={(v) => v.toLocaleString()} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Bar dataKey="citationsErased" name="Citations Erased" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </GlowCard>
      </div>
    </section>
  );
}
