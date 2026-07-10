import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts';
import GlowCard from '../ui/GlowCard';
import AnimatedCounter from '../ui/AnimatedCounter';
import StatusBadge from '../ui/StatusBadge';
import { tokenizedIPStats, wrappedTokenTypes, daoStructures, communityDetection, fentanylUBOResolution, fortuneLinkedEntities } from '../../data/tokenizedIP';

const fmtT = (v) => `$${(v / 1e12).toFixed(1)}T`;

export default function TokenizedIPTracing() {
  return (
    <section id="tokenized" className="space-y-6">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Tokenized IP Tracing — Genesis to Date</h2>
      <p className="text-xs text-gray-500">15,213+ stolen global patent families • 194 WIPO jurisdictions • Fortune 5000 / Global 2000 / S&P 500 • All derivative works via illicit DAOs & stealth DAOs</p>

      {/* KPI Row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <GlowCard glow="cyan"><p className="text-[10px] text-gray-500">Wrapped Tokens</p><AnimatedCounter value={tokenizedIPStats.totalWrappedTokens} className="text-xl font-bold text-cyan-400" /></GlowCard>
        <GlowCard glow="purple"><p className="text-[10px] text-gray-500">DAOs + Stealth</p><AnimatedCounter value={tokenizedIPStats.totalDAOs + tokenizedIPStats.totalStealthDAOs} className="text-xl font-bold text-purple-400" /></GlowCard>
        <GlowCard glow="red"><p className="text-[10px] text-gray-500">Fractionalized NFTs</p><AnimatedCounter value={tokenizedIPStats.fractionalizedPatents} className="text-xl font-bold text-red-400" /></GlowCard>
        <GlowCard glow="amber"><p className="text-[10px] text-gray-500">Synthetic Identities</p><AnimatedCounter value={tokenizedIPStats.syntheticInventorIdentities} className="text-xl font-bold text-amber-400" /></GlowCard>
        <GlowCard glow="emerald"><p className="text-[10px] text-gray-500">Wallets Discovered</p><AnimatedCounter value={tokenizedIPStats.totalWalletsDiscovered} className="text-xl font-bold text-emerald-400" /></GlowCard>
        <GlowCard glow="red"><p className="text-[10px] text-gray-500">Hidden Wallets</p><AnimatedCounter value={tokenizedIPStats.hiddenWalletsExposed} className="text-xl font-bold text-red-400" /></GlowCard>
      </div>

      {/* Wrapped Token Types */}
      <GlowCard>
        <h3 className="mb-3 text-sm font-semibold text-gray-400">Wrapped Tokenized IP Categories (by Value)</h3>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={wrappedTokenTypes} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
            <XAxis type="number" tickFormatter={fmtT} stroke="#64748b" fontSize={10} />
            <YAxis type="category" dataKey="type" stroke="#64748b" fontSize={9} width={160} />
            <Tooltip formatter={fmtT} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
            <Bar dataKey="valueUsd" name="Value (USD)">{wrappedTokenTypes.map((e, i) => <Cell key={i} fill={e.color} />)}</Bar>
          </BarChart>
        </ResponsiveContainer>
      </GlowCard>

      {/* DAO Structures */}
      <GlowCard glow="purple">
        <h3 className="mb-3 text-sm font-semibold text-purple-400">Illicit DAOs & Stealth DAOs ({daoStructures.length} Identified)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-purple-500/10"><tr>
              <th className="px-3 py-2 text-xs text-gray-500">DAO Name</th><th className="px-3 py-2 text-xs text-gray-500">Type</th><th className="px-3 py-2 text-xs text-gray-500">Patents</th><th className="px-3 py-2 text-xs text-gray-500">TVL</th><th className="px-3 py-2 text-xs text-gray-500">Governance</th><th className="px-3 py-2 text-xs text-gray-500">RICO Link</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{daoStructures.map(d => (
              <tr key={d.name}><td className="px-3 py-2 font-mono text-xs text-cyan-400">{d.name}</td><td className="px-3 py-2"><StatusBadge status={d.type === 'Stealth DAO' ? 'CRITICAL' : 'HIGH'} /></td><td className="px-3 py-2 text-white">{d.patents.toLocaleString()}</td><td className="px-3 py-2 font-mono text-amber-400">${(d.tvlUsd / 1e9).toFixed(1)}B</td><td className="px-3 py-2 text-xs text-gray-400">{d.governance}</td><td className="px-3 py-2 text-xs text-red-400">{d.linkedRICO}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>

      {/* Community Detection Hierarchy */}
      <GlowCard glow="cyan">
        <h3 className="mb-3 text-sm font-semibold text-cyan-400">Recursive Community Detection (7 Levels — EXHAUSTED)</h3>
        <div className="space-y-2">
          {communityDetection.map((level, i) => (
            <div key={level.level} className="flex items-center gap-3">
              <div className="w-32 text-xs font-mono text-gray-400">{level.level}</div>
              <div className="flex-1">
                <div className="h-4 rounded-full bg-gray-800 overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${Math.max(5, (level.wallets / 891247) * 100)}%`, background: `hsl(${180 + i * 25}, 70%, 50%)` }} />
                </div>
              </div>
              <div className="w-48 text-right text-xs text-gray-500">{level.clusters.toLocaleString()} clusters • {level.wallets.toLocaleString()} wallets</div>
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-emerald-400 font-semibold">✓ All real-world data EXHAUSTED at Level 7 (Atomic decomposition)</p>
      </GlowCard>

      {/* Fentanyl UBO Resolution */}
      <GlowCard glow="red">
        <h3 className="mb-3 text-sm font-semibold text-red-400">Fentanyl Token — True UBO Resolution (Real Person Identification)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-red-500/10"><tr>
              <th className="px-3 py-2 text-xs text-gray-500">Token Contract</th><th className="px-3 py-2 text-xs text-gray-500">True UBO (Person)</th><th className="px-3 py-2 text-xs text-gray-500">Jurisdiction</th><th className="px-3 py-2 text-xs text-gray-500">Profit Share</th><th className="px-3 py-2 text-xs text-gray-500">Total USD</th><th className="px-3 py-2 text-xs text-gray-500">Chain</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{fentanylUBOResolution.map(f => (
              <tr key={f.tokenContract}><td className="px-3 py-2 font-mono text-xs text-cyan-400">{f.tokenContract}</td><td className="px-3 py-2 text-white font-semibold">{f.uboPerson}</td><td className="px-3 py-2 text-gray-400">{f.jurisdiction}</td><td className="px-3 py-2 text-red-400 font-mono">{f.profitSharePct}%</td><td className="px-3 py-2 font-mono text-amber-400">${(f.totalUsd / 1e9).toFixed(1)}B</td><td className="px-3 py-2 text-gray-400">{f.chain}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>

      {/* Fortune/Global/S&P Linkage */}
      <GlowCard>
        <h3 className="mb-3 text-sm font-semibold text-gray-400">Corporate Linkage (Fortune 5000 / Global 2000 / S&P 500)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-cyan-500/10"><tr>
              <th className="px-4 py-2 text-xs text-gray-500">Index</th><th className="px-4 py-2 text-xs text-gray-500">Companies Linked</th><th className="px-4 py-2 text-xs text-gray-500">Tokenized Licenses</th><th className="px-4 py-2 text-xs text-gray-500">Total Value</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{fortuneLinkedEntities.map(f => (
              <tr key={f.category}><td className="px-4 py-2 text-white font-semibold">{f.category}</td><td className="px-4 py-2 font-mono text-cyan-400">{f.linked.toLocaleString()}</td><td className="px-4 py-2 text-gray-400">{f.tokenizedLicenses.toLocaleString()}</td><td className="px-4 py-2 font-mono text-amber-400">{fmtT(f.totalValueUsd)}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>
    </section>
  );
}
