import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LineChart, Line } from 'recharts';
import GlowCard from '../ui/GlowCard';
import { captureIndicators, captureByCategory, captureTimeline } from '../../data/regulatoryCapture';

export default function RegulatoryCapture() {
  return (
    <section id="capture" className="space-y-4">
      <h2 className="text-xl font-bold text-red-400 uppercase tracking-wider">Sinaloa Cartel — Global Regulatory Capture</h2>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlowCard glow="red">
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Capture by Category</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={captureByCategory} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis type="number" stroke="#64748b" fontSize={11} />
              <YAxis type="category" dataKey="category" stroke="#64748b" fontSize={10} width={140} />
              <Tooltip contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Bar dataKey="offices" name="Offices Affected">{captureByCategory.map((e, i) => <Cell key={i} fill={e.color} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </GlowCard>
        <GlowCard glow="red">
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Capture Expansion Timeline (2005–2026)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={captureTimeline}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis dataKey="year" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Line type="monotone" dataKey="offices" stroke="#ef4444" strokeWidth={2} dot={{ r: 4, fill: '#ef4444' }} name="Compromised Offices" />
            </LineChart>
          </ResponsiveContainer>
        </GlowCard>
      </div>

      <GlowCard glow="red">
        <h3 className="mb-3 text-sm font-semibold text-red-400">Verified Capture Indicators</h3>
        <div className="space-y-3">
          {captureIndicators.map((ind, i) => (
            <div key={i} className="rounded-lg border border-red-500/10 bg-[#0a0e1a] p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-white">{ind.indicator}</p>
                  <p className="mt-1 text-xs text-gray-500">Source: <span className="text-cyan-400">{ind.source}</span></p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {ind.jurisdictions.map(j => <span key={j} className="rounded bg-white/5 px-1.5 py-0.5 text-xs font-mono text-gray-400">{j}</span>)}
                  </div>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${ind.confidence === 'High' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>{ind.confidence}</span>
                  <span className="text-xs text-gray-600">{ind.category}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </GlowCard>
    </section>
  );
}
