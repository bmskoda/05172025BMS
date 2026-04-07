import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';
import GlowCard from '../ui/GlowCard';
import { shellsByJurisdiction, shellDetectionTimeline } from '../../data/shellCorps';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Legend } from 'recharts';

const treemapData = shellsByJurisdiction.map(s => ({ name: s.jurisdiction, size: s.count, fill: s.color }));

const CustomContent = (props) => {
  const { x, y, width, height, name, fill } = props;
  if (width < 30 || height < 20) return null;
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} fill={fill} fillOpacity={0.7} stroke="#0a0e1a" strokeWidth={2} rx={4} />
      {width > 60 && height > 30 && <text x={x + width / 2} y={y + height / 2} textAnchor="middle" dominantBaseline="central" fill="white" fontSize={Math.min(11, width / 10)}>{name?.split(',')[0]}</text>}
    </g>
  );
};

export default function ShellCorpMap() {
  return (
    <section id="shellcorps" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Shell Corporation Analysis</h2>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Distribution by Jurisdiction (31.5M Total)</h3>
          <ResponsiveContainer width="100%" height={350}>
            <Treemap data={treemapData} dataKey="size" nameKey="name" content={<CustomContent />}>
              <Tooltip formatter={(v) => `${(v / 1e6).toFixed(1)}M shells`} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
            </Treemap>
          </ResponsiveContainer>
        </GlowCard>
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Shell Detection vs. Total Over Time</h3>
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={shellDetectionTimeline}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis dataKey="year" stroke="#64748b" fontSize={11} />
              <YAxis tickFormatter={v => `${(v / 1e6).toFixed(0)}M`} stroke="#64748b" fontSize={11} />
              <Tooltip formatter={v => `${(v / 1e6).toFixed(1)}M`} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Area type="monotone" dataKey="total" stroke="#f97316" fill="#f97316" fillOpacity={0.2} name="Total Shell Corps" />
              <Area type="monotone" dataKey="detected" stroke="#10b981" fill="#10b981" fillOpacity={0.3} name="Detected" />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </AreaChart>
          </ResponsiveContainer>
        </GlowCard>
      </div>
      <div className="overflow-x-auto rounded-xl border border-cyan-500/10">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-cyan-500/10 bg-[#0a0e1a]"><tr>
            <th className="px-4 py-3 text-xs text-gray-500">Jurisdiction</th><th className="px-4 py-3 text-xs text-gray-500">Shell Corps</th><th className="px-4 py-3 text-xs text-gray-500">% of Total</th><th className="px-4 py-3 text-xs text-gray-500">Detection Rate</th>
          </tr></thead>
          <tbody className="divide-y divide-white/5">{shellsByJurisdiction.map(s => (
            <tr key={s.jurisdiction}><td className="px-4 py-2 text-white">{s.jurisdiction}</td><td className="px-4 py-2 font-mono text-cyan-400">{(s.count / 1e6).toFixed(1)}M</td><td className="px-4 py-2 text-gray-400">{s.pct}%</td><td className="px-4 py-2"><div className="h-2 w-24 rounded-full bg-gray-700"><div className="h-2 rounded-full bg-emerald-500" style={{ width: `${s.detectionRate * 100}%` }} /></div></td></tr>
          ))}</tbody>
        </table>
      </div>
    </section>
  );
}
