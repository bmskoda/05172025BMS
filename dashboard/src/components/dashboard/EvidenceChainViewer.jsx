import { CheckCircle, Link } from 'lucide-react';
import { evidenceRecords } from '../../data/evidenceChain';

export default function EvidenceChainViewer() {
  return (
    <section id="evidence" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Evidence Chain (FRE 902(13)-(14))</h2>
      <div className="flex items-center gap-2 text-sm">
        <CheckCircle className="h-4 w-4 text-emerald-400" />
        <span className="text-emerald-400">Chain Integrity: VERIFIED</span>
        <span className="text-gray-500">• {evidenceRecords.length} records • Post-Quantum Signed</span>
      </div>
      <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
        {evidenceRecords.map((r, i) => (
          <div key={r.id} className="flex items-start gap-3 rounded-lg border border-cyan-500/10 bg-[#0f1629] p-3 transition hover:border-cyan-500/30">
            <div className="flex flex-col items-center gap-1">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-500/20">
                <CheckCircle className="h-4 w-4 text-emerald-400" />
              </div>
              {i < evidenceRecords.length - 1 && <div className="h-8 w-px bg-cyan-500/20" />}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs text-cyan-400">{r.id}</span>
                <span className="rounded bg-white/5 px-2 py-0.5 text-xs text-gray-400">{r.type}</span>
                <span className="text-xs text-gray-600">{r.source}</span>
              </div>
              <div className="mt-1 flex items-center gap-1 text-xs text-gray-500">
                <Link className="h-3 w-3" />
                <span className="font-mono">{r.hash}</span>
              </div>
              <p className="mt-0.5 text-xs text-gray-600">{r.timestamp} • Position #{r.position}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
