import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import GlowCard from '../ui/GlowCard';
import AnimatedCounter from '../ui/AnimatedCounter';
import { disruptionByYear, supplyChainNodes } from '../../data/fentanylData';

export default function FentanylDashboard() {
  return (
    <section id="fentanyl" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Fentanyl Supply Chain Disruption</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <GlowCard glow="emerald"><p className="text-xs text-gray-500">Total Doses Disrupted</p><AnimatedCounter value={18000001} className="text-3xl font-bold text-emerald-400" /></GlowCard>
        <GlowCard glow="emerald"><p className="text-xs text-gray-500">Lives Saved</p><AnimatedCounter value={18001} className="text-3xl font-bold text-emerald-400" /></GlowCard>
        <GlowCard glow="red"><p className="text-xs text-gray-500">Lives Endangered</p><AnimatedCounter value={500000} className="text-3xl font-bold text-red-400" suffix="+" /></GlowCard>
      </div>
      <GlowCard>
        <h3 className="mb-3 text-sm font-semibold text-gray-400">Annual Disruption Timeline</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={disruptionByYear}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
            <XAxis dataKey="year" stroke="#64748b" fontSize={11} />
            <YAxis tickFormatter={v => `${(v / 1e6).toFixed(1)}M`} stroke="#64748b" fontSize={11} />
            <Tooltip formatter={v => v.toLocaleString()} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
            <Area type="monotone" dataKey="dosesDisrupted" stroke="#10b981" fill="#10b981" fillOpacity={0.3} name="Doses Disrupted" />
          </AreaChart>
        </ResponsiveContainer>
      </GlowCard>
      <GlowCard>
        <h3 className="mb-3 text-sm font-semibold text-gray-400">Supply Chain Flow</h3>
        <div className="flex flex-wrap items-center justify-center gap-2">
          {supplyChainNodes.map((node, i) => (
            <div key={node.id} className="flex items-center gap-2">
              <div className={`rounded-lg border px-4 py-3 text-center ${node.id === 'disrupted' ? 'border-emerald-500/40 bg-emerald-500/10' : 'border-cyan-500/20 bg-[#0a0e1a]'}`}>
                <p className={`text-sm font-bold ${node.id === 'disrupted' ? 'text-emerald-400' : 'text-white'}`}>{node.label}</p>
                <p className="text-xs text-gray-500 mt-1">{node.region}</p>
              </div>
              {i < supplyChainNodes.length - 1 && <span className="text-gray-600 text-xl">→</span>}
            </div>
          ))}
        </div>
      </GlowCard>
    </section>
  );
}
