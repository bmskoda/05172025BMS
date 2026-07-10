import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Snowflake, ShieldCheck, Landmark } from 'lucide-react';
import GlowCard from '../ui/GlowCard';
import AnimatedCounter from '../ui/AnimatedCounter';
import StatusBadge from '../ui/StatusBadge';
import { treasuryStats, freezeTargets, geniusActPayload, stablecoinIssuers } from '../../data/treasuryGenius';

const fmtT = (v) => `$${(v / 1e12).toFixed(1)}T`;

export default function TreasuryWalletFreeze() {
  return (
    <section id="treasury" className="space-y-6">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">US Treasury / GENIUS Act Wallet Freezing</h2>
      <p className="text-xs text-gray-500">GENIUS Act-compliant freeze payloads ready for immediate submission to US Treasury (OFAC), Secret Service, White House, Department of War, FinCEN</p>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <GlowCard glow="cyan"><p className="text-[10px] text-gray-500">Wallets Flagged</p><AnimatedCounter value={treasuryStats.totalWalletsFlagged} className="text-lg font-bold text-cyan-400" /></GlowCard>
        <GlowCard glow="emerald"><p className="text-[10px] text-gray-500">GENIUS Compliant</p><AnimatedCounter value={treasuryStats.geniusActCompliant} className="text-lg font-bold text-emerald-400" /></GlowCard>
        <GlowCard glow="amber"><p className="text-[10px] text-gray-500">Total Freezable</p><AnimatedCounter value={340000000000000} prefix="$" decimals={0} className="text-lg font-bold text-amber-400" /></GlowCard>
        <GlowCard glow="purple"><p className="text-[10px] text-gray-500">Issuers Notified</p><AnimatedCounter value={treasuryStats.stablecoinIssuersNotified} className="text-lg font-bold text-purple-400" /></GlowCard>
        <GlowCard glow="red"><p className="text-[10px] text-gray-500">Submission Status</p><p className="mt-1 text-sm font-bold text-emerald-400">READY</p></GlowCard>
      </div>

      {/* Freeze Targets */}
      <GlowCard glow="cyan">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-cyan-400"><Snowflake className="h-4 w-4" />Priority Freeze Targets</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-cyan-500/10"><tr>
              <th className="px-3 py-2 text-xs text-gray-500">Wallet</th><th className="px-3 py-2 text-xs text-gray-500">Chain</th><th className="px-3 py-2 text-xs text-gray-500">Entity</th><th className="px-3 py-2 text-xs text-gray-500">Balance</th><th className="px-3 py-2 text-xs text-gray-500">OFAC Match</th><th className="px-3 py-2 text-xs text-gray-500">Issuer</th><th className="px-3 py-2 text-xs text-gray-500">Status</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{freezeTargets.map(t => (
              <tr key={t.wallet}>
                <td className="px-3 py-2 font-mono text-xs text-cyan-400">{t.wallet}</td>
                <td className="px-3 py-2 text-gray-400">{t.chain}</td>
                <td className="px-3 py-2 text-white">{t.entity}</td>
                <td className="px-3 py-2 font-mono text-amber-400">${(t.balanceUsd / 1e9).toFixed(2)}B</td>
                <td className="px-3 py-2 font-mono text-xs text-red-400">{t.ofacMatch}</td>
                <td className="px-3 py-2 text-xs text-gray-400">{t.issuer}</td>
                <td className="px-3 py-2"><span className={`rounded-full px-2 py-0.5 text-xs font-bold ${t.geniusStatus === 'FROZEN' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-emerald-500/20 text-emerald-400'}`}>{t.geniusStatus}</span></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>

      {/* Stablecoin Issuers */}
      <GlowCard glow="purple">
        <h3 className="mb-3 text-sm font-semibold text-purple-400">Freezable Value by Stablecoin Issuer</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={stablecoinIssuers} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
            <XAxis type="number" tickFormatter={fmtT} stroke="#64748b" fontSize={10} />
            <YAxis type="category" dataKey="issuer" stroke="#64748b" fontSize={9} width={150} />
            <Tooltip formatter={fmtT} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
            <Bar dataKey="freezableUsd" name="Freezable USD" fill="#8b5cf6" />
          </BarChart>
        </ResponsiveContainer>
      </GlowCard>

      {/* GENIUS Act Payload Spec */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlowCard glow="emerald">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-emerald-400"><ShieldCheck className="h-4 w-4" />Legal Basis</h3>
          <p className="text-xs text-gray-400 mb-2 font-mono">{geniusActPayload.statute}</p>
          <ul className="list-disc pl-5 space-y-1 text-xs text-gray-400">
            {geniusActPayload.legalBasis.map((l, i) => <li key={i}>{l}</li>)}
          </ul>
        </GlowCard>
        <GlowCard glow="cyan">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-cyan-400"><Landmark className="h-4 w-4" />Submission Targets</h3>
          <div className="flex flex-wrap gap-2">
            {geniusActPayload.submissionTargets.map((t) => (
              <span key={t} className="rounded-lg border border-cyan-500/20 bg-[#0a0e1a] px-2.5 py-1 text-xs text-cyan-400">{t}</span>
            ))}
          </div>
          <h4 className="mt-4 mb-2 text-xs font-semibold text-gray-400">Payload Fields</h4>
          <div className="flex flex-wrap gap-1">
            {geniusActPayload.payloadFields.map((f) => (
              <span key={f} className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-[10px] text-gray-500">{f}</span>
            ))}
          </div>
        </GlowCard>
      </div>
    </section>
  );
}
