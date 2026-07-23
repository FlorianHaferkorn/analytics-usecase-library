/**
 * KPI Catalog Loader
 *
 * Parses the KPI Catalog markdown file (which embeds a YAML block)
 * and returns typed KPI definition objects. Server-side only (fs access).
 */

import 'server-only';

import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { parse, stringify } from 'yaml';
import type { CatalogKpi } from './catalog-types';

export type { CatalogKpi } from './catalog-types';

const KPI_CATALOG_PATH = join(
  process.cwd(),
  '..',
  'core',
  'kpi_catalog',
  'KPI_Catalog.md'
);

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
  const raw = (await readFile(KPI_CATALOG_PATH, 'utf-8')).replace(/\r\n/g, '\n');
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

function kpisToYamlBlock(kpis: CatalogKpi[]): string {
  return kpis
    .map((kpi) => {
      const body = stringify(kpi).trim();
      return body.startsWith('-') ? body : `- ${body}`;
    })
    .join('\n');
}

function replaceYamlBlock(markdown: string, yamlBlock: string): string {
  const startMarker = '```yaml\n';
  const endMarker = '\n```';
  const start = markdown.indexOf(startMarker);
  if (start === -1) throw new Error('KPI catalog YAML fence not found');
  const contentStart = start + startMarker.length;
  const end = markdown.indexOf(endMarker, contentStart);
  if (end === -1) throw new Error('KPI catalog YAML fence end not found');
  return `${markdown.slice(0, contentStart)}${yamlBlock}${markdown.slice(end)}`;
}

/** Patch KPI display fields and persist to KPI_Catalog.md. */
export async function updateKpiInCatalog(
  kpiId: string,
  patch: { kpi_key?: string; business?: Partial<CatalogKpi['business']> },
): Promise<CatalogKpi | null> {
  const kpis = await loadKpiCatalog();
  const index = kpis.findIndex((k) => k.kpi_id === kpiId);
  if (index < 0) return null;

  const updated: CatalogKpi = {
    ...kpis[index],
    ...(patch.kpi_key ? { kpi_key: patch.kpi_key } : {}),
    business: { ...kpis[index].business, ...patch.business },
  };
  kpis[index] = updated;

  const raw = (await readFile(KPI_CATALOG_PATH, 'utf-8')).replace(/\r\n/g, '\n');
  const next = replaceYamlBlock(raw, kpisToYamlBlock(kpis));
  await writeFile(KPI_CATALOG_PATH, next, 'utf-8');

  return updated;
}

/** Append a new KPI to KPI_Catalog.md (wizard / governance draft). */
export async function addKpiToCatalog(kpi: CatalogKpi): Promise<string> {
  const kpis = await loadKpiCatalog();
  if (kpis.some((k) => k.kpi_id === kpi.kpi_id)) {
    throw new Error(`KPI already exists: ${kpi.kpi_id}`);
  }
  kpis.push(kpi);
  const raw = (await readFile(KPI_CATALOG_PATH, 'utf-8')).replace(/\r\n/g, '\n');
  const next = replaceYamlBlock(raw, kpisToYamlBlock(kpis));
  await writeFile(KPI_CATALOG_PATH, next, 'utf-8');
  return 'core/kpi_catalog/KPI_Catalog.md';
}
