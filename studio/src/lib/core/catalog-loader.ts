/**
 * KPI Catalog Loader
 *
 * Parses the KPI Catalog markdown file (which embeds a YAML block)
 * and returns typed KPI definition objects. Server-side only (fs access).
 */

import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { parse } from 'yaml';

const KPI_CATALOG_PATH = join(
  process.cwd(),
  '..',
  'core',
  'kpi_catalog',
  'KPI_Catalog.md'
);

/** Minimal KPI shape extracted from the catalog's embedded YAML. */
export interface CatalogKpi {
  kpi_id: string;
  kpi_key: string;
  kpi_type: string;
  kpi_role: string;
  impact_dimension: string;
  domain_tag: string[];
  use_case_ref: string[];
  action_code_ref: string[];
  calc_type: string;
  business: {
    purpose: string;
    definition: string;
    grain_scope: string;
    unit_format: string;
    interpretation: string;
  };
  technical: {
    dax_name: string;
    formatString: string;
    description: string;
    dax_expression: string;
    depends_on_measures: string[];
    lineage: string[];
  };
  governance: {
    business_owner: string;
    data_owner: string;
    steward: string;
    review_cycle: string;
    validation_process: string;
    qa_rules: string[];
    version: string;
  };
  metadata_quality: {
    completeness_score: number;
    last_review: string;
  };
}

/**
 * Extract the YAML block from the KPI Catalog markdown.
 * The catalog wraps all KPIs in a single ```yaml ... ``` fenced block.
 */
function extractYamlBlock(markdown: string): string {
  const startMarker = '```yaml\n';
  const endMarker = '\n```';

  const start = markdown.indexOf(startMarker);
  if (start === -1) return '';

  const contentStart = start + startMarker.length;
  const end = markdown.indexOf(endMarker, contentStart);
  if (end === -1) return markdown.slice(contentStart);

  return markdown.slice(contentStart, end);
}

/**
 * Load all KPIs from the catalog.
 *
 * The KPI Catalog YAML may contain minor structural issues (e.g. multiline
 * domain_tag values). We split by top-level "- kpi_id:" entries and parse
 * each individually, skipping any that fail.
 */
export async function loadKpiCatalog(): Promise<CatalogKpi[]> {
  const raw = await readFile(KPI_CATALOG_PATH, 'utf-8');
  const yamlBlock = extractYamlBlock(raw);
  if (!yamlBlock) return [];

  // Split into individual KPI entries and parse each independently
  const entries = yamlBlock.split(/\n(?=- kpi_id:)/);
  const kpis: CatalogKpi[] = [];

  for (const entry of entries) {
    const trimmed = entry.trim();
    if (!trimmed || !trimmed.includes('kpi_id:')) continue;

    try {
      // Wrap single entry back into a list for consistent parsing
      const yamlStr = trimmed.startsWith('-') ? trimmed : `- ${trimmed}`;
      const doc = parse(yamlStr) as unknown;
      if (Array.isArray(doc)) {
        for (const item of doc) {
          if (item && typeof item === 'object' && 'kpi_id' in item) {
            kpis.push(item as CatalogKpi);
          }
        }
      }
    } catch {
      // Skip malformed entries — log in dev if needed
    }
  }

  return kpis;
}

/** Load a single KPI by ID. */
export async function loadKpi(kpiId: string): Promise<CatalogKpi | null> {
  const all = await loadKpiCatalog();
  return all.find((k) => k.kpi_id === kpiId) ?? null;
}

/** Load the KPI catalog as a Map keyed by kpi_id. */
export async function loadKpiMap(): Promise<Map<string, CatalogKpi>> {
  const kpis = await loadKpiCatalog();
  return new Map(kpis.map((k) => [k.kpi_id, k]));
}

/** Get unique domain tags from the catalog. */
export async function loadDomainTags(): Promise<string[]> {
  const all = await loadKpiCatalog();
  const tags = new Set<string>();
  for (const kpi of all) {
    for (const tag of kpi.domain_tag ?? []) {
      tags.add(tag);
    }
  }
  return [...tags].sort();
}
