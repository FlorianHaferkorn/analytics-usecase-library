/** Sample Aurora Group data for dashboard previews. */

export interface KpiSnapshot {
  kpiId: string;
  label: string;
  value: number;
  previousValue: number;
  target: number;
  unit: string;
  status: 'on-track' | 'at-risk' | 'off-track';
}

export interface TrendPoint {
  period: string;
  value: number;
}

export interface WaterfallDriver {
  driver: string;
  delta: number;
}

export interface EvidenceRow {
  entity: string;
  kpiValue: number;
  delta: number;
  actionCode: string;
  priority: 'P1' | 'P2' | 'P3';
}

export const SAMPLE_KPIS: KpiSnapshot[] = [
  { kpiId: 'KPI-GM', label: 'Gross Margin', value: 42.3, previousValue: 41.1, target: 43.0, unit: '%', status: 'at-risk' },
  { kpiId: 'KPI-NS', label: 'Net Sales', value: 4.2, previousValue: 3.9, target: 4.5, unit: '€B', status: 'on-track' },
  { kpiId: 'KPI-CCC', label: 'CCC Days', value: 38, previousValue: 41, target: 35, unit: 'd', status: 'at-risk' },
  { kpiId: 'KPI-OEE', label: 'OEE %', value: 76, previousValue: 73, target: 80, unit: '%', status: 'off-track' },
];

export const SAMPLE_TREND: TrendPoint[] = [
  { period: 'Jan', value: 40.1 }, { period: 'Feb', value: 40.5 }, { period: 'Mar', value: 41.0 },
  { period: 'Apr', value: 40.8 }, { period: 'May', value: 41.3 }, { period: 'Jun', value: 41.1 },
  { period: 'Jul', value: 41.5 }, { period: 'Aug', value: 41.8 }, { period: 'Sep', value: 42.0 },
  { period: 'Oct', value: 41.7 }, { period: 'Nov', value: 42.1 }, { period: 'Dec', value: 42.3 },
];

export const SAMPLE_WATERFALL: WaterfallDriver[] = [
  { driver: 'Price', delta: 1.2 },
  { driver: 'Volume', delta: -0.3 },
  { driver: 'Mix', delta: 0.5 },
  { driver: 'COGS', delta: -0.8 },
  { driver: 'FX', delta: 0.2 },
  { driver: 'Other', delta: 0.4 },
];

export const SAMPLE_EVIDENCE: EvidenceRow[] = [
  { entity: 'DACH Region', kpiValue: 44.1, delta: 2.1, actionCode: 'C-M2.1', priority: 'P2' },
  { entity: 'Benelux', kpiValue: 39.8, delta: -1.5, actionCode: 'C-M1.3', priority: 'P1' },
  { entity: 'Nordics', kpiValue: 41.2, delta: 0.3, actionCode: 'C-M2.2', priority: 'P3' },
  { entity: 'UK & Ireland', kpiValue: 38.5, delta: -2.8, actionCode: 'C-M1.1', priority: 'P1' },
  { entity: 'Southern Europe', kpiValue: 43.7, delta: 1.8, actionCode: 'C-M3.1', priority: 'P3' },
];
