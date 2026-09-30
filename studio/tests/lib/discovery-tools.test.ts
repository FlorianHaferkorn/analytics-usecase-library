import { describe, it, expect } from 'vitest';
import { discoveryTools } from '@/lib/ai/tools/discovery-tools';

type KpiResult = { kpi_id: string; name: string; type: string; role: string; domains: string[]; definition: string; dax: string };
type BracketResult = { id: string; title: string; domain: string; strategicKpiId: string; driverCount: number; actionCount: number };
type DraftResult = { id: string; yaml: string };
type ActionResult = { id: string; name: string; domain: string; status: string; triggerKpis: string[]; relationship: string };

describe('discovery-tools', () => {
  describe('lookup_kpi', () => {
    it('returns results when searching by name', async () => {
      const result = (await discoveryTools.lookup_kpi.execute!(
        { query: 'margin', searchBy: 'name' },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      )) as KpiResult[];
      expect(Array.isArray(result)).toBe(true);
      if (result.length > 0) {
        expect(result[0]).toHaveProperty('kpi_id');
        expect(result[0]).toHaveProperty('name');
      }
    });

    it('returns results when searching by domain', async () => {
      const result = (await discoveryTools.lookup_kpi.execute!(
        { query: 'Commercial', searchBy: 'domain' },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      )) as KpiResult[];
      expect(Array.isArray(result)).toBe(true);
    });

    it('limits results to 10', async () => {
      const result = (await discoveryTools.lookup_kpi.execute!(
        { query: '', searchBy: 'name' },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      )) as KpiResult[];
      expect(result.length).toBeLessThanOrEqual(10);
    });
  });

  describe('list_brackets', () => {
    it('returns brackets as array', async () => {
      const result = (await discoveryTools.list_brackets.execute!(
        { domain: undefined },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      )) as BracketResult[];
      expect(Array.isArray(result)).toBe(true);
      if (result.length > 0) {
        expect(result[0]).toHaveProperty('id');
        expect(result[0]).toHaveProperty('title');
        expect(result[0]).toHaveProperty('strategicKpiId');
      }
    });
  });

  describe('create_bracket_draft', () => {
    it('generates a YAML draft with correct structure', async () => {
      const result = (await discoveryTools.create_bracket_draft.execute!(
        {
          title: 'Test Use Case',
          domain: 'Commercial',
          strategicKpiId: 'KPI-COM-013',
          influencingKpiIds: ['KPI-COM-005'],
          actionCodeIds: ['C-M2.1'],
        },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      )) as DraftResult;
      expect(result).toHaveProperty('id');
      expect(result).toHaveProperty('yaml');
      expect(result.yaml).toContain('schema_version: "2.0"');
      expect(result.yaml).toContain('Test Use Case');
      expect(result.yaml).toContain('KPI-COM-013');
    });
  });

  describe('suggest_actions', () => {
    it('returns actions related to a KPI', async () => {
      const result = (await discoveryTools.suggest_actions.execute!(
        { kpiId: 'KPI-COM-013' },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      )) as ActionResult[];
      expect(Array.isArray(result)).toBe(true);
      for (const a of result) {
        expect(a).toHaveProperty('id');
        expect(a).toHaveProperty('relationship');
      }
    });
  });
});
