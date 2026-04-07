export const isinCusipStats = {
  totalIsinMapped: 4219,
  totalCusipLinked: 3847,
  illicitInstrumentsExposed: 4219,
  totalLaunderedUsd: 2300000000000,
  beneficialOwnersUnmasked: 1847,
  shellEntitiesLinked: 2341,
};

export const isinCusipRecords = [
  { isin: 'US0378331005', cusip: '037833100', name: 'Apple Inc.', patentId: 'US10101010B2', beneficialOwner: 'ABG Shell Network #14', riskLevel: 'HIGH', exposedVia: 'Blockchain Tracing', amountUsd: 890000000 },
  { isin: 'US88160R1014', cusip: '88160R101', name: 'Tesla Inc.', patentId: 'US10234567B1', beneficialOwner: 'Sinaloa Front Entity (Cayman)', riskLevel: 'CRITICAL', exposedVia: 'FinCEN SAR', amountUsd: 1240000000 },
  { isin: 'US5949181045', cusip: '594918104', name: 'Microsoft Corp.', patentId: 'US10345678B2', beneficialOwner: 'Page-Linked Shell (Ireland)', riskLevel: 'HIGH', exposedVia: 'ISIN/CUSIP Linkage', amountUsd: 670000000 },
  { isin: 'US67066G1040', cusip: '67066G104', name: 'NVIDIA Corp.', patentId: 'US10456789B1', beneficialOwner: 'PLA Front Company (HK)', riskLevel: 'CRITICAL', exposedVia: 'OFAC SDN Match', amountUsd: 2100000000 },
  { isin: 'US30303M1027', cusip: '30303M102', name: 'Meta Platforms', patentId: 'US10567890B2', beneficialOwner: 'Lazarus Mixer Output', riskLevel: 'CRITICAL', exposedVia: 'Chainalysis KYT', amountUsd: 980000000 },
  { isin: 'US02079K3059', cusip: '02079K305', name: 'Alphabet Inc.', patentId: 'US10678901B1', beneficialOwner: 'Page Personal Trust (BVI)', riskLevel: 'CRITICAL', exposedVia: 'OpenCorporates + Sayari', amountUsd: 1560000000 },
  { isin: 'US46625H1005', cusip: '46625H100', name: 'JPMorgan Chase', patentId: 'CDS-JPM-2024-001', beneficialOwner: 'Cartel CDS Counterparty', riskLevel: 'CRITICAL', exposedVia: 'DeFi Protocol Analysis', amountUsd: 3400000000 },
  { isin: 'US7181721090', cusip: '718172109', name: 'Philip Morris Intl', patentId: 'US10789012B2', beneficialOwner: 'IQOS Shell (Switzerland)', riskLevel: 'HIGH', exposedVia: 'FinCEN BOI', amountUsd: 780000000 },
  { isin: 'US0846707026', cusip: '084670702', name: 'Berkshire Hathaway', patentId: 'US10890123B1', beneficialOwner: 'Insurance CDS Structure', riskLevel: 'MEDIUM', exposedVia: 'SEC EDGAR', amountUsd: 450000000 },
  { isin: 'US4781601046', cusip: '478160104', name: 'Johnson & Johnson', patentId: 'US10901234B2', beneficialOwner: 'Health IP Shell (NL)', riskLevel: 'HIGH', exposedVia: 'GLEIF LEI', amountUsd: 340000000 },
];

export const exposureByMethod = [
  { method: 'Blockchain Tracing', count: 1247, amountUsd: 89000000000, color: '#06b6d4' },
  { method: 'FinCEN SAR/BOI', count: 892, amountUsd: 67000000000, color: '#8b5cf6' },
  { method: 'ISIN/CUSIP Linkage', count: 734, amountUsd: 52000000000, color: '#f97316' },
  { method: 'OFAC SDN Match', count: 489, amountUsd: 41000000000, color: '#ef4444' },
  { method: 'Chainalysis KYT', count: 367, amountUsd: 34000000000, color: '#eab308' },
  { method: 'OpenCorporates + Sayari', count: 234, amountUsd: 18000000000, color: '#10b981' },
  { method: 'SEC EDGAR', count: 156, amountUsd: 12000000000, color: '#ec4899' },
  { method: 'DeFi Protocol Analysis', count: 100, amountUsd: 8700000000, color: '#14b8a6' },
];
