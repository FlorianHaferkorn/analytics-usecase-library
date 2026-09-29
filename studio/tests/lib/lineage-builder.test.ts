import { describe, it, expect } from 'vitest';
import { buildLineageGraph } from '@/lib/core/lineage-builder';
import type { ResolvedContract } from '@/lib/core/contract-loader';
import type { CatalogKpi } from '@/lib/core/catalog-loader';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';

function makeContract(domain: string): ResolvedContract {
  return {
    domain,
    version: '1.0',
    owner: 'test',
    dimension: [
      { name: 'dim_date', columns: [{ name: 'Date', type: 'date', role: 'key' }] },
    ],
    fact: [
      {
        name: 'fact_sales',
        grain: 'invoice_line',
        columns: [
          { name: 'Amount', type: 'decimal', agg: 'sum' },
          { name: 'Date', type: 'date', ref: 'dim_date.Date' },
        ],
      },
    ],
  };
}

function makeKpi(id: string, lineage: string[] = [], deps: string[] = []): CatalogKpi {
  return {
    kpi_id: id,
    kpi_key: `KPI ${id}`,
    kpi_type: 'diagnostic',
    kpi_role: 'strategic',
    impact_dimension: 'Test',
    domain_tag: ['Test'],
    use_case_ref: [],
    action_code_ref: [],
    calc_type: 'measure',
    business: { purpose: '', definition: '', grain_scope: '', unit_format: '', interpretation: '' },
    technical: {
      dax_name: id,
      formatString: '#,0',
      description: '',
      dax_expression: '',
      depends_on_measures: deps,
      lineage,
    },
    governance: {
      business_owner: '', data_owner: '', steward: '',
      review_cycle: '', validation_process: '', qa_rules: [], version: '1.0',
    },
    metadata_quality: { completeness_score: 1, last_review: '2024-01-01' },
  };
}

function makeBracket(id: string, strategicKpi: string, influencing: string[]): UseCaseBracketV20Lean {
  return {
    schema_version: '2.0',
    id,
    title: `Bracket ${id}`,
    domain: 'Test',
    governance: { owner_role: 'test', steward_role: 'test' },
    orchestration: {
      strategic_kpi_id: strategicKpi,
      influencing_kpi_ids: influencing,
      action_code_ids: [],
    },
    value_driver_model: { formula: '', impact_direction: 'maximize' },
    ux_layout_rules: {
      report_structure: '2-Page-Lead',
      page_1_summary: {
        title: 'Summary',
        component_3s: { kpi_id: strategicKpi, visual_type: 'kpi_card' },
        component_30s: [],
      },
      page_2_execution: {
        title: 'Execution',
        component_300s: { evidence_grain: 'test', evidence_columns: [], action_panel: true, payload_mode: 'full' },
      },
    },
    documentation: { business_factsheet: './test.md' },
  };
}

describe('buildLineageGraph', () => {
  it('creates nodes for dimension, fact, kpi, and bracket', async () => {
    const graph = await buildLineageGraph({
      contracts: [makeContract('commercial')],
      kpis: [makeKpi('K1', ['fact_sales.Amount'])],
      brackets: [makeBracket('B1', 'K1', [])],
    });

    const types = graph.nodes.map((n) => n.type);
    expect(types).toContain('dimension');
    expect(types).toContain('fact');
    expect(types).toContain('kpi');
    expect(types).toContain('bracket');
  });

  it('connects fact to dimension via foreign key refs', async () => {
    const graph = await buildLineageGraph({
      contracts: [makeContract('commercial')],
      kpis: [],
      brackets: [],
    });

    const dimToFact = graph.edges.filter(
      (e) => e.source === 'dim:dim_date' && e.target === 'fact:fact_sales',
    );
    expect(dimToFact).toHaveLength(1);
    expect(dimToFact[0].relationship).toBe('sources');
  });

  it('connects KPI to fact table via lineage', async () => {
    const graph = await buildLineageGraph({
      contracts: [makeContract('commercial')],
      kpis: [makeKpi('K1', ['fact_sales.Amount'])],
      brackets: [],
    });

    const factToKpi = graph.edges.filter(
      (e) => e.source === 'fact:fact_sales' && e.target === 'kpi:K1',
    );
    expect(factToKpi).toHaveLength(1);
    expect(factToKpi[0].relationship).toBe('computes');
  });

  it('connects KPI to KPI via depends_on_measures', async () => {
    const graph = await buildLineageGraph({
      contracts: [],
      kpis: [makeKpi('K1'), makeKpi('K2', [], ['K1'])],
      brackets: [],
    });

    const kpiToKpi = graph.edges.filter(
      (e) => e.source === 'kpi:K1' && e.target === 'kpi:K2',
    );
    expect(kpiToKpi).toHaveLength(1);
  });

  it('connects bracket to its KPIs', async () => {
    const graph = await buildLineageGraph({
      contracts: [],
      kpis: [makeKpi('K1'), makeKpi('K2')],
      brackets: [makeBracket('B1', 'K1', ['K2'])],
    });

    const kpiToBracket = graph.edges.filter(
      (e) => e.target === 'bracket:B1' && e.relationship === 'consumes',
    );
    expect(kpiToBracket).toHaveLength(2);
  });

  it('returns empty graph for empty inputs', async () => {
    const graph = await buildLineageGraph({
      contracts: [],
      kpis: [],
      brackets: [],
    });
    expect(graph.nodes).toHaveLength(0);
    expect(graph.edges).toHaveLength(0);
  });
});
