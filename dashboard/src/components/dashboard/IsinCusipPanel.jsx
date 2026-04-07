import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import GlowCard from '../ui/GlowCard';
import AnimatedCounter from '../ui/AnimatedCounter';
import StatusBadge from '../ui/StatusBadge';
import { isinCusipStats, isinCusipRecords, exposureByMethod } from '../../data/isinCusip';

const fmtB = (v) => `$${(v / 1e9).toFixed(1)}B`;

export default function IsinCusipPanel() {
  return (
    <section id="isincusip" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">ISIN ↔ CUSIP Exposure Analysis</h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <GlowCard><p className="text-xs text-gray-500">ISINs Mapped</p><AnimatedCounter value={isinCusipStats.totalIsinMapped} className="text-2xl font-bold text-white" /></GlowCard>
        <GlowCard><p className="text-xs text-gray-500">CUSIPs Linked</p><AnimatedCounter value={isinCusipStats.totalCusipLinked} className="text-2xl font-bold text-white" /></GlowCard>
        <GlowCard glow="red"><p className="text-xs text-gray-500">Illicit Instruments</p><AnimatedCounter value={isinCusipStats.illicitInstrumentsExposed} className="text-2xl font-bold text-red-400" /></GlowCard>
        <GlowCard glow="amber"><p className="text-xs text-gray-500">Laundered</p><AnimatedCounter value={2300000000000} prefix="$" decimals={1} className="text-2xl font-bold text-amber-400" /></GlowCard>
        <GlowCard><p className="text-xs text-gray-500">Owners Unmasked</p><AnimatedCounter value={isinCusipStats.beneficialOwnersUnmasked} className="text-2xl font-bold text-cyan-400" /></GlowCard>
        <GlowCard><p className="text-xs text-gray-500">Shells Linked</p><AnimatedCounter value={isinCusipStats.shellEntitiesLinked} className="text-2xl font-bold text-purple-400" /></GlowCard>
      </div>

      <GlowCard>
        <h3 className="mb-3 text-sm font-semibold text-gray-400">Exposure by Detection Method</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={exposureByMethod} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
            <XAxis type="number" tickFormatter={fmtB} stroke="#64748b" fontSize={11} />
            <YAxis type="category" dataKey="method" stroke="#64748b" fontSize={10} width={160} />
            <Tooltip formatter={fmtB} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
            <Bar dataKey="amountUsd" name="Amount Exposed">{exposureByMethod.map((e, i) => <Cell key={i} fill={e.color} />)}</Bar>
          </BarChart>
        </ResponsiveContainer>
      </GlowCard>

      <GlowCard glow="purple">
        <h3 className="mb-3 text-sm font-semibold text-purple-400">ISIN/CUSIP Exposure Records (Sample)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-purple-500/10"><tr>
              <th className="px-3 py-2 text-xs text-gray-500">ISIN</th><th className="px-3 py-2 text-xs text-gray-500">CUSIP</th><th className="px-3 py-2 text-xs text-gray-500">Entity</th><th className="px-3 py-2 text-xs text-gray-500">Beneficial Owner</th><th className="px-3 py-2 text-xs text-gray-500">Risk</th><th className="px-3 py-2 text-xs text-gray-500">Exposed Via</th><th className="px-3 py-2 text-xs text-gray-500">Amount</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{isinCusipRecords.map(r => (
              <tr key={r.isin}><td className="px-3 py-2 font-mono text-xs text-cyan-400">{r.isin}</td><td className="px-3 py-2 font-mono text-xs text-gray-400">{r.cusip}</td><td className="px-3 py-2 text-white">{r.name}</td><td className="px-3 py-2 text-xs text-red-400">{r.beneficialOwner}</td><td className="px-3 py-2"><StatusBadge status={r.riskLevel} /></td><td className="px-3 py-2 text-xs text-gray-400">{r.exposedVia}</td><td className="px-3 py-2 font-mono text-amber-400">${(r.amountUsd / 1e9).toFixed(1)}B</td></tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>
    </section>
  );
}
