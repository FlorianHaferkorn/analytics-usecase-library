/**
 * Aurora KPI Snapshot Loader
 *
 * Reads the static KPI-values snapshot produced from the Aurora gold facts by
 * `showcases/aurora_group/data/build_kpi_snapshot.py` (DuckDB over partitioned
 * parquet → JSON). Studio consumes the snapshot so report/dashboard numbers are
 * the real governed values instead of hard-coded stubs — without shipping a
 * DuckDB/parquet reader into the Next.js runtime.
 *
 * Server-side only (uses `node:fs`). The snapshot keys are KPI ids
 * (`sales.net_sales.amount`, `margin.gm.pct`, …) so callers can look values up
 * by `kpi_id` straight from the catalog.
 */

import { readFileSync } from 'node:fs';
import { join } from 'node:path';

/** A single point on a KPI's monthly trend line. */
export interface AuroraTrendPoint {
  period: string;
  value: number;
}

/** Computed values for one KPI, keyed by `kpi_id` in the snapshot. */
export interface AuroraKpiValue {
  value: number;
  previousValue: number;
  target: number;
  unit: string;
  trend: AuroraTrendPoint[];
}

/** The full snapshot document written by the aggregator. */
export interface AuroraSnapshot {
  _meta: {
    source: string;
    generatedAt: string;
    latestPeriod: string;
    note: string;
  };
  kpis: Record<string, AuroraKpiValue>;
}

const SNAPSHOT_PATH = join(process.cwd(), 'data', 'aurora_kpi_snapshot.json');

let cached: AuroraSnapshot | null = null;

/**
 * Load and cache the Aurora KPI snapshot. Returns `null` when the snapshot has
 * not been generated yet, so callers can gracefully fall back to stub values.
 */
export function loadAuroraSnapshot(): AuroraSnapshot | null {
  if (cached) return cached;
  try {
    const raw = readFileSync(SNAPSHOT_PATH, 'utf-8');
    cached = JSON.parse(raw) as AuroraSnapshot;
    return cached;
  } catch {
    return null;
  }
}

/** Look up computed values for a single KPI by its `kpi_id`. */
export function getAuroraKpiValue(kpiId: string): AuroraKpiValue | undefined {
  return loadAuroraSnapshot()?.kpis[kpiId];
}
