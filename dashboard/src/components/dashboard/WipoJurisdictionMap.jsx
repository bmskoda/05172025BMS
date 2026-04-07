import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend, LineChart, Line } from 'recharts';
import GlowCard from '../ui/GlowCard';
import AnimatedCounter from '../ui/AnimatedCounter';
import StatusBadge from '../ui/StatusBadge';
import { wipoRegions, topCompromisedOffices, wipoStats } from '../../data/wipoJurisdictions';

export default function WipoJurisdictionMap() {
  return (
    <section id="wipo" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Global IP System — 194 WIPO Jurisdictions</h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <GlowCard glow="cyan"><p className="text-xs text-gray-500">WIPO Members</p><AnimatedCounter value={wipoStats.totalMembers} className="text-2xl font-bold text-white" /></GlowCard>
        <GlowCard glow="red"><p className="text-xs text-gray-500">Compromised</p><AnimatedCounter value={wipoStats.compromisedMembers} className="text-2xl font-bold text-red-400" /></GlowCard>
        <GlowCard glow="red"><p className="text-xs text-gray-500">Compromise Rate</p><p className="mt-1 text-2xl font-bold text-red-400">{wipoStats.compromiseRate}%</p></GlowCard>
        <GlowCard glow="amber"><p className="text-xs text-gray-500">Stolen Filings</p><AnimatedCounter value={wipoStats.totalStolenFilings} className="text-2xl font-bold text-amber-400" /></GlowCard>
        <GlowCard glow="red"><p className="text-xs text-gray-500">Examiners Bribed</p><AnimatedCounter value={wipoStats.totalExaminersBribed} className="text-2xl font-bold text-red-400" /></GlowCard>
        <GlowCard glow="red"><p className="text-xs text-gray-500">Cartel-Controlled</p><AnimatedCounter value={wipoStats.cartelControlledOffices} className="text-2xl font-bold text-red-400" /></GlowCard>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Compromised Offices by Region</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={wipoRegions}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis dataKey="region" stroke="#64748b" fontSize={10} angle={-20} textAnchor="end" height={60} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Bar dataKey="compromised" name="Compromised" fill="#ef4444" />
              <Bar dataKey="members" name="Total Members" fill="#1e274d" />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </BarChart>
          </ResponsiveContainer>
        </GlowCard>
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Stolen Filings by Region</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={wipoRegions} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis type="number" stroke="#64748b" fontSize={11} />
              <YAxis type="category" dataKey="region" stroke="#64748b" fontSize={10} width={140} />
              <Tooltip contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Bar dataKey="stolenFilings" name="Stolen Filings">{wipoRegions.map((e, i) => <Cell key={i} fill={e.color} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </GlowCard>
      </div>

      <GlowCard glow="red">
        <h3 className="mb-3 text-sm font-semibold text-red-400">Top Compromised Patent Offices</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-red-500/10"><tr>
              <th className="px-3 py-2 text-xs text-gray-500">Office</th><th className="px-3 py-2 text-xs text-gray-500">Code</th><th className="px-3 py-2 text-xs text-gray-500">Stolen Filings</th><th className="px-3 py-2 text-xs text-gray-500">Level</th><th className="px-3 py-2 text-xs text-gray-500">Bribed</th><th className="px-3 py-2 text-xs text-gray-500">Method</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{topCompromisedOffices.map(o => (
              <tr key={o.code}><td className="px-3 py-2 text-white">{o.office}</td><td className="px-3 py-2 font-mono text-cyan-400">{o.code}</td><td className="px-3 py-2 font-mono text-amber-400">{o.stolenFilings.toLocaleString()}</td><td className="px-3 py-2"><StatusBadge status={o.compromiseLevel} /></td><td className="px-3 py-2 text-red-400">{o.examinersBribed}</td><td className="px-3 py-2 text-xs text-gray-400 max-w-xs">{o.method}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>
    </section>
  );
}
