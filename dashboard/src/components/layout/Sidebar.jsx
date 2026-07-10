import {
  LayoutDashboard,
  Network,
  Users,
  DollarSign,
  FileText,
  Link,
  Building2,
  Skull,
  ShieldCheck,
  Bot,
  Calendar,
  Database,
  CheckSquare,
  X,
  Globe,
  CreditCard,
  AlertTriangle,
  Scroll,
  UserX,
  Landmark,
  EyeOff,
} from 'lucide-react';

export default function Sidebar({ isOpen, onClose, activeSection, onNavigate }) {
  const sections = [
    { id: 'executive', label: 'Executive Summary', icon: LayoutDashboard },
    { id: 'network', label: 'RICO Network', icon: Network },
    { id: 'leaders', label: 'RICO Leaders', icon: Users },
    { id: 'financial', label: 'Financial Flows', icon: DollarSign },
    { id: 'patents', label: 'Patent Analytics', icon: FileText },
    { id: 'wipo', label: '194 WIPO Jurisdictions', icon: Globe },
    { id: 'isincusip', label: 'ISIN / CUSIP Exposure', icon: CreditCard },
    { id: 'capture', label: 'Regulatory Capture', icon: AlertTriangle },
    { id: 'tokenized', label: 'Tokenized IP Tracing', icon: Network },
    { id: 'cyberdust', label: 'Cyber Dust Detection', icon: AlertTriangle },
    { id: 'synthetic', label: 'Synthetic Inventors', icon: UserX },
    { id: 'treasury', label: 'Treasury / GENIUS Act', icon: Landmark },
    { id: 'erasure', label: 'Citation Erasure', icon: EyeOff },
    { id: 'blockchain', label: 'Blockchain Forensics', icon: Link },
    { id: 'shellcorps', label: 'Shell Corporations', icon: Building2 },
    { id: 'fentanyl', label: 'Fentanyl Disruption', icon: Skull },
    { id: 'evidence', label: 'Evidence Chain', icon: ShieldCheck },
    { id: 'agents', label: 'Agent Swarm', icon: Bot },
    { id: 'timeline', label: 'Investigation Timeline', icon: Calendar },
    { id: 'sources', label: 'Data Sources', icon: Database },
    { id: 'compliance', label: 'Compliance Matrix', icon: CheckSquare },
    { id: 'hardening', label: 'Corpus Hardening Gate', icon: ShieldCheck },
    { id: 'report', label: 'Report & Press Release', icon: Scroll },
  ];

  const handleNav = (id) => {
    onNavigate(id);
    onClose();
  };

  return (
    <>
      {isOpen ? (
        <button
          type="button"
          aria-label="Close menu"
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-[1px] md:hidden"
          onClick={onClose}
        />
      ) : null}

      <aside
        className={[
          'fixed left-0 top-0 z-50 flex h-screen w-64 flex-col border-r border-cyan-500/10 bg-[#0a0e1a] pt-4 transition-transform duration-300 ease-out',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          'md:translate-x-0',
        ].join(' ')}
      >
        <div className="relative flex shrink-0 items-center justify-end px-2 pb-2 md:hidden">
          <button
            type="button"
            aria-label="Close sidebar"
            className="rounded-md p-2 text-gray-400 transition hover:bg-white/5 hover:text-cyan-400"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="min-h-0 flex-1 overflow-y-auto pb-6">
          <ul className="space-y-0.5">
            {sections.map(({ id, label, icon: Icon }) => {
              const active = activeSection === id;
              return (
                <li key={id}>
                  <button
                    type="button"
                    onClick={() => handleNav(id)}
                    className={[
                      'mx-2 flex w-[calc(100%-1rem)] cursor-pointer items-center gap-3 rounded-lg px-4 py-2.5 text-left text-sm transition',
                      active
                        ? 'border-l-2 border-cyan-400 bg-cyan-500/10 text-cyan-400'
                        : 'border-l-2 border-transparent text-gray-500 hover:bg-white/5 hover:text-gray-300',
                    ].join(' ')}
                  >
                    <Icon className="h-4 w-4 shrink-0" aria-hidden />
                    <span className="leading-snug">{label}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="mt-auto border-t border-cyan-500/10 px-4 py-4">
          <p className="text-center text-xs font-semibold uppercase tracking-widest text-red-500">
            CLASSIFIED
          </p>
          <p className="mt-1 text-center text-lg text-amber-500/80" aria-hidden>
            Ω
          </p>
        </div>
      </aside>
    </>
  );
}
