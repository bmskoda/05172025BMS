import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend } from 'recharts';
import GlowCard from '../ui/GlowCard';
import AnimatedCounter from '../ui/AnimatedCounter';
import { patentsByOffice, patentsByYear, patentsByCategory } from '../../data/patentData';

export default function PatentAnalytics() {
  return (
    <section id="patents" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Patent Theft Analytics</h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <GlowCard><p className="text-xs text-gray-500">Total Families</p><AnimatedCounter value={14213} className="text-2xl font-bold text-white" /></GlowCard>
        <GlowCard><p className="text-xs text-gray-500">Patent Offices</p><AnimatedCounter value={11} className="text-2xl font-bold text-white" /></GlowCard>
        <GlowCard><p className="text-xs text-gray-500">WIPO Jurisdictions</p><AnimatedCounter value={194} className="text-2xl font-bold text-white" /></GlowCard>
        <GlowCard><p className="text-xs text-gray-500">Peak Year</p><p className="mt-1 text-2xl font-bold text-white">2019</p></GlowCard>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Stolen Patents by Office</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={patentsByOffice}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis dataKey="code" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Bar dataKey="count" name="Patents Stolen">{patentsByOffice.map((e, i) => <Cell key={i} fill={e.color} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </GlowCard>
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Cumulative Patent Theft (1985–2025)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={patentsByYear}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis dataKey="year" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Line type="monotone" dataKey="cumulative" stroke="#06b6d4" strokeWidth={2} dot={false} name="Cumulative Stolen" />
              <Line type="monotone" dataKey="stolen" stroke="#ef4444" strokeWidth={1} dot={{ r: 3 }} name="Per Period" />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </LineChart>
          </ResponsiveContainer>
        </GlowCard>
        <GlowCard className="lg:col-span-2">
          <h3 className="mb-3 text-sm font-semibold text-gray-400">By Technology Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={patentsByCategory} cx="50%" cy="50%" innerRadius={50} outerRadius={110} dataKey="count" nameKey="category" label={({ category, pct }) => `${category.split('/')[0]} ${pct}%`} labelLine={false}>
                {patentsByCategory.map((e, i) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </GlowCard>
      </div>
    </section>
  );
}
