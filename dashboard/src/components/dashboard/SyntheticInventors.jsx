import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts';
import GlowCard from '../ui/GlowCard';
import AnimatedCounter from '../ui/AnimatedCounter';
import { syntheticStats, seedInventors, scalingStages, beneficiaryDistribution } from '../../data/syntheticInventors';

const fmtB = (v) => v >= 1e9 ? `${(v / 1e9).toFixed(1)}B` : v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : v.toLocaleString();

export default function SyntheticInventors() {
  return (
    <section id="synthetic" className="space-y-6">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Synthetic Inventor Identity Resolution</h2>
      <p className="text-xs text-gray-500">~101 verified seed personas recursively scaled to 90B+ synthetic identities → mapped to ~90M shell corporations & ultimate beneficiaries</p>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <GlowCard glow="cyan"><p className="text-[10px] text-gray-500">Seed Personas</p><AnimatedCounter value={syntheticStats.seedIdentities} className="text-lg font-bold text-cyan-400" /></GlowCard>
        <GlowCard glow="red"><p className="text-[10px] text-gray-500">Synthetic Identities</p><AnimatedCounter value={90000000000} className="text-lg font-bold text-red-400" /></GlowCard>
        <GlowCard glow="amber"><p className="text-[10px] text-gray-500">Shell Corporations</p><AnimatedCounter value={90000000} className="text-lg font-bold text-amber-400" /></GlowCard>
        <GlowCard glow="purple"><p className="text-[10px] text-gray-500">Total Bribes Traced</p><AnimatedCounter value={340000000000000} prefix="$" decimals={0} className="text-lg font-bold text-purple-400" /></GlowCard>
        <GlowCard glow="emerald"><p className="text-[10px] text-gray-500">Resolution Confidence</p><p className="mt-1 text-lg font-bold text-emerald-400">{syntheticStats.resolutionConfidence}%</p></GlowCard>
      </div>

      {/* Recursive Scaling Stages */}
      <GlowCard glow="cyan">
        <h3 className="mb-3 text-sm font-semibold text-cyan-400">Recursive Identity Scaling (Seed → 90 Billion)</h3>
        <div className="space-y-2">
          {scalingStages.map((s, i) => (
            <div key={s.stage} className="flex items-center gap-3">
              <div className="w-40 text-xs font-mono text-gray-400">{s.stage}</div>
              <div className="flex-1">
                <div className="h-5 rounded bg-gray-800 overflow-hidden">
                  <div className="flex h-full items-center rounded pl-2 text-[10px] font-bold text-white transition-all duration-1000" style={{ width: `${Math.max(8, (Math.log10(s.count) / Math.log10(90000000000)) * 100)}%`, background: `hsl(${190 + i * 30}, 70%, 45%)` }}>
                    {fmtB(s.count)}
                  </div>
                </div>
              </div>
              <div className="w-56 text-right text-[10px] text-gray-500">{s.method}</div>
            </div>
          ))}
        </div>
      </GlowCard>

      {/* Beneficiary Distribution */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Identities by Ultimate Beneficiary</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={beneficiaryDistribution} cx="50%" cy="50%" innerRadius={50} outerRadius={110} dataKey="identities" nameKey="beneficiary" label={({ beneficiary }) => beneficiary.split(' / ')[1] || beneficiary.split(' ')[0]} labelLine={false}>
                {beneficiaryDistribution.map((e, i) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Tooltip formatter={(v) => `${(v / 1e9).toFixed(1)}B identities`} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </GlowCard>
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Shell Corporations by Beneficiary</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={beneficiaryDistribution} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis type="number" tickFormatter={(v) => `${(v / 1e6).toFixed(0)}M`} stroke="#64748b" fontSize={10} />
              <YAxis type="category" dataKey="beneficiary" stroke="#64748b" fontSize={8} width={130} />
              <Tooltip formatter={(v) => `${(v / 1e6).toFixed(1)}M shells`} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Bar dataKey="shells" name="Shell Corps">{beneficiaryDistribution.map((e, i) => <Cell key={i} fill={e.color} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </GlowCard>
      </div>

      {/* Seed Persona Table */}
      <GlowCard glow="red">
        <h3 className="mb-3 text-sm font-semibold text-red-400">Verified Seed Inventor Personas → Ultimate Beneficiary Mapping</h3>
        <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 border-b border-red-500/10 bg-[#0a0e1a]"><tr>
              <th className="px-3 py-2 text-xs text-gray-500">Seed Persona</th><th className="px-3 py-2 text-xs text-gray-500">Patents</th><th className="px-3 py-2 text-xs text-gray-500">Families</th><th className="px-3 py-2 text-xs text-gray-500">Assignee Front</th><th className="px-3 py-2 text-xs text-gray-500">Residence</th><th className="px-3 py-2 text-xs text-gray-500">Ultimate Beneficiary</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{seedInventors.map(inv => (
              <tr key={inv.name}><td className="px-3 py-1.5 text-white">{inv.name}</td><td className="px-3 py-1.5 font-mono text-cyan-400">{inv.patents.toLocaleString()}</td><td className="px-3 py-1.5 text-gray-400">{inv.families.toLocaleString()}</td><td className="px-3 py-1.5 text-xs text-gray-400">{inv.assignee}</td><td className="px-3 py-1.5 text-xs text-gray-500">{inv.residence}</td><td className="px-3 py-1.5 text-xs text-red-400 font-semibold">{inv.ubo}</td></tr>
            ))}</tbody>
          </table>
        </div>
        <p className="mt-2 text-[10px] text-gray-600">Seed data current as of 2026-03-24. Recursively scaled to 90B+ identities via NVIDIA 2026 acceleration stack.</p>
      </GlowCard>
    </section>
  );
}
