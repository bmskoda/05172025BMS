export default function GlowCard({ children, className = '', glow = 'cyan' }) {
  const glowColors = {
    cyan: 'shadow-cyan-500/10 hover:shadow-cyan-500/20 border-cyan-500/20 hover:border-cyan-500/40',
    red: 'shadow-red-500/10 hover:shadow-red-500/20 border-red-500/20 hover:border-red-500/40',
    amber: 'shadow-amber-500/10 hover:shadow-amber-500/20 border-amber-500/20 hover:border-amber-500/40',
    emerald: 'shadow-emerald-500/10 hover:shadow-emerald-500/20 border-emerald-500/20 hover:border-emerald-500/40',
    purple: 'shadow-purple-500/10 hover:shadow-purple-500/20 border-purple-500/20 hover:border-purple-500/40',
  };
  const g = glowColors[glow] || glowColors.cyan;
  return (
    <div className={`rounded-xl border bg-[#0f1629] p-5 shadow-lg transition-all duration-300 ${g} ${className}`}>
      {children}
    </div>
  );
}
