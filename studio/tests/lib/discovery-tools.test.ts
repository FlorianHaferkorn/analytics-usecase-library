import { describe, it, expect } from 'vitest';
import { discoveryTools } from '@/lib/ai/tools/discovery-tools';

describe('discovery-tools', () => {
  describe('lookup_kpi', () => {
    it('returns results when searching by name', async () => {
      const result = await discoveryTools.lookup_kpi.execute(
        { query: 'margin', searchBy: 'name' },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      );
      expect(Array.isArray(result)).toBe(true);
      if (result.length > 0) {
        expect(result[0]).toHaveProperty('kpi_id');
        expect(result[0]).toHaveProperty('name');
      }
    });

    it('returns results when searching by domain', async () => {
      const result = await discoveryTools.lookup_kpi.execute(
        { query: 'Commercial', searchBy: 'domain' },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      );
      expect(Array.isArray(result)).toBe(true);
    });

    it('limits results to 10', async () => {
      const result = await discoveryTools.lookup_kpi.execute(
        { query: '', searchBy: 'name' },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      );
      expect(result.length).toBeLessThanOrEqual(10);
    });
  });

  describe('list_brackets', () => {
    it('returns brackets as array', async () => {
      const result = await discoveryTools.list_brackets.execute(
        { domain: undefined },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      );
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
      const result = await discoveryTools.create_bracket_draft.execute(
        {
          title: 'Test Use Case',
          domain: 'Commercial',
          strategicKpiId: 'margin.gm.pct',
          influencingKpiIds: ['sales.net_sales.amount'],
          actionCodeIds: ['C-M2.1'],
        },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      );
      expect(result).toHaveProperty('id');
      expect(result).toHaveProperty('yaml');
      expect(result.yaml).toContain('schema_version: "2.0"');
      expect(result.yaml).toContain('Test Use Case');
      expect(result.yaml).toContain('margin.gm.pct');
    });
  });

  describe('suggest_actions', () => {
    it('returns actions related to a KPI', async () => {
      const result = await discoveryTools.suggest_actions.execute(
        { kpiId: 'margin.gm.pct' },
        { toolCallId: 'test', messages: [], abortSignal: undefined as never },
      );
      expect(Array.isArray(result)).toBe(true);
      for (const a of result) {
        expect(a).toHaveProperty('id');
        expect(a).toHaveProperty('relationship');
      }
    });
  });
});
