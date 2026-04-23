/**
 * Entity Context Builder
 *
 * Builds a compact YAML-style context string (< 1500 chars) from governed
 * Core artifacts for injection into the Studio AI chat system prompt.
 * Server-side only — imports node:fs loaders.
 */

import { loadKpi } from '@/lib/core/catalog-loader';
import { getFactsheetForKpi } from '@/lib/core/factsheet-loader';
import { loadBracket } from '@/lib/core/bracket-loader';
import { loadFactsheet } from '@/lib/core/factsheet-loader';

export interface EntityContext {
  entityType: 'kpi' | 'bracket' | 'use_case' | 'general';
  entityId?: string;
}

/** Truncate a string to max chars, appending "..." when truncated. */
function trunc(value: string | undefined | null, max = 200): string {
  if (!value) return '—';
  return value.length > max ? value.slice(0, max) + '...' : value;
}

/** Format a bullet list from an array, limiting to maxItems entries. */
function bulletList(items: string[] | undefined | null, maxItems = 3): string {
  if (!items || items.length === 0) return '  - —';
  return items
    .slice(0, maxItems)
    .map((q) => `  - ${trunc(q)}`)
    .join('\n');
}

async function buildKpiContext(entityId: string): Promise<string> {
  const [kpi, factsheetResult] = await Promise.all([
    loadKpi(entityId),
    getFactsheetForKpi(entityId),
  ]);

  if (!kpi) return '';

  const domain = (kpi.domain_tag ?? [])[0] ?? '—';
  const dax = trunc(kpi.technical?.dax_expression, 200);

  let out = `## KPI Context: ${kpi.kpi_id}
name: ${trunc(kpi.kpi_key)}
domain: ${domain}
purpose: ${trunc(kpi.business?.purpose)}
definition: ${trunc(kpi.business?.definition)}
grain: ${trunc(kpi.business?.grain_scope)}
unit: ${trunc(kpi.business?.unit_format)}
dax_expression: |
  ${dax}`;

  if (factsheetResult) {
    const { factsheet, role } = factsheetResult;
    out += `\n\n## Use Case Context (from Business Factsheet)
factsheet_id: ${factsheet.id}
factsheet_role: ${role}
use_case_purpose: ${trunc(factsheet.purpose)}
business_questions:
${bulletList(factsheet.business_questions)}`;
  }

  return out;
}

async function buildBracketContext(entityId: string): Promise<string> {
  const bracket = await loadBracket(entityId);
  if (!bracket) return '';

  const factsheet = await loadFactsheet(entityId).catch(() => null);

  let out = `## Bracket Context: ${bracket.id}
title: ${trunc(bracket.title)}
domain: ${trunc(bracket.domain)}
strategic_kpi: ${trunc(bracket.orchestration.strategic_kpi_id)}
formula: ${trunc(bracket.value_driver_model.formula)}
impact_direction: ${bracket.value_driver_model.impact_direction}`;

  if (factsheet) {
    out += `\n\n## Business Factsheet
purpose: ${trunc(factsheet.purpose)}
business_value: ${trunc(factsheet.business_value)}
business_questions:
${bulletList(factsheet.business_questions, 2)}`;
  }

  return out;
}

async function buildUseCaseContext(entityId: string): Promise<string> {
  // use_case is treated the same as bracket — brackets are the machine-readable
  // representation of use cases
  return buildBracketContext(entityId);
}

/**
 * Build a compact context string for the given entity.
 * Returns an empty string for `general` or when no data is found.
 */
export async function buildEntityContext(ctx: EntityContext): Promise<string> {
  if (!ctx.entityId) return '';

  switch (ctx.entityType) {
    case 'kpi':
      return buildKpiContext(ctx.entityId);
    case 'bracket':
      return buildBracketContext(ctx.entityId);
    case 'use_case':
      return buildUseCaseContext(ctx.entityId);
    case 'general':
    default:
      return '';
  }
}

