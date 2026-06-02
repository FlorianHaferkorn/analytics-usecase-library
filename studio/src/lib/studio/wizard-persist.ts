/**
 * Persist wizard drafts to governed core/ artifacts (server-only).
 */

import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { stringify } from 'yaml';
import { addKpiToCatalog, type CatalogKpi } from '@/lib/core/catalog-loader';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { parseYaml } from '@/lib/core/yaml-loader';

const REPO_CORE = join(process.cwd(), '..', 'core');
const USECASES_DIR = join(REPO_CORE, 'usecases', 'core');
const ACTION_CODES_DIR = join(REPO_CORE, 'action_codes');
const SOURCES_DIR = join(REPO_CORE, 'data_contracts', 'sources');

export type WizardPersistKind = 'kpi' | 'bracket' | 'action' | 'source';

export interface WizardDraftInput {
  name: string;
  ref: string;
  domain: string;
  type: string;
  grain: string;
  description: string;
  sql?: string;
}

export interface WizardPersistResult {
  kind: WizardPersistKind;
  entityId: string;
  path: string;
  detailHref: string;
}

const DOMAIN_TAG_MAP: Record<string, string> = {
  Revenue: 'Commercial',
  Operations: 'Operations',
  Finance: 'Finance',
  Customer: 'Customer & Market',
  Supply: 'Supply Chain',
  Quality: 'Operations',
  HR: 'People',
};

const BRACKET_DOMAIN_MAP: Record<string, string> = {
  Revenue: 'Commercial',
  Operations: 'Operations',
  Finance: 'Finance',
  Customer: 'Commercial',
  Supply: 'SupplyChain',
  Quality: 'Operations',
  HR: 'XD',
};

const DOMAIN_PREFIX: Record<string, string> = {
  Commercial: 'COM',
  Finance: 'FIN',
  Operations: 'OPS',
  SupplyChain: 'SCM',
  XD: 'XD',
};

function slugId(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 32);
}

function kpiIdFromRef(ref: string): string {
  if (ref.startsWith('met.')) return ref.slice(4);
  return ref.replace(/\./g, '.');
}

function domainFolder(domain: string): string {
  const map: Record<string, string> = {
    Commercial: 'Commercial',
    Finance: 'Finance',
    Operations: 'Operations',
    Supply: 'SupplyChain',
    'Supply Chain': 'SupplyChain',
    Customer: 'Commercial',
    Revenue: 'Commercial',
  };
  return map[domain] ?? 'Commercial';
}

function uniqueActionId(): string {
  const n = Date.now() % 90 + 10;
  return `C-W${n}.1`;
}

function newUseCaseId(domain: string): string {
  const prefix = DOMAIN_PREFIX[BRACKET_DOMAIN_MAP[domain] ?? 'Commercial'] ?? 'XD';
  const suffix = Date.now().toString(36).slice(-4).toUpperCase();
  return `${prefix}-W${suffix}`;
}

function buildFactsheetMarkdown(id: string, draft: WizardDraftInput): string {
  const domain = BRACKET_DOMAIN_MAP[draft.domain] ?? draft.domain;
  return `---
id: ${id}
factsheet_type: business
---

# ${id} - ${draft.name}

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** ${id}
- **Domain:** ${domain}
- **Business Owner:** TBD
- **KPI Owner:** TBD
- **Decision Owner:** TBD
- **Reporting Level:** ${draft.type}
- **Analytics Stage:** Draft (wizard)

---

## 1. Business Summary

**Purpose:** ${draft.description}
**Business Value:** TBD — refine after first review cycle.
**Out of Scope:** TBD

---

## 2. Core Business Questions

- What decision does this use case enable?
- Which KPIs and actions should be wired in the bracket?

---

## 3. KPI Roles

| KPI ID | Role |
| --- | --- |
| margin.gm.pct | Strategic |

`;
}

function buildBracketYaml(id: string, draft: WizardDraftInput): string {
  const domain = BRACKET_DOMAIN_MAP[draft.domain] ?? 'Commercial';
  const doc = {
    schema_version: '2.0',
    id,
    title: draft.name,
    domain,
    governance: {
      owner_role: 'commercial_controlling_lead',
      steward_role: 'commercial_bi_pricing_analytics_lead',
    },
    orchestration: {
      strategic_kpi_id: 'margin.gm.pct',
      influencing_kpi_ids: [] as string[],
      action_code_ids: [] as string[],
      supporting_kpi_ids: [] as string[],
    },
    value_driver_model: {
      formula: `${draft.ref} — refine in bracket editor`,
      impact_direction: 'maximize' as const,
      impact_logic: draft.description,
    },
    ux_layout_rules: {
      report_structure: '2-Page-Lead',
      report_canvas: { width: 1920, height: 1080 },
      page_1_summary: {
        title: `${draft.name} — Overview`,
        template_id: 'pulse',
        component_3s: { kpi_id: 'margin.gm.pct', visual_type: 'kpi_card' },
        component_30s: [],
      },
      page_2_execution: {
        title: `${draft.name} — Detail`,
        template_id: 'investigator',
        component_300s: {
          evidence_grain: draft.grain === 'day' ? 'day' : 'month',
          evidence_columns: ['entity'],
          action_panel: false,
          payload_mode: 'summary' as const,
        },
      },
    },
    documentation: { business_factsheet: 'Business_Factsheet.md' },
  };
  return stringify(doc);
}

function draftToKpi(draft: WizardDraftInput): CatalogKpi {
  const kpiId = kpiIdFromRef(draft.ref);
  const domainTag = DOMAIN_TAG_MAP[draft.domain] ?? draft.domain;
  const today = new Date().toISOString().slice(0, 10);
  return {
    kpi_id: kpiId,
    kpi_key: draft.name,
    kpi_type: 'diagnostic',
    kpi_role: 'influencing',
    impact_dimension: domainTag,
    domain_tag: [domainTag],
    use_case_ref: [],
    action_code_ref: [],
    calc_type: draft.type.toLowerCase().includes('ratio') ? 'ratio' : 'amount',
    business: {
      purpose: draft.description,
      definition: draft.description,
      grain_scope: draft.grain,
      unit_format: 'TBD',
      interpretation: 'Draft from Studio wizard — complete metadata in Detail.',
    },
    technical: {
      dax_name: draft.name.replace(/\s+/g, ''),
      formatString: '#,0',
      description: draft.sql ? `${draft.description}\n\nSQL (draft):\n${draft.sql}` : draft.description,
      dax_expression: '0',
      depends_on_measures: [],
      lineage: [],
    },
    governance: {
      business_owner: 'TBD',
      data_owner: 'TBD',
      steward: 'TBD',
      review_cycle: 'quarterly',
      validation_process: 'wizard draft',
      qa_rules: [],
      version: 'v0.1',
    },
    metadata_quality: {
      completeness_score: 0.45,
      last_review: today,
    },
  };
}

export async function persistWizardDraft(
  kind: WizardPersistKind,
  draft: WizardDraftInput,
  actorEmail: string,
): Promise<WizardPersistResult> {
  switch (kind) {
    case 'kpi': {
      const kpi = draftToKpi(draft);
      const path = await addKpiToCatalog(kpi);
      logAuditEvent('kpi', kpi.kpi_id, 'create', { before: null, after: { kpi_key: kpi.kpi_key } }, 'default', actorEmail);
      return {
        kind,
        entityId: kpi.kpi_id,
        path,
        detailHref: `/detail/kpi/${encodeURIComponent(kpi.kpi_id)}`,
      };
    }
    case 'action': {
      const actionId = uniqueActionId();
      const folder = domainFolder(draft.domain);
      const yaml = stringify({
        schema_version: '2.0',
        id: actionId,
        name: draft.name,
        owner_domain: folder === 'SupplyChain' ? 'SupplyChain' : folder,
        impact_dimension: draft.domain,
        status: 'draft',
        owner_role: 'bi_lead',
        steward_role: 'bi_lead',
        use_case_links: { core_use_cases: [], related_use_cases: [] },
        kpis: { trigger_kpis: [], guardrail_kpis: [], outcome_kpis: [] },
        scope: { default_grain: draft.grain, default_perspective: [], supported_slices: [], exclusions: [] },
        trigger: {
          type: 'Manual',
          evaluation: { grain: draft.grain, window: { type: 'rolling', periods: 1 } },
        },
        playbook: { summary: draft.description, steps: [] },
      });
      const dir = join(ACTION_CODES_DIR, folder);
      await mkdir(dir, { recursive: true });
      const fileName = `${actionId.replace(/\./g, '_')}.yaml`;
      const filePath = join(dir, fileName);
      await writeFile(filePath, yaml, 'utf-8');
      logAuditEvent('governance', actionId, 'create', { before: null, after: { name: draft.name } }, 'default', actorEmail);
      return {
        kind,
        entityId: actionId,
        path: `core/action_codes/${folder}/${fileName}`,
        detailHref: `/library?tab=actions`,
      };
    }
    case 'source': {
      const slug = slugId(draft.name || draft.ref);
      const fileName = `wizard_${slug}.yaml`;
      const filePath = join(SOURCES_DIR, fileName);
      const domainSlug = slugId(BRACKET_DOMAIN_MAP[draft.domain] ?? 'commercial');
      const yaml = stringify({
        source_system: draft.name,
        domain: `${domainSlug}_sales`,
        version: 'v0.1',
        description: draft.description,
        tables: [
          {
            name: slugId(draft.ref),
            target: `fact_${slug}`,
            grain: draft.grain,
            columns: [{ name: 'value', maps_to: 'Value' }],
          },
        ],
      });
      await mkdir(SOURCES_DIR, { recursive: true });
      await writeFile(filePath, yaml, 'utf-8');
      logAuditEvent('governance', fileName, 'create', { before: null, after: { domain: draft.domain } }, 'default', actorEmail);
      return {
        kind,
        entityId: fileName.replace('.yaml', ''),
        path: `core/data_contracts/sources/${fileName}`,
        detailHref: `/library?tab=sources`,
      };
    }
    case 'bracket': {
      const id = newUseCaseId(draft.domain);
      const dirName = `${id}_${slugId(draft.name)}`;
      const dirPath = join(USECASES_DIR, dirName);
      await mkdir(dirPath, { recursive: true });
      const factsheet = buildFactsheetMarkdown(id, draft);
      const bracketYaml = buildBracketYaml(id, draft);
      parseYaml(bracketYaml);
      await writeFile(join(dirPath, 'Business_Factsheet.md'), factsheet, 'utf-8');
      await writeFile(join(dirPath, 'UseCase_Bracket.yaml'), bracketYaml, 'utf-8');
      logAuditEvent('bracket', id, 'create', { before: null, after: { title: draft.name } }, 'default', actorEmail);
      logAuditEvent('factsheet', id, 'create', { before: null, after: { title: draft.name } }, 'default', actorEmail);
      return {
        kind,
        entityId: id,
        path: `core/usecases/core/${dirName}/`,
        detailHref: `/detail/usecase/${encodeURIComponent(id)}?tab=factsheet`,
      };
    }
  }
  throw new Error(`Unknown wizard kind: ${String(kind)}`);
}
