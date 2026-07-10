import { ShieldCheck, CheckCircle2, Lock } from 'lucide-react';
import GlowCard from '../ui/GlowCard';
import AnimatedCounter from '../ui/AnimatedCounter';
import StatusBadge from '../ui/StatusBadge';
import { hardeningStats, prosecutorialDimensions, integrityChecks, executiveTargets } from '../../data/corpusHardening';

export default function CorpusHardening() {
  return (
    <section id="hardening" className="space-y-6">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Corpus-Completeness Hardening Gate</h2>
      <p className="text-xs text-gray-500">Deterministic 99.99% completeness verification • Auto-remediation • U.S. Supreme Court quality-exceeding integrity • Court-ready evidence archive</p>

      {/* Gate Status Banner */}
      <GlowCard glow="emerald">
        <div className="flex flex-col items-center gap-3 py-2 sm:flex-row sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-emerald-500/20 p-3"><ShieldCheck className="h-7 w-7 text-emerald-400" /></div>
            <div>
              <p className="text-2xl font-bold text-emerald-400">{hardeningStats.achievedCompleteness}% COMPLETE</p>
              <p className="text-xs text-gray-500">Threshold: {hardeningStats.completenessThreshold}% • {hardeningStats.dimensionsResolved}/{hardeningStats.dimensionsTotal} dimensions resolved</p>
            </div>
          </div>
          <div className="text-center sm:text-right">
            <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-sm font-bold text-emerald-400">GATE PASSED</span>
            <p className="mt-1 text-xs text-cyan-400">{hardeningStats.prosecutorialReferral}</p>
          </div>
        </div>
      </GlowCard>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <GlowCard glow="cyan"><p className="text-[10px] text-gray-500">Evidence Records</p><AnimatedCounter value={hardeningStats.totalEvidenceRecords} className="text-lg font-bold text-cyan-400" /></GlowCard>
        <GlowCard glow="emerald"><p className="text-[10px] text-gray-500">Auto-Remediations</p><AnimatedCounter value={hardeningStats.autoRemediations} className="text-lg font-bold text-emerald-400" /></GlowCard>
        <GlowCard glow="purple"><p className="text-[10px] text-gray-500">Dimensions</p><AnimatedCounter value={hardeningStats.dimensionsTotal} className="text-lg font-bold text-purple-400" /></GlowCard>
        <GlowCard glow="amber"><p className="text-[10px] text-gray-500">Integrity Checks</p><AnimatedCounter value={integrityChecks.length} className="text-lg font-bold text-amber-400" /></GlowCard>
        <GlowCard glow="emerald"><p className="text-[10px] text-gray-500">Archive Status</p><p className="mt-1 text-sm font-bold text-emerald-400">COURT-READY</p></GlowCard>
      </div>

      {/* Prosecutorial Dimensions Grid */}
      <GlowCard>
        <h3 className="mb-3 text-sm font-semibold text-gray-400">Prosecutorial Dimensions — Zero-Gap Coverage</h3>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {prosecutorialDimensions.map(d => (
            <div key={d.dimension} className="flex items-center justify-between rounded-lg border border-emerald-500/10 bg-[#0a0e1a] px-3 py-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
                <span className="text-xs text-white">{d.dimension}</span>
              </div>
              <span className="font-mono text-xs text-gray-500">{d.records.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </GlowCard>

      {/* Integrity Checks */}
      <GlowCard glow="emerald">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-emerald-400"><Lock className="h-4 w-4" />Integrity Verification (Supreme Court Quality Exceeding)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-emerald-500/10"><tr>
              <th className="px-3 py-2 text-xs text-gray-500">Integrity Check</th><th className="px-3 py-2 text-xs text-gray-500">Standard</th><th className="px-3 py-2 text-xs text-gray-500">Status</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{integrityChecks.map(c => (
              <tr key={c.check}><td className="px-3 py-2 text-white">{c.check}</td><td className="px-3 py-2 text-xs text-gray-400">{c.standard}</td><td className="px-3 py-2"><span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-xs font-bold text-emerald-400">{c.status}</span></td></tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>

      {/* Executive Targets */}
      <GlowCard glow="red">
        <h3 className="mb-3 text-sm font-semibold text-red-400">Executive Target Matrix — IP + Blockchain Forensics (100% Resolved)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-red-500/10"><tr>
              <th className="px-3 py-2 text-xs text-gray-500">Entity</th><th className="px-3 py-2 text-xs text-gray-500">Executive</th><th className="px-3 py-2 text-xs text-gray-500">Ownership</th><th className="px-3 py-2 text-xs text-gray-500">IP Status</th><th className="px-3 py-2 text-xs text-gray-500">Blockchain</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">{executiveTargets.map(t => (
              <tr key={t.executive}><td className="px-3 py-2 text-white font-semibold">{t.entity}</td><td className="px-3 py-2 text-gray-300">{t.executive}</td><td className="px-3 py-2"><span className="rounded-full bg-red-500/20 px-2 py-0.5 text-xs font-bold text-red-400">{t.ownershipPct}%</span></td><td className="px-3 py-2"><span className="rounded bg-red-500/10 px-2 py-0.5 text-xs text-red-400">{t.ipStatus}</span></td><td className="px-3 py-2"><span className="rounded bg-amber-500/10 px-2 py-0.5 text-xs text-amber-400">{t.blockchainStatus}</span></td></tr>
            ))}</tbody>
          </table>
        </div>
      </GlowCard>
    </section>
  );
}
