import { FileText, AlertTriangle, BookOpen, Megaphone } from 'lucide-react';
import GlowCard from '../ui/GlowCard';
import StatusBadge from '../ui/StatusBadge';
import { reportMeta, keyFindings, recommendations, pressRelease } from '../../data/forensicReport';

export default function ForensicReport() {
  return (
    <section id="report" className="space-y-6">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Forensic Report & Press Release</h2>

      {/* Report Header */}
      <GlowCard glow="cyan">
        <div className="flex items-start gap-4">
          <div className="rounded-lg bg-cyan-500/10 p-3"><FileText className="h-6 w-6 text-cyan-400" /></div>
          <div className="min-w-0 flex-1">
            <h3 className="text-lg font-bold text-white">{reportMeta.title}</h3>
            <p className="mt-1 text-xs text-gray-500">Case: <span className="text-cyan-400 font-mono">{reportMeta.caseNumber}</span> • Date: {reportMeta.date} • Version: {reportMeta.version}</p>
            <p className="mt-1 text-xs text-red-400">{reportMeta.classification}</p>
            <div className="mt-2 flex flex-wrap gap-1">{reportMeta.agencies.map(a => <span key={a} className="rounded bg-white/5 px-2 py-0.5 text-xs font-mono text-cyan-400">{a}</span>)}</div>
          </div>
        </div>
      </GlowCard>

      {/* Key Findings */}
      <GlowCard glow="red">
        <div className="flex items-center gap-2 mb-4"><AlertTriangle className="h-5 w-5 text-red-400" /><h3 className="text-lg font-bold text-red-400">Key Findings</h3></div>
        <div className="space-y-3">
          {keyFindings.map((f, i) => (
            <div key={i} className="rounded-lg border border-white/5 bg-[#0a0e1a] p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-semibold text-white">{f.category}</span>
                <StatusBadge status={f.severity} />
              </div>
              <p className="text-xs leading-relaxed text-gray-400">{f.finding}</p>
            </div>
          ))}
        </div>
      </GlowCard>

      {/* Recommendations */}
      <GlowCard glow="emerald">
        <div className="flex items-center gap-2 mb-4"><BookOpen className="h-5 w-5 text-emerald-400" /><h3 className="text-lg font-bold text-emerald-400">Recommendations</h3></div>
        <ol className="list-decimal pl-5 space-y-2">
          {recommendations.map((r, i) => <li key={i} className="text-sm text-gray-300">{r}</li>)}
        </ol>
      </GlowCard>

      {/* Press Release */}
      <GlowCard glow="amber">
        <div className="flex items-center gap-2 mb-4"><Megaphone className="h-5 w-5 text-amber-400" /><h3 className="text-lg font-bold text-amber-400">FOR IMMEDIATE RELEASE</h3></div>
        <div className="rounded-lg border border-amber-500/10 bg-[#0a0e1a] p-4">
          <p className="text-xs text-gray-500 mb-2">{pressRelease.date} • {pressRelease.contact} • Operation: <span className="text-amber-400">{pressRelease.operationName}</span></p>
          <h4 className="text-sm font-bold text-white mb-3">{pressRelease.headline}</h4>
          <div className="space-y-3">
            {pressRelease.body.map((para, i) => <p key={i} className="text-xs leading-relaxed text-gray-400">{para}</p>)}
          </div>
        </div>
      </GlowCard>
    </section>
  );
}
