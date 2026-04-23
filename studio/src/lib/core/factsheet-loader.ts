/**
 * Business Factsheet Loader
 *
 * Parses Business_Factsheet.md files from core/usecases/core/ and returns
 * typed FactsheetSummary objects. Server-side only (fs access).
 */

import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';

const CORE_USECASES_DIR = join(
  process.cwd(),
  '..',
  'core',
  'usecases',
  'core'
);

export interface FactsheetSummary {
  id: string;
  title: string;
  domain: string;
  business_owner: string;
  decision_owner: string;
  kpi_owner: string;
  reporting_level: string;
  analytics_stage: string;
  purpose: string;
  business_value: string;
  out_of_scope: string[];
  business_questions: string[];
  kpi_roles: Array<{ kpi_id: string; role: 'Strategic' | 'Influencing' | 'Supporting' | string }>;
  raw_markdown: string;
}

/**
 * Extract YAML frontmatter value for a given key.
 * Returns empty string if not found.
 */
function parseFrontmatterField(frontmatter: string, key: string): string {
  const match = new RegExp(`^${key}:\\s*(.+)$`, 'm').exec(frontmatter);
  return match ? match[1].trim() : '';
}

/**
 * Extract a bold-label bullet value, e.g. "**Domain:** Commercial" → "Commercial"
 */
function extractBulletField(text: string, label: string): string {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = new RegExp(`\\*\\*${escaped}:\\*\\*\\s*(.+?)(?:\\n|$)`).exec(text);
  return match ? match[1].trim() : '';
}

/**
 * Parse the KPI table rows from section 3.
 * Looks for rows matching "| kpi_id | Role |" pattern.
 */
function parseKpiTable(
  text: string
): Array<{ kpi_id: string; role: 'Strategic' | 'Influencing' | 'Supporting' | string }> {
  const results: Array<{ kpi_id: string; role: string }> = [];
  // Match table rows: | cell | cell |
  const rowRegex = /^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|/gm;
  let match: RegExpExecArray | null;
  while ((match = rowRegex.exec(text)) !== null) {
    const col1 = match[1].trim();
    const col2 = match[2].trim();
    // Skip header and separator rows
    if (col1.toLowerCase() === 'kpi id' || col1.startsWith('-') || col1.startsWith('=')) {
      continue;
    }
    // Must look like a KPI ID (contains a dot or is not a plain word header)
    if (col1.includes('.') || /^[a-z]/.test(col1)) {
      results.push({ kpi_id: col1, role: col2 });
    }
  }
  return results;
}

/**
 * Parse bullet list items under a section header.
 * Extracts lines starting with "- " (ignoring continuation indented lines).
 */
function parseBulletList(sectionText: string): string[] {
  const lines = sectionText.split('\n');
  const items: string[] = [];
  let current = '';

  for (const line of lines) {
    if (/^- /.test(line)) {
      if (current) items.push(current.trim());
      current = line.replace(/^- /, '').trim();
    } else if (/^\s{2,}/.test(line) && current) {
      // Continuation of previous bullet
      current += ' ' + line.trim();
    } else if (line.trim() === '' && current) {
      items.push(current.trim());
      current = '';
    }
  }
  if (current) items.push(current.trim());
  return items.filter((s) => s.length > 0);
}

/**
 * Extract content between two section headers.
 * Returns text between the start header and the next ## header (or end of string).
 */
function extractSection(markdown: string, sectionPattern: RegExp): string {
  const start = markdown.search(sectionPattern);
  if (start === -1) return '';

  // Find the end of the header line
  const afterHeader = markdown.indexOf('\n', start);
  if (afterHeader === -1) return '';

  // Find the next ## or ### heading after this one
  const rest = markdown.slice(afterHeader + 1);
  const nextSection = rest.search(/^#{2,3}\s/m);
  return nextSection === -1 ? rest : rest.slice(0, nextSection);
}

/**
 * Parse a Business_Factsheet.md file into a FactsheetSummary.
 */
function parseFactsheet(raw: string): FactsheetSummary | null {
  // --- Frontmatter ---
  const fmMatch = /^---\n([\s\S]*?)\n---/.exec(raw);
  if (!fmMatch) return null;
  const frontmatter = fmMatch[1];
  const id = parseFrontmatterField(frontmatter, 'id');
  const factsheetType = parseFrontmatterField(frontmatter, 'factsheet_type');
  if (!id || factsheetType !== 'business') return null;

  // Body is everything after the closing ---
  const bodyStart = fmMatch.index + fmMatch[0].length;
  const body = raw.slice(bodyStart);

  // --- Title: first # heading ---
  const titleMatch = /^#\s+(.+)$/m.exec(body);
  const title = titleMatch ? titleMatch[1].trim() : id;

  // --- Metadata section (## 0. Metadata) ---
  const metadataSection = extractSection(body, /^## 0\.\s+Metadata/m);
  const domain = extractBulletField(metadataSection, 'Domain');
  const business_owner = extractBulletField(metadataSection, 'Business Owner');
  const kpi_owner = extractBulletField(metadataSection, 'KPI Owner');
  const decision_owner = extractBulletField(metadataSection, 'Decision Owner');
  const reporting_level = extractBulletField(metadataSection, 'Reporting Level');
  const analytics_stage = extractBulletField(metadataSection, 'Analytics Stage');

  // --- Business Summary section (## 1. Business Summary) ---
  const summarySection = extractSection(body, /^## 1\.\s+Business Summary/m);
  const purpose = extractBulletField(summarySection, 'Purpose');
  const business_value = extractBulletField(summarySection, 'Business Value');

  // Out of Scope: extract from the **Out of Scope:** bullet, split by semicolons
  const outOfScopeRaw = extractBulletField(summarySection, 'Out of Scope');
  const out_of_scope = outOfScopeRaw.length > 0
    ? outOfScopeRaw.split(/;\s*/).map((s) => s.trim()).filter((s) => s.length > 0)
    : [];

  // --- Business Questions section (## 2. Core Business Questions) ---
  const questionsSection = extractSection(body, /^## 2\.\s+Core Business Questions/m);
  const business_questions = parseBulletList(questionsSection);

  // --- KPI & Action Code Overview (### 3. KPI & Action Code Overview) ---
  const kpiSection = extractSection(body, /^###\s+3\.\s+KPI\s*&\s*Action Code Overview/m);
  const kpi_roles = parseKpiTable(kpiSection);

  return {
    id,
    title,
    domain,
    business_owner,
    decision_owner,
    kpi_owner,
    reporting_level,
    analytics_stage,
    purpose,
    business_value,
    out_of_scope,
    business_questions,
    kpi_roles,
    raw_markdown: raw,
  };
}

/** Load a single Business Factsheet by use case ID (e.g. "COM-001"). */
export async function loadFactsheet(useCaseId: string): Promise<FactsheetSummary | null> {
  const dirs = await readdir(CORE_USECASES_DIR);
  const match = dirs.find((d) => d.startsWith(useCaseId));
  if (!match) return null;

  const factsheetPath = join(CORE_USECASES_DIR, match, 'Business_Factsheet.md');
  try {
    const raw = await readFile(factsheetPath, 'utf-8');
    return parseFactsheet(raw);
  } catch {
    return null;
  }
}

/** Load all Business Factsheets from core/usecases/core/. */
export async function loadAllFactsheets(): Promise<FactsheetSummary[]> {
  const dirs = await readdir(CORE_USECASES_DIR);

  const results = await Promise.all(
    dirs.sort().map(async (dir) => {
      const factsheetPath = join(CORE_USECASES_DIR, dir, 'Business_Factsheet.md');
      try {
        const raw = await readFile(factsheetPath, 'utf-8');
        return parseFactsheet(raw);
      } catch {
        return null;
      }
    })
  );

  return results.filter((f): f is FactsheetSummary => f !== null);
}

/**
 * Find which factsheet references a given KPI ID and with what role.
 * Returns the first match (a KPI may appear in multiple factsheets).
 */
export async function getFactsheetForKpi(
  kpiId: string
): Promise<{ factsheet: FactsheetSummary; role: string } | null> {
  const all = await loadAllFactsheets();
  for (const factsheet of all) {
    const entry = factsheet.kpi_roles.find((k) => k.kpi_id === kpiId);
    if (entry) {
      return { factsheet, role: entry.role };
    }
  }
  return null;
}
