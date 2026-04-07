import { timelineEvents } from '../../data/timeline';

export default function InvestigationTimeline() {
  return (
    <section id="timeline" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">Investigation Timeline (1985–2026)</h2>
      <div className="relative space-y-0">
        <div className="absolute left-4 top-0 bottom-0 w-px bg-cyan-500/20 md:left-1/2" />
        {timelineEvents.map((evt, i) => {
          const isLeft = i % 2 === 0;
          return (
            <div key={i} className={`relative flex items-start gap-4 py-4 ${isLeft ? 'md:flex-row' : 'md:flex-row-reverse'}`}>
              <div className={`hidden md:block md:w-1/2 ${isLeft ? 'md:text-right md:pr-8' : 'md:text-left md:pl-8'}`}>
                <p className="text-xs font-mono text-gray-500">{evt.date}</p>
                <h3 className="mt-1 text-sm font-bold text-white">{evt.title}</h3>
                <p className="mt-1 text-xs leading-relaxed text-gray-400">{evt.desc}</p>
              </div>
              <div className="absolute left-4 md:left-1/2 -translate-x-1/2 z-10">
                <div className="h-3 w-3 rounded-full border-2 border-[#0a0e1a]" style={{ backgroundColor: evt.color }} />
              </div>
              <div className="ml-10 md:hidden">
                <p className="text-xs font-mono text-gray-500">{evt.date}</p>
                <h3 className="mt-1 text-sm font-bold text-white">{evt.title}</h3>
                <p className="mt-1 text-xs leading-relaxed text-gray-400">{evt.desc}</p>
              </div>
              <div className={`hidden md:block md:w-1/2 ${isLeft ? '' : ''}`} />
            </div>
          );
        })}
      </div>
    </section>
  );
}
