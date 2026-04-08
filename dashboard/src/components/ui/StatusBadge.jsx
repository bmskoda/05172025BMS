const colorMap = {
  CRITICAL: 'bg-red-500/20 text-red-400 border-red-500/40',
  HIGH: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
  MEDIUM: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
  LOW: 'bg-green-500/20 text-green-400 border-green-500/40',
  active: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  degraded: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
  offline: 'bg-red-500/20 text-red-400 border-red-500/40',
  Compliant: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  Pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
};

export default function StatusBadge({ status }) {
  const cls = colorMap[status] || 'bg-gray-500/20 text-gray-400 border-gray-500/40';
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${cls}`}>
      {status}
    </span>
  );
}
