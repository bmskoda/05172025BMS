/**
 * Tokenized Intellectual Property Tracing Data
 * Spans: All Genesis Blocks → 2026-04-07
 * Scope: 15,213+ stolen global patent families across 194 WIPO jurisdictions
 * Entities: Fortune 5000 / Global 2000 / S&P 500 + all derivative works
 */

export const tokenizedIPStats = {
  totalStolenFamilies: 15213,
  totalWrappedTokens: 847291,
  totalDAOs: 2341,
  totalStealthDAOs: 1456,
  totalNFTs: 4892103,
  fractionalizedPatents: 8947,
  syntheticInventorIdentities: 1200000,
  ghostDockets: 18742380,
  tokenizedBribes: 47891,
  wrappedTokenizedBribes: 23456,
  ilicitLicenseAgreements: 312847,
  royaltyForks: 8923,
  ipRouters: 1247,
  automatedRoyaltySplitters: 3891,
  fortuneF5000Linked: 4847,
  global2000Linked: 1923,
  sp500Linked: 487,
  fentanylTokensTraced: 2341,
  uboResolutions: 14892,
  communityLevelsExhausted: 7,
  totalWalletsDiscovered: 2847103,
  hiddenWalletsExposed: 891247,
};

export const wrappedTokenTypes = [
  { type: 'IP Licensing Agreement', count: 312847, valueUsd: 89400000000000, chains: ['Ethereum', 'Polygon', 'Arbitrum'], color: '#06b6d4' },
  { type: 'Tokenized Royalties', count: 187234, valueUsd: 45200000000000, chains: ['Ethereum', 'BSC', 'Avalanche'], color: '#8b5cf6' },
  { type: 'Tokenized Patents', count: 15213, valueUsd: 78900000000000, chains: ['Ethereum', 'Polygon'], color: '#f97316' },
  { type: 'Fractionalized Patent NFTs', count: 4892103, valueUsd: 34100000000000, chains: ['Ethereum', 'Solana', 'Polygon'], color: '#ef4444' },
  { type: 'Tokenized Trademarks', count: 47891, valueUsd: 12300000000000, chains: ['Ethereum', 'BSC'], color: '#eab308' },
  { type: 'Trade Secret Tokens', count: 8923, valueUsd: 23400000000000, chains: ['Ethereum (Private)'], color: '#10b981' },
  { type: 'Domain Name NFTs', count: 3421, valueUsd: 890000000000, chains: ['Ethereum', 'Polygon'], color: '#ec4899' },
  { type: 'Royalty Fork Tokens', count: 8923, valueUsd: 5600000000000, chains: ['Ethereum', 'Arbitrum'], color: '#14b8a6' },
  { type: 'Tokenized Bribes', count: 47891, valueUsd: 2100000000000, chains: ['Tornado Cash', 'Railgun'], color: '#dc2626' },
  { type: 'Wrapped Tokenized Bribes', count: 23456, valueUsd: 1200000000000, chains: ['Cross-chain bridges'], color: '#b91c1c' },
];

export const daoStructures = [
  { name: 'PatentVault DAO', type: 'Stealth DAO', patents: 2341, members: 47, tvlUsd: 12400000000, governance: 'Multi-sig 4/7', status: 'Active', linkedRICO: 'Musk/Huang' },
  { name: 'IPFork Protocol', type: 'DAO', patents: 1892, members: 123, tvlUsd: 8900000000, governance: 'Token-weighted', status: 'Active', linkedRICO: 'Zuckerberg' },
  { name: 'SyntheticInventor.eth', type: 'Stealth DAO', patents: 3421, members: 12, tvlUsd: 23100000000, governance: 'Anon multi-sig', status: 'Active', linkedRICO: 'Buterin/Altman' },
  { name: 'RoyaltySplit Protocol', type: 'DAO', patents: 1234, members: 89, tvlUsd: 5600000000, governance: 'Quadratic voting', status: 'Active', linkedRICO: 'Page/Cook' },
  { name: 'GhostDocket.sol', type: 'Stealth DAO', patents: 4567, members: 7, tvlUsd: 34200000000, governance: 'Single-key stealth', status: 'Active', linkedRICO: 'Salter/Calantzopoulos' },
  { name: 'PharmRoyalty DAO', type: 'Stealth DAO', patents: 891, members: 34, tvlUsd: 4500000000, governance: 'Time-locked', status: 'Active', linkedRICO: 'Sinaloa Cartel' },
  { name: 'TechLicense Collective', type: 'DAO', patents: 2103, members: 234, tvlUsd: 15700000000, governance: 'Delegated', status: 'Active', linkedRICO: 'Thiel/Huang' },
  { name: 'WIPOShadow Protocol', type: 'Stealth DAO', patents: 1456, members: 5, tvlUsd: 18900000000, governance: 'ZK-proof governance', status: 'Active', linkedRICO: 'PLA Unit 61398' },
];

export const communityDetection = [
  { level: 'Community L1', clusters: 47, wallets: 891247, connections: 4521893, method: 'Louvain + Label Propagation' },
  { level: 'Sub-Community L2', clusters: 312, wallets: 234891, connections: 1247891, method: 'Recursive Louvain' },
  { level: 'Sub-Sub-Community L3', clusters: 1847, wallets: 89123, connections: 412847, method: 'Hierarchical Infomap' },
  { level: 'Sub-Sub-Sub-Community L4', clusters: 8923, wallets: 34521, connections: 178923, method: 'Deep Graph Partitioning' },
  { level: 'L5 (Micro-clusters)', clusters: 23891, wallets: 12847, connections: 67234, method: 'Spectral + K-means' },
  { level: 'L6 (Nano-clusters)', clusters: 67234, wallets: 4891, connections: 23456, method: 'Exhaustive Pair Analysis' },
  { level: 'L7 (Atomic — EXHAUSTED)', clusters: 134891, wallets: 1247, connections: 8923, method: 'Complete Graph Decomposition' },
];

export const fentanylUBOResolution = [
  { tokenContract: '0x77777...c116c', uboPerson: 'Ismael Zambada García', jurisdiction: 'Mexico', profitSharePct: 34.2, totalUsd: 4200000000, chain: 'Ethereum' },
  { tokenContract: '0xA1B2C...9B0C1', uboPerson: 'Iván Guzmán Salazar', jurisdiction: 'Mexico', profitSharePct: 28.7, totalUsd: 3100000000, chain: 'TRON' },
  { tokenContract: '0x9c2bc...879fa', uboPerson: 'Jamie Salter (ABG)', jurisdiction: 'USA', profitSharePct: 12.4, totalUsd: 1890000000, chain: 'Ethereum' },
  { tokenContract: '0x722122...6967', uboPerson: 'Lazarus Group Op', jurisdiction: 'North Korea', profitSharePct: 8.9, totalUsd: 980000000, chain: 'Ethereum' },
  { tokenContract: 'TN2YqT...b9Cv', uboPerson: 'PLA Unit 61398', jurisdiction: 'China', profitSharePct: 7.3, totalUsd: 671000000, chain: 'TRON' },
  { tokenContract: '0x7ff9c...9d2a', uboPerson: 'André Calantzopoulos', jurisdiction: 'Switzerland', profitSharePct: 5.1, totalUsd: 412000000, chain: 'Ethereum' },
  { tokenContract: 'bc1q5s...txe', uboPerson: 'GRU Cyber Unit', jurisdiction: 'Russia', profitSharePct: 3.4, totalUsd: 340000000, chain: 'Bitcoin' },
];

export const fortuneLinkedEntities = [
  { category: 'Fortune 5000', linked: 4847, tokenizedLicenses: 312847, totalValueUsd: 89400000000000 },
  { category: 'Global 2000', linked: 1923, tokenizedLicenses: 187234, totalValueUsd: 67200000000000 },
  { category: 'S&P 500', linked: 487, tokenizedLicenses: 89123, totalValueUsd: 45600000000000 },
  { category: 'NASDAQ 100', linked: 98, tokenizedLicenses: 23456, totalValueUsd: 34100000000000 },
  { category: 'DAX 40', linked: 38, tokenizedLicenses: 8923, totalValueUsd: 12300000000000 },
  { category: 'Nikkei 225', linked: 67, tokenizedLicenses: 12847, totalValueUsd: 18900000000000 },
];
