import { useState, useMemo } from 'react';
import { Search, ChevronDown, ChevronUp } from 'lucide-react';
import StatusBadge from '../ui/StatusBadge';
import { ricoLeaders, professionalEnablers, criminalOrganizations } from '../../data/ricoLeaders';

export default function RicoLeadersTable() {
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState('financialExposure');
  const [sortDir, setSortDir] = useState('desc');
  const [filter, setFilter] = useState('ALL');
  const [expanded, setExpanded] = useState(null);

  const filtered = useMemo(() => {
    let list = ricoLeaders;
    if (filter !== 'ALL') list = list.filter(l => l.riskLevel === filter);
    if (search) list = list.filter(l => l.name.toLowerCase().includes(search.toLowerCase()) || l.organization.toLowerCase().includes(search.toLowerCase()));
    list = [...list].sort((a, b) => { const m = sortDir === 'asc' ? 1 : -1; return a[sortKey] > b[sortKey] ? m : -m; });
    return list;
  }, [search, sortKey, sortDir, filter]);

  const toggleSort = (key) => { if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc'); else { setSortKey(key); setSortDir('desc'); } };
  const SortIcon = ({ col }) => sortKey === col ? (sortDir === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />) : null;

  return (
    <section id="leaders" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">RICO Enterprise Leaders</h2>
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input type="text" placeholder="Search leaders..." value={search} onChange={e => setSearch(e.target.value)} className="w-full rounded-lg border border-cyan-500/20 bg-[#0f1629] py-2 pl-10 pr-4 text-sm text-gray-300 placeholder-gray-600 focus:border-cyan-500/50 focus:outline-none" />
        </div>
        {['ALL', 'CRITICAL', 'HIGH'].map(f => (
          <button key={f} onClick={() => setFilter(f)} className={`rounded-full px-3 py-1 text-xs font-semibold transition ${filter === f ? 'bg-cyan-500/20 text-cyan-400' : 'bg-white/5 text-gray-500 hover:text-gray-300'}`}>{f}</button>
        ))}
      </div>
      <div className="overflow-x-auto rounded-xl border border-cyan-500/10">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-cyan-500/10 bg-[#0a0e1a]">
            <tr>
              {[['name','Name'],['role','Role'],['organization','Organization'],['jurisdiction','Jurisdiction'],['riskLevel','Risk'],['financialExposure','Exposure ($)'],['connections','Connections']].map(([k,l])=>(
                <th key={k} className="cursor-pointer px-4 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500 hover:text-cyan-400" onClick={() => toggleSort(k)}>
                  <span className="flex items-center gap-1">{l}<SortIcon col={k} /></span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filtered.map(l => (
              <tr key={l.id} className="cursor-pointer transition hover:bg-white/[0.02]" onClick={() => setExpanded(expanded === l.id ? null : l.id)}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${l.riskLevel === 'CRITICAL' ? 'bg-red-500/20 text-red-400' : 'bg-orange-500/20 text-orange-400'}`}>{l.initials}</div>
                    <span className="font-medium text-white">{l.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-400">{l.role}</td>
                <td className="px-4 py-3 text-gray-400 max-w-[180px] truncate">{l.organization}</td>
                <td className="px-4 py-3 text-gray-400">{l.jurisdiction}</td>
                <td className="px-4 py-3"><StatusBadge status={l.riskLevel} /></td>
                <td className="px-4 py-3 font-mono text-amber-400">${(l.financialExposure / 1e12).toFixed(1)}T</td>
                <td className="px-4 py-3 text-gray-400">{l.connections.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {expanded && (() => { const l = ricoLeaders.find(x => x.id === expanded); if (!l) return null; return (
        <div className="rounded-xl border border-cyan-500/10 bg-[#0f1629] p-4 space-y-3">
          <h3 className="text-lg font-bold text-white">{l.name} — Detailed Allegations</h3>
          <ul className="list-disc pl-5 space-y-1 text-sm text-gray-400">{l.allegations.map((a,i) => <li key={i}>{a}</li>)}</ul>
          <div><span className="text-xs text-gray-500">Linked Entities: </span><span className="text-xs text-cyan-400">{l.linkedEntities.join(', ')}</span></div>
        </div>
      ); })()}

      <h3 className="mt-8 text-lg font-bold text-amber-400 uppercase tracking-wider">Professional Enablers</h3>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {professionalEnablers.map(e => (
          <div key={e.firm} className="rounded-xl border border-amber-500/10 bg-[#0f1629] p-4">
            <p className="font-semibold text-white">{e.firm}</p>
            <p className="text-xs text-gray-500 mt-1">{e.type}</p>
            <p className="text-xs text-gray-400 mt-2">Key Personnel: <span className="text-amber-400">{e.personnel.join(', ')}</span></p>
            <div className="mt-2 flex gap-4 text-xs"><span className="text-red-400">Dual Rep: {e.dualRepCount.toLocaleString()}</span><span className="text-fuchsia-400">Impersonation: {e.judicialImpCount.toLocaleString()}</span></div>
          </div>
        ))}
      </div>

      <h3 className="mt-8 text-lg font-bold text-red-400 uppercase tracking-wider">Criminal Organizations</h3>
      <div className="overflow-x-auto rounded-xl border border-red-500/10">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-red-500/10 bg-[#0a0e1a]"><tr>
            <th className="px-4 py-3 text-xs text-gray-500">Organization</th><th className="px-4 py-3 text-xs text-gray-500">Category</th><th className="px-4 py-3 text-xs text-gray-500">Risk</th><th className="px-4 py-3 text-xs text-gray-500">Wallets</th><th className="px-4 py-3 text-xs text-gray-500">Received (USD)</th>
          </tr></thead>
          <tbody className="divide-y divide-white/5">{criminalOrganizations.map(o => (
            <tr key={o.name}><td className="px-4 py-2 text-white">{o.name}</td><td className="px-4 py-2 text-gray-400">{o.category}</td><td className="px-4 py-2"><StatusBadge status={o.riskLevel} /></td><td className="px-4 py-2 text-gray-400">{o.wallets}</td><td className="px-4 py-2 font-mono text-red-400">${(o.receivedUsd / 1e12).toFixed(1)}T</td></tr>
          ))}</tbody>
        </table>
      </div>
    </section>
  );
}
