import { DollarSign, FileText, Users, Building2, Shield, Database, Scale, UserX, Landmark, Ghost, BookOpen, Gavel } from 'lucide-react';
import AnimatedCounter from '../ui/AnimatedCounter';
import GlowCard from '../ui/GlowCard';
import { kpiCards } from '../../data/metrics';

const iconMap = { DollarSign, FileText, Users, Building2, Shield, Database, Scale, UserX, Landmark, Ghost, BookOpen, Gavel };
const glowMap = { crimson: 'red', amber: 'amber', red: 'red', purple: 'purple', orange: 'amber', emerald: 'emerald', green: 'emerald', cyan: 'cyan', gold: 'amber', rose: 'red', fuchsia: 'purple', teal: 'cyan' };

export default function ExecutiveSummary() {
  return (
    <section id="executive" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Executive Summary</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {kpiCards.map((card) => {
          const Icon = iconMap[card.icon] || Database;
          return (
            <GlowCard key={card.id} glow={glowMap[card.color] || 'cyan'}>
              <div className="flex items-start justify-between">
                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase tracking-wider text-gray-500">{card.label}</p>
                  <AnimatedCounter value={card.value} prefix={card.prefix || ''} suffix={card.suffix || ''} decimals={card.decimals || 0} className="mt-1 block text-2xl font-bold text-white" duration={2500} />
                </div>
                <div className="rounded-lg bg-white/5 p-2"><Icon className="h-5 w-5 text-cyan-400" /></div>
              </div>
            </GlowCard>
          );
        })}
      </div>
    </section>
  );
}
