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
  // Build KPI snapshots from catalog metadata
  const kpis: KpiSnapshot[] = bracketKpiIds
    .map((id) => kpiMap.get(id))
    .filter((k): k is CatalogKpi => !!k)
    .map((kpi) => ({
      kpiId: kpi.kpi_id,
      label: kpi.kpi_key ?? kpi.kpi_id,
      value: 0,
      previousValue: 0,
      target: 0,
      unit: inferUnit(kpi),
      status: 'on-track' as const,
    }));

  // Build trend from strategic KPI (placeholder periods)
  const strategicKpi = kpiMap.get(bracketKpiIds[0]);
  const trend: TrendPoint[] = generatePlaceholderTrend(12);
  const trendLabel = strategicKpi?.kpi_key ?? bracketId;

  // Build waterfall from influencing KPIs
  const waterfall: WaterfallDriver[] = bracketKpiIds.slice(1, 6).map((id) => {
    const kpi = kpiMap.get(id);
    return {
      driver: kpi?.kpi_key ?? id,
      delta: 0,
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
