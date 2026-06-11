/**
 * Report Data Builder — constructs ReportData from bracket KPIs.
 *
 * Loads bracket KPI references, resolves them from the catalog,
 * and builds report data with actual metadata. Falls back to
 * sample data when no bracketId is provided.
 */

import type { ReportData } from './html-report-builder';
import type { CatalogKpi } from '@/lib/core/catalog-loader';
import type { KpiSnapshot, TrendPoint, WaterfallDriver, EvidenceRow } from '@/lib/dashboard/sample-data';
import { getAuroraKpiValue, type AuroraKpiValue } from '@/lib/aurora/kpi-snapshot';

/**
 * Build ReportData from bracket KPIs.
 *
 * @param bracketId - The bracket to load KPIs from
 * @param kpiMap - Resolved KPI catalog map
 * @param bracketKpiIds - KPI IDs from the bracket's orchestration
 * @param projectName - Project display name
 */
export function buildReportDataFromBracket(
  bracketId: string,
  kpiMap: Map<string, CatalogKpi>,
  bracketKpiIds: string[],
  projectName: string,
): ReportData {
  // Build KPI snapshots from catalog metadata, hydrated with real values from
  // the Aurora gold snapshot when the KPI has been computed (falls back to the
  // catalog-only stub for KPIs not yet wired into the snapshot).
  const kpis: KpiSnapshot[] = bracketKpiIds
    .map((id) => kpiMap.get(id))
    .filter((k): k is CatalogKpi => !!k)
    .map((kpi) => {
      const actual = getAuroraKpiValue(kpi.kpi_id);
      return {
        kpiId: kpi.kpi_id,
        label: kpi.kpi_key ?? kpi.kpi_id,
        value: actual?.value ?? 0,
        previousValue: actual?.previousValue ?? 0,
        target: actual?.target ?? 0,
        unit: actual?.unit ?? inferUnit(kpi),
        status: deriveStatus(actual),
      };
    });

  // Build trend from the strategic KPI's real monthly series when available.
  const strategicKpi = kpiMap.get(bracketKpiIds[0]);
  const strategicActual = strategicKpi ? getAuroraKpiValue(strategicKpi.kpi_id) : undefined;
  const trend: TrendPoint[] = strategicActual?.trend.length
    ? strategicActual.trend.map((p) => ({ period: p.period, value: p.value }))
    : generatePlaceholderTrend(12);
  const trendLabel = strategicKpi?.kpi_key ?? bracketId;

  // Build waterfall from influencing KPIs — use the real month-over-month delta
  // for KPIs present in the snapshot, otherwise leave the driver at zero.
  const waterfall: WaterfallDriver[] = bracketKpiIds.slice(1, 6).map((id) => {
    const kpi = kpiMap.get(id);
    const actual = kpi ? getAuroraKpiValue(kpi.kpi_id) : undefined;
    return {
      driver: kpi?.kpi_key ?? id,
      delta: actual ? round2(actual.value - actual.previousValue) : 0,
    };
  });

  // Build evidence placeholder
  const evidence: EvidenceRow[] = [];

  return {
    projectName,
    bracketTitle: bracketId,
    kpis,
    trend,
    trendLabel,
    waterfall,
    evidence,
  };
}

/**
 * Derive a RAG status from actual vs. target. Treats target as a
 * higher-is-better goal: on-track within 2% under target, at-risk within 10%,
 * off-track beyond. Neutral (on-track) when no actual or no meaningful target
 * (the snapshot sets target = value for KPIs without a plan reference).
 */
function deriveStatus(actual: AuroraKpiValue | undefined): KpiSnapshot['status'] {
  if (!actual || !actual.target) return 'on-track';
  const deviation = (actual.value - actual.target) / Math.abs(actual.target);
  if (deviation >= -0.02) return 'on-track';
  if (deviation >= -0.1) return 'at-risk';
  return 'off-track';
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

function inferUnit(kpi: CatalogKpi): string {
  const format = kpi.technical?.formatString ?? '';
  if (format.includes('%')) return '%';
  if (format.includes('$') || format.includes('€')) return '';
  return '';
}

function generatePlaceholderTrend(periods: number): TrendPoint[] {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return Array.from({ length: periods }, (_, i) => ({
    period: months[i % 12],
    value: 0,
  }));
}
