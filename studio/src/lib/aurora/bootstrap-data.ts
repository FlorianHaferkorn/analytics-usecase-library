import { loadAuroraSnapshot } from '@/lib/aurora/kpi-snapshot';

export interface AuroraBootstrapData {
  linked: boolean;
  kpiCount: number;
  source: string | null;
  note: string | null;
}

/** Server-side Aurora showcase linkage summary for Studio bootstrap. */
export function getAuroraBootstrapData(): AuroraBootstrapData {
  const snapshot = loadAuroraSnapshot();
  if (!snapshot) {
    return {
      linked: false,
      kpiCount: 0,
      source: null,
      note: 'Aurora gold snapshot not found — run showcases/aurora_group/data/build_kpi_snapshot.py',
    };
  }
  return {
    linked: true,
    kpiCount: Object.keys(snapshot.kpis).length,
    source: snapshot._meta?.source ?? null,
    note: snapshot._meta?.note ?? null,
  };
}
