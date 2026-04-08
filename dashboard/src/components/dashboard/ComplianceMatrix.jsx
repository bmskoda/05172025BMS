import { useState } from 'react';
import StatusBadge from '../ui/StatusBadge';
import { complianceStandards } from '../../data/compliance';

const categories = ['All', ...new Set(complianceStandards.map(c => c.category))];

export default function ComplianceMatrix() {
  const [cat, setCat] = useState('All');
  const filtered = cat === 'All' ? complianceStandards : complianceStandards.filter(c => c.category === cat);

  return (
    <section id="compliance" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Compliance Matrix ({complianceStandards.length} Standards)</h2>
      <div className="flex flex-wrap gap-2">
        {categories.map(c => (
          <button key={c} onClick={() => setCat(c)} className={`rounded-full px-3 py-1 text-xs font-semibold transition ${cat === c ? 'bg-cyan-500/20 text-cyan-400' : 'bg-white/5 text-gray-500 hover:text-gray-300'}`}>{c}</button>
        ))}
      </div>
      <div className="overflow-x-auto rounded-xl border border-cyan-500/10">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-cyan-500/10 bg-[#0a0e1a]"><tr>
            <th className="px-4 py-3 text-xs text-gray-500">Standard</th><th className="px-4 py-3 text-xs text-gray-500">Code</th><th className="px-4 py-3 text-xs text-gray-500">Category</th><th className="px-4 py-3 text-xs text-gray-500">Status</th><th className="px-4 py-3 text-xs text-gray-500">Description</th>
          </tr></thead>
          <tbody className="divide-y divide-white/5">{filtered.map(c => (
            <tr key={c.code}><td className="px-4 py-2 text-white">{c.name}</td><td className="px-4 py-2 font-mono text-xs text-cyan-400">{c.code}</td><td className="px-4 py-2 text-gray-400">{c.category}</td><td className="px-4 py-2"><StatusBadge status={c.status} /></td><td className="px-4 py-2 text-xs text-gray-500 max-w-xs truncate">{c.description}</td></tr>
          ))}</tbody>
        </table>
      </div>
    </section>
  );
}
