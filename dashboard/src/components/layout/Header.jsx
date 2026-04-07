import { useState, useEffect } from 'react';
import { Shield, Menu, Clock, Lock } from 'lucide-react';

export default function Header({ sidebarOpen, onToggleSidebar }) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const utcString = time.toISOString().replace('T', ' ').slice(0, 19);

  return (
    <header className="w-full">
      <div className="w-full bg-red-700 py-1 text-center text-xs font-bold uppercase tracking-[0.3em] text-white">
        TOP SECRET // ORCON // NOFORN // LAW ENFORCEMENT EYES ONLY
      </div>

      <div className="border-b border-cyan-500/20 bg-[#0a0e1a] px-4 py-3 md:px-6">
        <div className="relative flex items-center justify-between gap-3">
          <div className="flex min-w-0 flex-1 items-center gap-2 md:gap-3">
            <button
              type="button"
              aria-expanded={sidebarOpen}
              aria-label="Toggle navigation menu"
              className="inline-flex shrink-0 items-center justify-center rounded-md p-2 text-cyan-400 transition hover:bg-white/5 md:hidden"
              onClick={onToggleSidebar}
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="flex min-w-0 items-center gap-2 text-cyan-400">
              <Shield className="h-6 w-6 shrink-0 text-cyan-400" aria-hidden />
              <span className="truncate text-lg font-bold">OMEGA v∞.FINAL</span>
            </div>
          </div>

          <div className="pointer-events-none absolute left-1/2 top-1/2 hidden -translate-x-1/2 -translate-y-1/2 md:block">
            <p className="whitespace-nowrap text-center text-sm font-medium uppercase tracking-widest text-gray-400">
              FORENSIC INTELLIGENCE DASHBOARD
            </p>
          </div>

          <div className="flex shrink-0 flex-col items-end gap-0.5 text-right">
            <div className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 shrink-0 text-cyan-400/80" aria-hidden />
              <time
                dateTime={time.toISOString()}
                className="font-mono text-xs text-cyan-400"
              >
                {utcString} UTC
              </time>
            </div>
            <span className="flex max-w-[14rem] items-center justify-end gap-1 truncate text-[0.65rem] leading-tight text-amber-500/90">
              <Lock className="h-3 w-3 shrink-0 text-amber-500/70" aria-hidden />
              ∞.FINAL.CONSOLIDATED.MAXIMUM
            </span>
          </div>
        </div>

        <p className="mt-2 text-center text-sm font-medium uppercase tracking-widest text-gray-400 md:hidden">
          FORENSIC INTELLIGENCE DASHBOARD
        </p>
      </div>
    </header>
  );
}
