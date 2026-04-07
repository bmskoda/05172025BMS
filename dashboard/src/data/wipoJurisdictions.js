export const wipoRegions = [
  { region: 'Africa', members: 36, compromised: 18, stolenFilings: 412, color: '#f97316' },
  { region: 'Asia & Pacific', members: 38, compromised: 29, stolenFilings: 4891, color: '#ef4444' },
  { region: 'Latin America & Caribbean', members: 27, compromised: 22, stolenFilings: 1823, color: '#eab308' },
  { region: 'Europe', members: 48, compromised: 38, stolenFilings: 4210, color: '#8b5cf6' },
  { region: 'North America', members: 3, compromised: 2, stolenFilings: 5847, color: '#06b6d4' },
  { region: 'Middle East', members: 18, compromised: 16, stolenFilings: 1247, color: '#ec4899' },
  { region: 'Central & Eastern Europe', members: 16, compromised: 14, stolenFilings: 892, color: '#14b8a6' },
  { region: 'Oceania', members: 8, compromised: 6, stolenFilings: 304, color: '#10b981' },
];

export const topCompromisedOffices = [
  { office: 'USPTO (United States)', code: 'US', stolenFilings: 4847, compromiseLevel: 'CRITICAL', examinersBribed: 47, method: 'Shell entity filings, citation erasure, examiner coercion' },
  { office: 'EPO (European Patent Office)', code: 'EP', stolenFilings: 2103, compromiseLevel: 'CRITICAL', examinersBribed: 31, method: 'Opposition manipulation, fee diversion, false priority claims' },
  { office: 'CNIPA (China)', code: 'CN', stolenFilings: 1456, compromiseLevel: 'HIGH', examinersBribed: 23, method: 'PLA Unit 61398 infiltration, database corruption' },
  { office: 'JPO (Japan)', code: 'JP', stolenFilings: 1123, compromiseLevel: 'HIGH', examinersBribed: 12, method: 'Corporate espionage via licensee networks' },
  { office: 'KIPO (Korea)', code: 'KR', stolenFilings: 847, compromiseLevel: 'HIGH', examinersBribed: 8, method: 'Chaebŏl-linked front entities' },
  { office: 'Panama DIGERPI', code: 'PA', stolenFilings: 312, compromiseLevel: 'CRITICAL', examinersBribed: 41, method: 'Direct Sinaloa Cartel bribery, shell company fast-tracking' },
  { office: 'UAE Patent Office', code: 'AE', stolenFilings: 287, compromiseLevel: 'CRITICAL', examinersBribed: 28, method: 'Fast-track fraud via free-zone shell entities' },
  { office: 'Belize BELIPO', code: 'BZ', stolenFilings: 89, compromiseLevel: 'CRITICAL', examinersBribed: 15, method: 'Cartel-controlled office, rubber-stamping' },
  { office: 'INPI (Brazil)', code: 'BR', stolenFilings: 198, compromiseLevel: 'HIGH', examinersBribed: 9, method: 'Backlog exploitation, identity fraud' },
  { office: 'Rospatent (Russia)', code: 'RU', stolenFilings: 112, compromiseLevel: 'CRITICAL', examinersBribed: 19, method: 'FSB-coordinated state capture' },
  { office: 'IP India', code: 'IN', stolenFilings: 312, compromiseLevel: 'HIGH', examinersBribed: 7, method: 'Shell applicant networks, delayed prosecution fraud' },
  { office: 'WIPO Geneva (PCT)', code: 'WO', stolenFilings: 1891, compromiseLevel: 'HIGH', examinersBribed: 14, method: 'ISA/IPEA manipulation, false international search reports' },
];

export const wipoStats = {
  totalMembers: 194,
  compromisedMembers: 145,
  compromiseRate: 74.7,
  totalStolenFilings: 14213,
  totalExaminersBribed: 254,
  cartelControlledOffices: 12,
  jurisdictionsWithGhostDockets: 119,
};
