import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import GlowCard from '../ui/GlowCard';
import StatusBadge from '../ui/StatusBadge';
import { trackedAddresses, chainDistribution, mixerEvents, cdsTargets } from '../../data/blockchainData';

const fmtM = (v) => `$${(v / 1e6).toFixed(0)}M`;

export default function BlockchainForensics() {
  return (
    <section id="blockchain" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Blockchain Forensics</h2>
      <div className="overflow-x-auto rounded-xl border border-cyan-500/10">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-cyan-500/10 bg-[#0a0e1a]"><tr>
            <th className="px-4 py-3 text-xs text-gray-500">Address</th><th className="px-4 py-3 text-xs text-gray-500">Chain</th><th className="px-4 py-3 text-xs text-gray-500">Entity</th><th className="px-4 py-3 text-xs text-gray-500">Risk</th><th className="px-4 py-3 text-xs text-gray-500">Txns</th><th className="px-4 py-3 text-xs text-gray-500">Volume</th>
          </tr></thead>
          <tbody className="divide-y divide-white/5">{trackedAddresses.map(a => (
            <tr key={a.address}><td className="px-4 py-2 font-mono text-xs text-cyan-400">{a.address.slice(0, 10)}...{a.address.slice(-6)}</td><td className="px-4 py-2 text-gray-400">{a.chain}</td><td className="px-4 py-2 text-white">{a.entity}</td><td className="px-4 py-2"><StatusBadge status={a.risk >= 95 ? 'CRITICAL' : a.risk >= 80 ? 'HIGH' : 'MEDIUM'} /></td><td className="px-4 py-2 text-gray-400">{a.txCount.toLocaleString()}</td><td className="px-4 py-2 font-mono text-amber-400">{fmtM(a.totalUsd)}</td></tr>
          ))}</tbody>
        </table>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Volume by Chain</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={chainDistribution} cx="50%" cy="50%" innerRadius={50} outerRadius={100} dataKey="volume" nameKey="chain" label={({ chain, pct }) => `${chain} ${pct}%`} labelLine={false}>
                {chainDistribution.map((e, i) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Tooltip formatter={(v) => `$${(v / 1e9).toFixed(1)}B`} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </GlowCard>
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Mixer Detection Events</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={mixerEvents}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis dataKey="year" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Bar dataKey="events" fill="#ef4444" name="Mixer Events" />
            </BarChart>
          </ResponsiveContainer>
        </GlowCard>
      </div>
      <GlowCard glow="red">
        <h3 className="mb-3 text-sm font-semibold text-red-400">CDS / Derivatives Exposure</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr><th className="px-3 py-2 text-xs text-gray-500">Ticker</th><th className="px-3 py-2 text-xs text-gray-500">Name</th><th className="px-3 py-2 text-xs text-gray-500">Notional</th><th className="px-3 py-2 text-xs text-gray-500">Positions</th><th className="px-3 py-2 text-xs text-gray-500">Avg Spread (bps)</th><th className="px-3 py-2 text-xs text-gray-500">Risk</th></tr></thead>
            <tbody className="divide-y divide-white/5">{cdsTargets.map(c => (
              <tr key={c.ticker}><td className="px-3 py-2 font-mono text-cyan-400">{c.ticker}</td><td className="px-3 py-2 text-white">{c.name}</td><td className="px-3 py-2 font-mono text-amber-400">${(c.notional / 1e9).toFixed(1)}B</td><td className="px-3 py-2 text-gray-400">{c.positions}</td><td className="px-3 py-2 text-gray-400">{c.avgSpread}</td><td className="px-3 py-2"><StatusBadge status={c.risk} /></td></tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>
    </section>
  );
}
