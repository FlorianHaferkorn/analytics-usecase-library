/**
 * AI Discovery Tools — Vercel AI SDK structured tool definitions.
 *
 * These tools enable the AI to deterministically look up KPIs,
 * browse brackets, create drafts, validate YAML, and suggest actions
 * during Discovery chat sessions.
 */

import { z } from 'zod';
import { tool } from 'ai';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';

export const discoveryTools = {
  lookup_kpi: tool({
    description: 'Search the KPI catalog by ID, name, or domain. Returns matching KPI definitions.',
    inputSchema: z.object({
      query: z.string().describe('Search term: KPI ID, name fragment, or domain tag'),
      searchBy: z.enum(['id', 'name', 'domain']).default('name').describe('Field to search'),
    }),
    execute: async ({ query, searchBy }) => {
      const kpis = await loadKpiCatalog();
      const q = query.toLowerCase();
      const matches = kpis.filter((k) => {
        if (searchBy === 'id') return k.kpi_id.toLowerCase().includes(q);
        if (searchBy === 'domain') return k.domain_tag.some((d) => d.toLowerCase().includes(q));
        return k.kpi_key.toLowerCase().includes(q) || k.kpi_id.toLowerCase().includes(q);
      });
      return matches.slice(0, 10).map((k) => ({
        kpi_id: k.kpi_id,
        name: k.kpi_key,
        type: k.kpi_type,
        role: k.kpi_role,
        domains: k.domain_tag,
        definition: k.business?.definition,
        dax: k.technical?.dax_expression,
      }));
    },
  }),

  list_brackets: tool({
    description: 'List all use case brackets with their strategic KPI and action code counts.',
    inputSchema: z.object({
      domain: z.string().optional().describe('Optional domain filter'),
    }),
    execute: async ({ domain }) => {
      const brackets = await loadAllBrackets();
      const filtered = domain
        ? brackets.filter((b) => b.domain.toLowerCase().includes(domain.toLowerCase()))
        : brackets;
      return filtered.map((b) => ({
        id: b.id,
        title: b.title,
        domain: b.domain,
        strategicKpiId: b.orchestration.strategic_kpi_id,
        driverCount: b.orchestration.influencing_kpi_ids.length,
        actionCount: b.orchestration.action_code_ids.length,
      }));
    },
  }),

  create_bracket_draft: tool({
    description: 'Generate a YAML draft for a new use case bracket with the given parameters.',
    inputSchema: z.object({
      title: z.string().describe('Use case title'),
      domain: z.string().describe('Business domain'),
      strategicKpiId: z.string().describe('North Star KPI ID'),
      influencingKpiIds: z.array(z.string()).describe('Driver KPI IDs'),
      actionCodeIds: z.array(z.string()).describe('Action code IDs'),
    }),
    execute: async ({ title, domain, strategicKpiId, influencingKpiIds, actionCodeIds }) => {
      const id = `${domain.slice(0, 3).toUpperCase()}-${String(Date.now()).slice(-3)}`;
      const yaml = [
        `schema_version: "2.0"`,
        `id: "${id}"`,
        `title: "${title}"`,
        `domain: "${domain}"`,
        `governance:`,
        `  owner_role: "${domain.toLowerCase()}_controlling_lead"`,
        `  steward_role: "${domain.toLowerCase()}_bi_lead"`,
        `orchestration:`,
        `  strategic_kpi_id: "${strategicKpiId}"`,
        `  influencing_kpi_ids:`,
        ...influencingKpiIds.map((k) => `    - "${k}"`),
        `  action_code_ids:`,
        ...actionCodeIds.map((a) => `    - "${a}"`),
        `value_driver_model:`,
        `  formula: "${strategicKpiId} = f(${influencingKpiIds.join(', ')})"`,
        `  impact_direction: "maximize"`,
      ].join('\n');
      return { id, yaml };
    },
  }),

  validate_artifact: tool({
    description: 'Validate a YAML artifact against its JSON schema. Returns validation results.',
    inputSchema: z.object({
      yaml: z.string().describe('YAML content to validate'),
      schemaName: z.string().describe('Schema name: usecase_bracket, action_code, kpi_definition, or data_contract'),
    }),
    execute: async ({ yaml, schemaName }) => {
      // Dynamic import to avoid bundling fs in client
      const { validateYaml } = await import('@/lib/mcp/tools');
      return validateYaml(yaml, schemaName);
    },
  }),

  suggest_actions: tool({
    description: 'Suggest action codes relevant to a given KPI by searching trigger and outcome KPIs.',
    inputSchema: z.object({
      kpiId: z.string().describe('KPI ID to find relevant actions for'),
    }),
    execute: async ({ kpiId }) => {
      const actions = await loadAllActionCodes();
      const q = kpiId.toLowerCase();
      const matches = actions.filter((a) => {
        const triggers = a.kpis.trigger_kpis.map((t) => t.toLowerCase());
        const outcomes = (a.kpis.outcome_kpis ?? []).map((o) => o.toLowerCase());
        const guardrails = (a.kpis.guardrail_kpis ?? []).map((g) => g.toLowerCase());
        return triggers.includes(q) || outcomes.includes(q) || guardrails.includes(q);
      });
      return matches.map((a) => ({
        id: a.id,
        name: a.name,
        domain: a.owner_domain,
        status: a.status,
        triggerKpis: a.kpis.trigger_kpis,
        relationship: a.kpis.trigger_kpis.map((t) => t.toLowerCase()).includes(q)
          ? 'trigger'
          : a.kpis.outcome_kpis?.map((o) => o.toLowerCase()).includes(q)
            ? 'outcome'
            : 'guardrail',
      }));
    },
  }),
};
