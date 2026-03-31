import { describe, it, expect } from 'vitest';
import { runDriftScan } from '@/lib/validation/drift-scanner';
import type { CatalogKpi } from '@/lib/core/catalog-loader';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import type { ActionCodeDefinitionV20AIMirror } from '@/lib/schemas';

function makeKpi(id: string, deps: string[] = []): CatalogKpi {
  return {
    kpi_id: id,
    kpi_key: id,
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
      lineage: [],
    },
    governance: {
      business_owner: '',
      data_owner: '',
      steward: '',
      review_cycle: '',
      validation_process: '',
      qa_rules: [],
      version: '1.0',
    },
    metadata_quality: { completeness_score: 1, last_review: '2024-01-01' },
  };
}

function makeBracket(
  id: string,
  strategicKpi: string,
  influencing: string[],
  actions: string[],
): UseCaseBracketV20Lean {
  return {
    schema_version: '2.0',
    id,
    title: `Test ${id}`,
    domain: 'Test',
    governance: { owner_role: 'test', steward_role: 'test' },
    orchestration: {
      strategic_kpi_id: strategicKpi,
      influencing_kpi_ids: influencing,
      action_code_ids: actions,
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
        component_300s: {
          evidence_grain: 'test',
          evidence_columns: [],
          action_panel: true,
          payload_mode: 'full',
        },
      },
    },
    documentation: { business_factsheet: './test.md' },
  };
}

function makeAction(
  id: string,
  triggerKpis: string[],
  status: 'active' | 'deprecated' = 'active',
): ActionCodeDefinitionV20AIMirror {
  return {
    schema_version: '2.0',
    id,
    name: `Action ${id}`,
    owner_domain: 'Test',
    impact_dimension: 'Test',
    status,
    owner_role: 'test',
    steward_role: 'test_steward',
    kpis: {
      trigger_kpis: triggerKpis as [string, ...string[]],
    },
    scope: { default_grain: 'day', default_perspective: [], supported_slices: [], exclusions: [] },
    trigger: {},
    impact: {},
    operational_execution: {},
    quality_rules: [],
  };
}

describe('runDriftScan', () => {
  it('returns empty issues when all references are valid', async () => {
    const report = await runDriftScan({
      kpis: [makeKpi('K1'), makeKpi('K2')],
      brackets: [makeBracket('B1', 'K1', ['K2'], ['A1'])],
      actions: [makeAction('A1', ['K1'])],
    });
    expect(report.counts.error).toBe(0);
    // K2 is referenced as influencing, K1 as strategic — no orphan KPIs
    // A1 is referenced — no orphan actions
  });

  it('detects broken bracket strategic_kpi_id', async () => {
    const report = await runDriftScan({
      kpis: [makeKpi('K1')],
      brackets: [makeBracket('B1', 'MISSING', ['K1'], [])],
      actions: [],
    });
    const errors = report.issues.filter((i) => i.severity === 'error');
    expect(errors).toHaveLength(1);
    expect(errors[0].referencedId).toBe('MISSING');
    expect(errors[0].field).toBe('orchestration.strategic_kpi_id');
  });

  it('detects broken bracket influencing_kpi_ids', async () => {
    const report = await runDriftScan({
      kpis: [makeKpi('K1')],
      brackets: [makeBracket('B1', 'K1', ['K1', 'MISSING'], [])],
      actions: [],
    });
    const errors = report.issues.filter((i) => i.severity === 'error');
    expect(errors).toHaveLength(1);
    expect(errors[0].referencedId).toBe('MISSING');
  });

  it('detects broken bracket action_code_ids', async () => {
    const report = await runDriftScan({
      kpis: [makeKpi('K1')],
      brackets: [makeBracket('B1', 'K1', [], ['MISSING'])],
      actions: [],
    });
    const errors = report.issues.filter((i) => i.severity === 'error');
    expect(errors).toHaveLength(1);
    expect(errors[0].referencedId).toBe('MISSING');
  });

  it('detects broken action trigger_kpis', async () => {
    const report = await runDriftScan({
      kpis: [makeKpi('K1')],
      brackets: [makeBracket('B1', 'K1', [], ['A1'])],
      actions: [makeAction('A1', ['MISSING'])],
    });
    const errors = report.issues.filter((i) => i.severity === 'error');
    expect(errors).toHaveLength(1);
    expect(errors[0].artifact).toBe('action');
    expect(errors[0].referencedId).toBe('MISSING');
  });

  it('detects orphan KPIs not referenced by any bracket', async () => {
    const report = await runDriftScan({
      kpis: [makeKpi('K1'), makeKpi('ORPHAN')],
      brackets: [makeBracket('B1', 'K1', [], [])],
      actions: [],
    });
    const warnings = report.issues.filter(
      (i) => i.severity === 'warning' && i.category === 'orphan' && i.artifact === 'kpi',
    );
    expect(warnings).toHaveLength(1);
    expect(warnings[0].artifactId).toBe('ORPHAN');
  });

  it('detects orphan actions not referenced by any bracket', async () => {
    const report = await runDriftScan({
      kpis: [makeKpi('K1')],
      brackets: [makeBracket('B1', 'K1', [], [])],
      actions: [makeAction('A-ORPHAN', ['K1'])],
    });
    const warnings = report.issues.filter(
      (i) => i.severity === 'warning' && i.category === 'orphan' && i.artifact === 'action',
    );
    expect(warnings).toHaveLength(1);
    expect(warnings[0].artifactId).toBe('A-ORPHAN');
  });

  it('flags deprecated actions still referenced by brackets', async () => {
    const report = await runDriftScan({
      kpis: [makeKpi('K1')],
      brackets: [makeBracket('B1', 'K1', [], ['A1'])],
      actions: [makeAction('A1', ['K1'], 'deprecated')],
    });
    const infos = report.issues.filter((i) => i.severity === 'info');
    expect(infos).toHaveLength(1);
    expect(infos[0].category).toBe('deprecated');
  });

  it('detects broken KPI depends_on_measures', async () => {
    const report = await runDriftScan({
      kpis: [makeKpi('K1', ['MISSING_DEP'])],
      brackets: [makeBracket('B1', 'K1', [], [])],
      actions: [],
    });
    const warnings = report.issues.filter(
      (i) => i.category === 'broken-ref' && i.artifact === 'kpi',
    );
    expect(warnings).toHaveLength(1);
    expect(warnings[0].referencedId).toBe('MISSING_DEP');
  });

  it('returns correct severity counts', async () => {
    const report = await runDriftScan({
      kpis: [makeKpi('K1'), makeKpi('K-ORPHAN')],
      brackets: [makeBracket('B1', 'MISSING', [], ['A1'])],
      actions: [makeAction('A1', ['K1'], 'deprecated')],
    });
    expect(report.counts.error).toBeGreaterThan(0);
    expect(report.counts.warning).toBeGreaterThan(0);
    expect(report.counts.info).toBeGreaterThan(0);
  });

  it('sorts issues by severity (errors first)', async () => {
    const report = await runDriftScan({
      kpis: [makeKpi('K1'), makeKpi('K-ORPHAN')],
      brackets: [makeBracket('B1', 'MISSING', [], ['A1'])],
      actions: [makeAction('A1', ['K1'], 'deprecated')],
    });
    const severities = report.issues.map((i) => i.severity);
    const errorIdx = severities.indexOf('error');
    const warningIdx = severities.indexOf('warning');
    const infoIdx = severities.indexOf('info');
    if (errorIdx >= 0 && warningIdx >= 0) expect(errorIdx).toBeLessThan(warningIdx);
    if (warningIdx >= 0 && infoIdx >= 0) expect(warningIdx).toBeLessThan(infoIdx);
  });
});
