/**
 * Tests for Report Data Builder.
 */

import { describe, it, expect } from 'vitest';
import { buildReportDataFromBracket } from '@/lib/report/report-data-builder';
import type { CatalogKpi } from '@/lib/core/catalog-loader';

function makeKpi(id: string, name: string, formatString = '#,0'): CatalogKpi {
  return {
    kpi_id: id,
    calc_type: 'measure',
    kpi_key: name,
    business: { purpose: `Purpose of ${id}` },
    technical: {
      dax_name: name.replace(/\s/g, '_'),
      dax_expression: `SUM(T[${name}])`,
      formatString,
      description: `Desc ${id}`,
      depends_on_measures: [],
    },
    governance: {},
    metadata_quality: {},
  } as unknown as CatalogKpi;
}

describe('buildReportDataFromBracket', () => {
  const kpiMap = new Map<string, CatalogKpi>();
  kpiMap.set('KPI_001', makeKpi('KPI_001', 'Revenue', '#,0'));
  kpiMap.set('KPI_002', makeKpi('KPI_002', 'Gross Margin', '0.0%'));
  kpiMap.set('KPI_003', makeKpi('KPI_003', 'COGS', '#,0'));

  it('builds KPI snapshots from catalog', () => {
    const data = buildReportDataFromBracket(
      'UC001', kpiMap, ['KPI_001', 'KPI_002', 'KPI_003'], 'Test Project',
    );
    expect(data.kpis).toHaveLength(3);
    expect(data.kpis[0].label).toBe('Revenue');
    expect(data.kpis[1].label).toBe('Gross Margin');
  });

  it('infers unit from formatString', () => {
    const data = buildReportDataFromBracket(
      'UC001', kpiMap, ['KPI_002'], 'Test',
    );
    expect(data.kpis[0].unit).toBe('%');
  });

  it('sets bracketTitle on report data', () => {
    const data = buildReportDataFromBracket(
      'UC001', kpiMap, ['KPI_001'], 'Test',
    );
    expect(data.bracketTitle).toBe('UC001');
  });

  it('uses strategic KPI name as trend label', () => {
    const data = buildReportDataFromBracket(
      'UC001', kpiMap, ['KPI_001', 'KPI_002'], 'Test',
    );
    expect(data.trendLabel).toBe('Revenue');
  });

  it('builds waterfall from influencing KPIs', () => {
    const data = buildReportDataFromBracket(
      'UC001', kpiMap, ['KPI_001', 'KPI_002', 'KPI_003'], 'Test',
    );
    expect(data.waterfall.length).toBeGreaterThanOrEqual(2);
    expect(data.waterfall[0].driver).toBe('Gross Margin');
  });

  it('skips KPIs not in catalog gracefully', () => {
    const data = buildReportDataFromBracket(
      'UC001', kpiMap, ['KPI_001', 'MISSING_KPI'], 'Test',
    );
    expect(data.kpis).toHaveLength(1);
  });

  it('generates 12 trend periods', () => {
    const data = buildReportDataFromBracket(
      'UC001', kpiMap, ['KPI_001'], 'Test',
    );
    expect(data.trend).toHaveLength(12);
  });
});
