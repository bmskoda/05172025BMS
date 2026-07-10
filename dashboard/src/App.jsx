import { useState, useEffect, useCallback } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import Footer from './components/layout/Footer';
import ExecutiveSummary from './components/dashboard/ExecutiveSummary';
import RicoNetworkGraph from './components/dashboard/RicoNetworkGraph';
import RicoLeadersTable from './components/dashboard/RicoLeadersTable';
import FinancialFlowChart from './components/dashboard/FinancialFlowChart';
import PatentAnalytics from './components/dashboard/PatentAnalytics';
import BlockchainForensics from './components/dashboard/BlockchainForensics';
import ShellCorpMap from './components/dashboard/ShellCorpMap';
import FentanylDashboard from './components/dashboard/FentanylDashboard';
import EvidenceChainViewer from './components/dashboard/EvidenceChainViewer';
import AgentSwarmPanel from './components/dashboard/AgentSwarmPanel';
import InvestigationTimeline from './components/dashboard/InvestigationTimeline';
import DataSourcesGrid from './components/dashboard/DataSourcesGrid';
import ComplianceMatrix from './components/dashboard/ComplianceMatrix';
import WipoJurisdictionMap from './components/dashboard/WipoJurisdictionMap';
import IsinCusipPanel from './components/dashboard/IsinCusipPanel';
import RegulatoryCapture from './components/dashboard/RegulatoryCapture';
import ForensicReport from './components/dashboard/ForensicReport';
import TokenizedIPTracing from './components/dashboard/TokenizedIPTracing';
import CyberDustDetection from './components/dashboard/CyberDustDetection';
import SyntheticInventors from './components/dashboard/SyntheticInventors';
import TreasuryWalletFreeze from './components/dashboard/TreasuryWalletFreeze';
import CitationErasure from './components/dashboard/CitationErasure';

const SECTIONS = [
  'executive', 'network', 'leaders', 'financial', 'patents',
  'wipo', 'isincusip', 'capture', 'tokenized',
  'cyberdust', 'synthetic', 'treasury', 'erasure',
  'blockchain', 'shellcorps', 'fentanyl', 'evidence',
  'agents', 'timeline', 'sources', 'compliance', 'report',
];

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('executive');

  const handleNavigate = useCallback((id) => {
    setActiveSection(id);
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
            break;
          }
        }
      },
      { rootMargin: '-20% 0px -70% 0px', threshold: 0 }
    );
    SECTIONS.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);

  return (
    <div className="min-h-screen bg-[#050816] text-gray-200">
      <div className="classified-watermark">TOP SECRET</div>
      <Header sidebarOpen={sidebarOpen} onToggleSidebar={() => setSidebarOpen((o) => !o)} />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} activeSection={activeSection} onNavigate={handleNavigate} />

      <main className="pb-8 pt-4 md:ml-64">
        <div className="mx-auto max-w-7xl space-y-12 px-4 md:px-6">
          <ExecutiveSummary />
          <div className="section-divider" />
          <RicoNetworkGraph />
          <div className="section-divider" />
          <RicoLeadersTable />
          <div className="section-divider" />
          <FinancialFlowChart />
          <div className="section-divider" />
          <PatentAnalytics />
          <div className="section-divider" />
          <WipoJurisdictionMap />
          <div className="section-divider" />
          <IsinCusipPanel />
          <div className="section-divider" />
          <RegulatoryCapture />
          <div className="section-divider" />
          <TokenizedIPTracing />
          <div className="section-divider" />
          <CyberDustDetection />
          <div className="section-divider" />
          <SyntheticInventors />
          <div className="section-divider" />
          <TreasuryWalletFreeze />
          <div className="section-divider" />
          <CitationErasure />
          <div className="section-divider" />
          <BlockchainForensics />
          <div className="section-divider" />
          <ShellCorpMap />
          <div className="section-divider" />
          <FentanylDashboard />
          <div className="section-divider" />
          <EvidenceChainViewer />
          <div className="section-divider" />
          <AgentSwarmPanel />
          <div className="section-divider" />
          <InvestigationTimeline />
          <div className="section-divider" />
          <DataSourcesGrid />
          <div className="section-divider" />
          <ComplianceMatrix />
          <div className="section-divider" />
          <ForensicReport />
        </div>
      </main>

      <div className="md:ml-64">
        <Footer />
      </div>
    </div>
  );
}
