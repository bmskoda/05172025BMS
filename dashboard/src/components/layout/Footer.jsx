export default function Footer() {
  return (
    <footer className="w-full">
      <div className="border-t border-cyan-500/10 bg-[#0a0e1a] px-6 py-4">
        <div className="flex flex-col items-center justify-between gap-4 text-center md:flex-row md:text-left">
          <div className="flex items-center justify-center gap-2 md:justify-start">
            <span
              className="inline-block h-2 w-2 shrink-0 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"
              aria-hidden
            />
            <span className="text-xs text-emerald-400">
              Evidence Chain Integrity: VERIFIED ✓
            </span>
          </div>

          <p className="text-xs text-gray-600">
            OMEGA v∞.FINAL | © 2026 DOJ/FBI/CIA Joint Task Force
          </p>

          <p className="text-xs text-red-400 md:text-right">
            Classification: TS//ORCON//NOFORN
          </p>
        </div>
      </div>

      <div className="w-full bg-red-700 py-1 text-center text-xs font-bold uppercase tracking-[0.3em] text-white">
        TOP SECRET // ORCON // NOFORN // LAW ENFORCEMENT EYES ONLY
      </div>
    </footer>
  );
}
