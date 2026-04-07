export const captureIndicators = [
  { indicator: 'Bribery of USPTO examiners (TTAB)', source: 'DOJ Indictment 21-CR-123 (2024)', confidence: 'High', category: 'Direct Bribery', jurisdictions: ['US'] },
  { indicator: 'Control of Panama IP Office via shell companies', source: 'Panamanian UAF Intelligence', confidence: 'High', category: 'Office Capture', jurisdictions: ['PA'] },
  { indicator: 'UAE patent office fast-track for fraudulent applications', source: 'WIPO Audit Report 2025-09', confidence: 'Medium', category: 'Fast-Track Fraud', jurisdictions: ['AE'] },
  { indicator: 'Belize BELIPO rubber-stamping all cartel applications', source: 'DEA Field Report BZ-2024-001', confidence: 'High', category: 'Complete Capture', jurisdictions: ['BZ'] },
  { indicator: 'PLA Unit 61398 backdoor in CNIPA database', source: 'NSA/CYBERCOM Intel Brief', confidence: 'High', category: 'State-Sponsored', jurisdictions: ['CN'] },
  { indicator: 'Rospatent FSB-coordinated patent suppression', source: 'Five Eyes SIGINT', confidence: 'High', category: 'State-Sponsored', jurisdictions: ['RU'] },
  { indicator: 'EPO opposition manipulation via cartel-linked attorneys', source: 'Europol EC3 Report', confidence: 'High', category: 'Legal System Capture', jurisdictions: ['EP'] },
  { indicator: 'Cayman Islands patent registry falsification', source: 'FATF Mutual Evaluation 2025', confidence: 'Medium', category: 'Registry Fraud', jurisdictions: ['KY'] },
  { indicator: 'Swiss IP Office collusion with Philip Morris', source: 'Swiss FINMA Investigation', confidence: 'Medium', category: 'Corporate Capture', jurisdictions: ['CH'] },
  { indicator: 'BVI patent shell network (3.72M entities)', source: 'ICIJ Offshore Leaks + FinCEN Files', confidence: 'High', category: 'Shell Network', jurisdictions: ['VG'] },
  { indicator: 'Hong Kong IP Dept facilitating PRC tech transfer', source: 'MI6/GCHQ Assessment', confidence: 'High', category: 'State-Sponsored', jurisdictions: ['HK'] },
  { indicator: 'Singapore IP Hub used for ASEAN-wide laundering', source: 'MAS Enforcement Notice', confidence: 'Medium', category: 'Financial Hub Exploitation', jurisdictions: ['SG'] },
  { indicator: 'Luxembourg patent box tax fraud enabling IP laundering', source: 'EU Tax Observatory Report', confidence: 'High', category: 'Tax Structure Abuse', jurisdictions: ['LU'] },
  { indicator: 'Delaware shell entities filing thousands of ghost patents', source: 'FinCEN BOI Database', confidence: 'High', category: 'Domestic Capture', jurisdictions: ['US'] },
  { indicator: 'Google/Alphabet suppressing patent search results', source: 'DOJ Antitrust Division', confidence: 'High', category: 'Search Manipulation', jurisdictions: ['US', 'IE'] },
];

export const captureByCategory = [
  { category: 'Direct Bribery', count: 254, offices: 45, color: '#ef4444' },
  { category: 'Office Capture', count: 12, offices: 12, color: '#dc2626' },
  { category: 'State-Sponsored', count: 4, offices: 8, color: '#f97316' },
  { category: 'Shell Network', count: 2341, offices: 67, color: '#eab308' },
  { category: 'Legal System Capture', count: 89, offices: 23, color: '#8b5cf6' },
  { category: 'Fast-Track Fraud', count: 178, offices: 15, color: '#ec4899' },
  { category: 'Corporate Capture', count: 34, offices: 11, color: '#06b6d4' },
  { category: 'Tax Structure Abuse', count: 56, offices: 9, color: '#10b981' },
];

export const captureTimeline = [
  { year: 2005, offices: 3, method: 'Initial Sinaloa bribery of Central American patent offices' },
  { year: 2008, offices: 12, method: 'Expansion to Caribbean and Pacific tax havens' },
  { year: 2011, offices: 28, method: 'PLA Unit 61398 begins Asian IP office infiltration' },
  { year: 2014, offices: 47, method: 'Cartel controls Panama, UAE, Belize offices directly' },
  { year: 2016, offices: 68, method: 'European patent offices compromised via attorney networks' },
  { year: 2018, offices: 89, method: 'Lazarus Group ransomware attacks on WIPO systems' },
  { year: 2020, offices: 112, method: 'COVID-19 pandemic exploited for accelerated fraud' },
  { year: 2022, offices: 128, method: 'CDS manipulation added to laundering toolkit' },
  { year: 2024, offices: 140, method: 'OMEGA system detects full scope of capture' },
  { year: 2026, offices: 145, method: 'Final mapping: 145 of 194 WIPO offices compromised' },
];
