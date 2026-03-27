import { describe, it, expect, vi } from 'vitest';
import { buildIRPackage } from '@/lib/delivery/ir-builder';
import type { CatalogKpi } from '@/lib/core/catalog-loader';

// Minimal bracket fixture
const mockBracket = {
  id: 'UC001',
  schema_version: '2.0',
  title: 'Revenue Growth',
  domain: 'Finance',
  orchestration: {
    strategic_kpi_id: 'KPI_001',
    influencing_kpi_ids: ['KPI_002', 'KPI_003'],
    supporting_kpi_ids: ['KPI_004'],
    action_code_ids: ['AC_001'],
  },
  ux_layout_rules: {
    page_1_summary: {
      title: 'Revenue Summary',
      template_id: 'pulse',
      component_3s: {
        kpi_id: 'KPI_001',
        visual_type: 'kpi_card',
      },
      component_30s: [
        {
          kpi_ids: ['KPI_002'],
          visual_type: 'line_chart',
        },
      ],
    },
    page_2_execution: {
      title: 'Revenue Actions',
      template_id: 'action_matrix',
      component_300s: {
        evidence_grain: 'weekly',
        evidence_columns: ['product', 'region'],
        action_panel: true,
      },
    },
  },
  governance: {},
} as never;

function makeKpi(id: string, daxName: string): CatalogKpi {
  return {
    kpi_id: id,
    business: { purpose: `Purpose of ${id}` },
    technical: {
      dax_name: daxName,
      dax_expression: `SUM(Table[${daxName}])`,
      formatString: '#,0',
      description: `Desc ${id}`,
      depends_on_measures: [],
    },
    governance: {},
    metadata_quality: {},
  } as CatalogKpi;
}

describe('buildIRPackage', () => {
  const kpiMap = new Map<string, CatalogKpi>();
  kpiMap.set('KPI_001', makeKpi('KPI_001', 'Revenue'));
  kpiMap.set('KPI_002', makeKpi('KPI_002', 'OnlineRevenue'));
  kpiMap.set('KPI_003', makeKpi('KPI_003', 'StoreRevenue'));
  kpiMap.set('KPI_004', makeKpi('KPI_004', 'FootTraffic'));

  it('collects all referenced KPIs as measures', () => {
    const ir = buildIRPackage(mockBracket, kpiMap);
    expect(ir.measures).toHaveLength(4);
    const ids = ir.measures.map((m) => m.id);
    expect(ids).toContain('KPI_001');
    expect(ids).toContain('KPI_002');
    expect(ids).toContain('KPI_003');
    expect(ids).toContain('KPI_004');
  });

  it('sets correct metadata', () => {
    const ir = buildIRPackage(mockBracket, kpiMap);
    expect(ir.useCaseId).toBe('UC001');
    expect(ir.title).toBe('Revenue Growth');
    expect(ir.domain).toBe('Finance');
    expect(ir.metadata.schemaVersion).toBe('2.0');
    expect(ir.metadata.generatedAt).toBeTruthy();
  });

  it('builds pages from ux_layout_rules', () => {
    const ir = buildIRPackage(mockBracket, kpiMap);
    expect(ir.pages).toHaveLength(2);
    expect(ir.pages[0].title).toBe('Revenue Summary');
    expect(ir.pages[1].title).toBe('Revenue Actions');
  });

  it('builds 3s, 30s, and 300s components', () => {
    const ir = buildIRPackage(mockBracket, kpiMap);
    const p1Components = ir.pages[0].components;
    expect(p1Components.some((c) => c.slot === '3s')).toBe(true);
    expect(p1Components.some((c) => c.slot === '30s')).toBe(true);

    const p2Components = ir.pages[1].components;
    expect(p2Components.some((c) => c.slot === '300s')).toBe(true);
  });

  it('skips KPIs not found in the map', () => {
    const sparseMap = new Map<string, CatalogKpi>();
    sparseMap.set('KPI_001', makeKpi('KPI_001', 'Revenue'));
    // KPI_002, 003, 004 missing
    const ir = buildIRPackage(mockBracket, sparseMap);
    expect(ir.measures).toHaveLength(1);
    expect(ir.measures[0].id).toBe('KPI_001');
  });

  it('includes action code IDs', () => {
    const ir = buildIRPackage(mockBracket, kpiMap);
    expect(ir.actionCodes).toEqual(['AC_001']);
  });
});
