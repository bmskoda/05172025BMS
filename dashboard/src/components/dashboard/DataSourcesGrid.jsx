import { useState } from 'react';
import StatusBadge from '../ui/StatusBadge';
import { dataSources } from '../../data/dataSources';

const categories = ['All', ...new Set(dataSources.map(d => d.category))];

export default function DataSourcesGrid() {
  const [cat, setCat] = useState('All');
  const filtered = cat === 'All' ? dataSources : dataSources.filter(d => d.category === cat);

  return (
    <section id="sources" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Data Sources ({dataSources.length} APIs)</h2>
      <div className="flex flex-wrap gap-2">
        {categories.map(c => (
          <button key={c} onClick={() => setCat(c)} className={`rounded-full px-3 py-1 text-xs font-semibold transition ${cat === c ? 'bg-cyan-500/20 text-cyan-400' : 'bg-white/5 text-gray-500 hover:text-gray-300'}`}>{c}</button>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map(d => (
          <div key={d.name} className="rounded-lg border border-cyan-500/10 bg-[#0f1629] p-3 transition hover:border-cyan-500/30">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white text-sm">{d.name}</span>
              <StatusBadge status={d.status} />
            </div>
            <p className="mt-1 text-xs text-gray-500">{d.category}</p>
            <p className="mt-1 font-mono text-xs text-cyan-400/70 truncate">{d.endpoint}</p>
            <p className="mt-2 text-xs text-gray-400 leading-relaxed">{d.purpose}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
