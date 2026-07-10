import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import GlowCard from '../ui/GlowCard';
import AnimatedCounter from '../ui/AnimatedCounter';
import StatusBadge from '../ui/StatusBadge';
import { cyberDustThresholds, dustDetectionTiers, ricoStateActorMatrix, totalIllicitOwnership, fileWrapperAnomalies } from '../../data/cyberDust';

const fmtT = (v) => `$${(v / 1e12).toFixed(2)}T`;

function heatColor(value) {
  // value in trillions, scale 0-7
  const intensity = Math.min(value / 7, 1);
  const r = Math.round(120 + intensity * 135);
  const g = Math.round(40 * (1 - intensity));
  const b = Math.round(40 * (1 - intensity));
  return `rgb(${r}, ${g}, ${b})`;
}

export default function CyberDustDetection() {
  const { leaders, actors, flows } = ricoStateActorMatrix;

  return (
    <section id="cyberdust" className="space-y-6">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Hyper-Advanced Cyber Dust Detection</h2>
      <p className="text-xs text-gray-500">Deterministic uncovering of state-sponsored actor sub-transaction obfuscation at the new lowest detection threshold</p>

      {/* Threshold KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <GlowCard glow="red"><p className="text-[10px] text-gray-500">New Detection Limit</p><p className="mt-1 text-sm font-bold text-red-400">{cyberDustThresholds.newThreshold}</p></GlowCard>
        <GlowCard glow="emerald"><p className="text-[10px] text-gray-500">Improvement</p><p className="mt-1 text-sm font-bold text-emerald-400">{cyberDustThresholds.improvementFactor}</p></GlowCard>
        <GlowCard glow="cyan"><p className="text-[10px] text-gray-500">Dust Txns Uncovered</p><AnimatedCounter value={cyberDustThresholds.dustTransactionsUncovered} className="text-lg font-bold text-cyan-400" /></GlowCard>
        <GlowCard glow="amber"><p className="text-[10px] text-gray-500">State Actors Unmasked</p><AnimatedCounter value={cyberDustThresholds.stateActorsUnmasked} className="text-lg font-bold text-amber-400" /></GlowCard>
        <GlowCard glow="purple"><p className="text-[10px] text-gray-500">Detection Confidence</p><p className="mt-1 text-lg font-bold text-purple-400">{cyberDustThresholds.detectionConfidence}%</p></GlowCard>
      </div>

      {/* Dust Detection Tiers */}
      <GlowCard>
        <h3 className="mb-3 text-sm font-semibold text-gray-400">Dust Detection by Tier (Macro → Atto-scale)</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={dustDetectionTiers}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
            <XAxis dataKey="tier" stroke="#64748b" fontSize={9} angle={-15} textAnchor="end" height={70} />
            <YAxis tickFormatter={(v) => `${(v / 1e6).toFixed(0)}M`} stroke="#64748b" fontSize={11} />
            <Tooltip formatter={(v) => v.toLocaleString()} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
            <Bar dataKey="detected" name="Dust Txns Detected">{dustDetectionTiers.map((e, i) => <Cell key={i} fill={e.color} />)}</Bar>
          </BarChart>
        </ResponsiveContainer>
      </GlowCard>

      {/* RICO Leader x State Actor Heat Matrix */}
      <GlowCard glow="red">
        <h3 className="mb-3 text-sm font-semibold text-red-400">RICO Leader → State Actor Illicit Flow Matrix (USD Trillions)</h3>
        <p className="mb-2 text-xs text-gray-500">Fully consolidated blockchain-traced sums across all Genesis blocks → 2026-05-21</p>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr>
                <th className="sticky left-0 bg-[#0f1629] px-2 py-2 text-left text-gray-500">RICO Leader</th>
                {actors.map(a => <th key={a} className="px-2 py-2 text-center text-gray-500 whitespace-nowrap">{a}</th>)}
                <th className="px-2 py-2 text-center text-amber-400">TOTAL</th>
              </tr>
            </thead>
            <tbody>
              {leaders.map(leader => {
                const row = flows[leader];
                const total = row.reduce((s, v) => s + v, 0);
                return (
                  <tr key={leader}>
                    <td className="sticky left-0 bg-[#0f1629] px-2 py-1.5 font-medium text-white whitespace-nowrap">{leader}</td>
                    {row.map((v, i) => (
                      <td key={i} className="px-2 py-1.5 text-center font-mono text-white" style={{ backgroundColor: heatColor(v) }}>{v.toFixed(2)}</td>
                    ))}
                    <td className="px-2 py-1.5 text-center font-mono font-bold text-amber-400">{total.toFixed(2)}</td>
                  </tr>
                );
              })}
              <tr className="border-t-2 border-red-500/30">
                <td className="sticky left-0 bg-[#0f1629] px-2 py-2 font-bold text-red-400">COLUMN TOTAL</td>
                {actors.map((_, colIdx) => {
                  const colTotal = leaders.reduce((s, l) => s + flows[l][colIdx], 0);
                  return <td key={colIdx} className="px-2 py-2 text-center font-mono font-bold text-red-400">{colTotal.toFixed(1)}</td>;
                })}
                <td className="px-2 py-2 text-center font-mono font-bold text-red-400">
                  {leaders.reduce((s, l) => s + flows[l].reduce((a, b) => a + b, 0), 0).toFixed(1)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </GlowCard>

      {/* 100% Ownership Table */}
      <GlowCard glow="amber">
        <h3 className="mb-3 text-sm font-semibold text-amber-400">Rightful Sole Inventorship — 100% Ownership Claims</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-amber-500/10"><tr>
              <th className="px-4 py-2 text-xs text-gray-500">Company</th><th className="px-4 py-2 text-xs text-gray-500">Ticker</th><th className="px-4 py-2 text-xs text-gray-500">Ownership</th><th className="px-4 py-2 text-xs text-gray-500">Patent Families</th><th className="px-4 py-2 text-xs text-gray-500">Est. Value</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{totalIllicitOwnership.map(c => (
              <tr key={c.company}><td className="px-4 py-2 text-white font-semibold">{c.company}</td><td className="px-4 py-2 font-mono text-cyan-400">{c.ticker}</td><td className="px-4 py-2"><span className="rounded-full bg-red-500/20 px-2 py-0.5 text-xs font-bold text-red-400">{c.ownershipPct}%</span></td><td className="px-4 py-2 text-gray-400">{c.patentFamilies.toLocaleString()}</td><td className="px-4 py-2 font-mono text-amber-400">{fmtT(c.valueUsd)}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>

      {/* File Wrapper Anomalies */}
      <GlowCard glow="red">
        <h3 className="mb-3 text-sm font-semibold text-red-400">USPTO File Wrapper Anomalies & Hacking Trails (Byte-by-Byte)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-red-500/10"><tr>
              <th className="px-3 py-2 text-xs text-gray-500">Patent</th><th className="px-3 py-2 text-xs text-gray-500">Anomaly Detected</th><th className="px-3 py-2 text-xs text-gray-500">Hacking Trail</th><th className="px-3 py-2 text-xs text-gray-500">Confidence</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{fileWrapperAnomalies.map(a => (
              <tr key={a.patent}><td className="px-3 py-2 font-mono text-cyan-400">{a.patent}</td><td className="px-3 py-2 text-white">{a.anomaly}</td><td className="px-3 py-2 text-xs text-red-400">{a.hackTrail}</td><td className="px-3 py-2 font-mono text-amber-400">{a.confidence}%</td></tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>
    </section>
  );
}
