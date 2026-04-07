import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend } from 'recharts';
import GlowCard from '../ui/GlowCard';
import { flowsByYear, flowsByCategory, flowsByAsset } from '../../data/financialFlows';

const fmt = (v) => `$${(v / 1e9).toFixed(0)}B`;
const fmtT = (v) => `$${(v / 1e12).toFixed(1)}T`;

export default function FinancialFlowChart() {
  return (
    <section id="financial" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Financial Flow Analysis</h2>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Illicit Flows by Year (1985–2026)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={flowsByYear}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis dataKey="year" stroke="#64748b" fontSize={11} />
              <YAxis tickFormatter={fmt} stroke="#64748b" fontSize={11} />
              <Tooltip formatter={(v) => fmt(v)} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Area type="monotone" dataKey="patentLicensing" stackId="1" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.4} name="Patent Licensing" />
              <Area type="monotone" dataKey="cryptoLaundering" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.4} name="Crypto Laundering" />
              <Area type="monotone" dataKey="shellTransfers" stackId="1" stroke="#f97316" fill="#f97316" fillOpacity={0.4} name="Shell Transfers" />
              <Area type="monotone" dataKey="cdsManipulation" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.4} name="CDS Manipulation" />
              <Area type="monotone" dataKey="fentanylProceeds" stackId="1" stroke="#eab308" fill="#eab308" fillOpacity={0.4} name="Fentanyl Proceeds" />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </AreaChart>
          </ResponsiveContainer>
        </GlowCard>
        <GlowCard>
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Flows by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={flowsByCategory} cx="50%" cy="50%" innerRadius={60} outerRadius={110} dataKey="value" nameKey="name" label={({ name, pct }) => `${pct}%`} labelLine={false}>
                {flowsByCategory.map((e, i) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Tooltip formatter={fmtT} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </GlowCard>
        <GlowCard className="lg:col-span-2">
          <h3 className="mb-3 text-sm font-semibold text-gray-400">Flows by Asset Type</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={flowsByAsset} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e274d" />
              <XAxis type="number" tickFormatter={fmtT} stroke="#64748b" fontSize={11} />
              <YAxis type="category" dataKey="asset" stroke="#64748b" fontSize={11} width={150} />
              <Tooltip formatter={fmtT} contentStyle={{ background: '#0a0e1a', border: '1px solid #1e274d', borderRadius: 8 }} />
              <Bar dataKey="amount" name="Amount">{flowsByAsset.map((e, i) => <Cell key={i} fill={e.color} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </GlowCard>
      </div>
    </section>
  );
}
