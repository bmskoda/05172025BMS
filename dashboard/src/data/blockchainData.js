export const trackedAddresses = [
  { address: '0x742d35Cc6634C0532925a3b8D4C0cFb3d4c27F91', chain: 'Ethereum', entity: 'Sinaloa Cartel Front', risk: 98, txCount: 14523, totalUsd: 892000000, firstSeen: '2017-03-14', lastSeen: '2026-02-28' },
  { address: '0x9c2bc757b66f24d60f016b6237f8cdd414a879fa', chain: 'Ethereum', entity: 'CDS Downstream Cluster', risk: 95, txCount: 8741, totalUsd: 1240000000, firstSeen: '2018-06-22', lastSeen: '2026-03-15' },
  { address: 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh', chain: 'Bitcoin', entity: 'Lazarus Group Mixer', risk: 99, txCount: 23891, totalUsd: 3410000000, firstSeen: '2015-08-03', lastSeen: '2026-03-20' },
  { address: '0x7ff9cfad3877f21d41da29e53e28a70e3f6a9d2a', chain: 'Ethereum', entity: 'Tornado Cash Router', risk: 100, txCount: 187432, totalUsd: 7820000000, firstSeen: '2019-12-16', lastSeen: '2026-01-31' },
  { address: '0x722122df12d4e14e13ac3b6895a86e84145b6967', chain: 'Ethereum', entity: 'Tornado Cash Proxy', risk: 100, txCount: 94215, totalUsd: 4560000000, firstSeen: '2020-01-03', lastSeen: '2026-02-14' },
  { address: 'TN2YqTv9HE52o7jGDLfmAJmT5rHzGnb9Cv', chain: 'TRON', entity: 'PLA Unit 61398 Front', risk: 97, txCount: 5623, totalUsd: 671000000, firstSeen: '2020-05-18', lastSeen: '2026-03-12' },
  { address: '0xA1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0', chain: 'Ethereum', entity: 'ABG Shell Network', risk: 87, txCount: 3214, totalUsd: 412000000, firstSeen: '2019-07-22', lastSeen: '2026-02-20' },
  { address: 'bc1q5shng7g4xnqrm6zvhvx0g9sptfy8wdpz3uvtxe', chain: 'Bitcoin', entity: 'GRU Cyber Unit', risk: 96, txCount: 11234, totalUsd: 1890000000, firstSeen: '2016-11-08', lastSeen: '2026-03-18' },
];

export const chainDistribution = [
  { chain: 'Ethereum', volume: 48200000000, txCount: 1247891, pct: 38.2, color: '#627eea' },
  { chain: 'Bitcoin', volume: 34100000000, txCount: 623412, pct: 27.0, color: '#f7931a' },
  { chain: 'TRON', volume: 12800000000, txCount: 312456, pct: 10.1, color: '#ff0013' },
  { chain: 'BSC', volume: 9400000000, txCount: 198723, pct: 7.5, color: '#f0b90b' },
  { chain: 'Polygon', volume: 7200000000, txCount: 156234, pct: 5.7, color: '#8247e5' },
  { chain: 'Solana', volume: 5600000000, txCount: 89123, pct: 4.4, color: '#14f195' },
  { chain: 'Avalanche', volume: 4100000000, txCount: 67891, pct: 3.2, color: '#e84142' },
  { chain: 'Arbitrum', volume: 3200000000, txCount: 78456, pct: 2.5, color: '#28a0f0' },
  { chain: 'Optimism', volume: 1700000000, txCount: 42891, pct: 1.3, color: '#ff0420' },
];

export const mixerEvents = [
  { year: 2017, events: 23 },
  { year: 2018, events: 89 },
  { year: 2019, events: 234 },
  { year: 2020, events: 512 },
  { year: 2021, events: 1247 },
  { year: 2022, events: 2341 },
  { year: 2023, events: 1892 },
  { year: 2024, events: 1456 },
  { year: 2025, events: 987 },
];

export const weaponizedCdsStats = {
  totalWeaponizedNotionalUsd: 450000000000000, // $450 trillion
  tokenizedCdsProtocols: 15,
  traditionalCdsCounterparties: 9,
  selfBettingLeaders: 13,
  totalPositions: 6231,
  description: 'RICO leaders self-betting against their own publicly '
    + 'traded corporations via tokenized on-chain + traditional CDS',
};

export const cdsTargets = [
  { ticker: 'JPM', name: 'JPMorgan Chase', sector: 'Banking', notional: 12400000000, positions: 847, avgSpread: 142, risk: 'HIGH' },
  { ticker: 'BAC', name: 'Bank of America', sector: 'Banking', notional: 8900000000, positions: 623, avgSpread: 168, risk: 'HIGH' },
  { ticker: 'C', name: 'Citigroup', sector: 'Banking', notional: 6700000000, positions: 512, avgSpread: 189, risk: 'HIGH' },
  { ticker: 'WFC', name: 'Wells Fargo', sector: 'Banking', notional: 7200000000, positions: 489, avgSpread: 156, risk: 'HIGH' },
  { ticker: 'GS', name: 'Goldman Sachs', sector: 'Investment Banking', notional: 9800000000, positions: 734, avgSpread: 134, risk: 'CRITICAL' },
  { ticker: 'MS', name: 'Morgan Stanley', sector: 'Investment Banking', notional: 5400000000, positions: 398, avgSpread: 178, risk: 'HIGH' },
  { ticker: 'PM', name: 'Philip Morris Intl', sector: 'Tobacco', notional: 3200000000, positions: 267, avgSpread: 212, risk: 'MEDIUM' },
  { ticker: 'NVDA', name: 'NVIDIA', sector: 'Semiconductors', notional: 18700000000, positions: 1234, avgSpread: 98, risk: 'CRITICAL' },
  { ticker: 'TSLA', name: 'Tesla', sector: 'Automotive/Tech', notional: 14300000000, positions: 987, avgSpread: 245, risk: 'CRITICAL' },
];
