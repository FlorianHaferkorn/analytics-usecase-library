/**
 * Deterministic Factsheet ↔ Bracket reconcile (Cascading AI fallback).
 * See REBUILD_DECISIONS §D7 — never auto-applies; returns a proposed patch only.
 */

import { parseYaml } from '@/lib/core/yaml-loader';
import { KPI_ID } from '@/lib/simulation/formula-parser';

export type ReconcileEditedSource = 'factsheet' | 'bracket';

export interface ReconcileRequest {
  editedSource: ReconcileEditedSource;
  prose: string;
  bracketYaml: string;
  changeHint?: string;
}

export interface ReconcileProposal {
  target: ReconcileEditedSource;
  summary: string;
  patch: string;
  hints: string[];
}

interface BracketOrchestration {
  strategic_kpi_id?: string;
  influencing_kpi_ids?: string[];
  supporting_kpi_ids?: string[];
  action_code_ids?: string[];
}

function parseBracketOrchestration(yaml: string): BracketOrchestration | null {
  try {
    const doc = parseYaml<Record<string, unknown>>(yaml);
    const orch = doc?.orchestration as BracketOrchestration | undefined;
    return orch ?? null;
  } catch {
    return null;
  }
}

/** Parse KPI rows from factsheet section 3 table (| kpi_id | Role |). */
export function extractFactsheetKpiRoles(markdown: string): Array<{ kpi_id: string; role: string }> {
  const section = markdown.match(
    /###\s+3\.\s+KPI\s*&\s*Action Code Overview([\s\S]*?)(?=\n## |$)/,
  );
  if (!section) return [];

  const rows: Array<{ kpi_id: string; role: string }> = [];
  const rowRe = /^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|/gm;
  let m: RegExpExecArray | null;
  const body = section[1];
  while ((m = rowRe.exec(body)) !== null) {
    const col1 = m[1].trim();
    const col2 = m[2].trim();
    if (col1.toLowerCase() === 'kpi id' || col1.startsWith('-')) continue;
    if (KPI_ID.test(col1)) rows.push({ kpi_id: col1, role: col2 });
  }
  return rows;
}

function extractActionCodesLine(markdown: string): string[] {
  const match = /\*\*Action Codes:\*\*\s*([^\n]+)/.exec(markdown);
  if (!match) return [];
  return match[1]
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

function listChanged(next: string[], current: string[] | undefined): boolean {
  const prev = current ?? [];
  if (next.length !== prev.length) return true;
  return next.some((value, index) => value !== prev[index]);
}

function upsertYamlList(yaml: string, key: string, values: string[]): string {
  const lines = yaml.split('\n');
  const keyRe = new RegExp(`^(\\s*)${key}:\\s*$`);
  let start = -1;
  let indent = '  ';
  for (let i = 0; i < lines.length; i++) {
    const m = keyRe.exec(lines[i]);
    if (m) {
      start = i;
      indent = m[1] + '  ';
      break;
    }
  }
  if (start === -1) return yaml;

  let end = start + 1;
  while (end < lines.length && (lines[end].startsWith(indent + '-') || lines[end].trim() === '')) {
    if (lines[end].trim().startsWith('-')) end++;
    else if (lines[end].trim() === '') end++;
    else break;
  }

  const newLines = values.map((v) => `${indent}- ${v}`);
  return [...lines.slice(0, start + 1), ...newLines, ...lines.slice(end)].join('\n');
}

function rebuildFactsheetSection3(
  markdown: string,
  orch: BracketOrchestration,
): string {
  const strategic = orch.strategic_kpi_id ?? '';
  const influencing = orch.influencing_kpi_ids ?? [];
  const supporting = orch.supporting_kpi_ids ?? [];
  const actions = orch.action_code_ids ?? [];

  const tableRows = [
    '| KPI ID | Role |',
    '|--------|------|',
    ...(strategic ? [`| ${strategic} | Strategic |`] : []),
    ...influencing.map((id) => `| ${id} | Influencing |`),
    ...supporting.map((id) => `| ${id} | Supporting |`),
  ];

  const actionLine = actions.length
    ? `**Action Codes:** ${actions.join(', ')}`
    : '**Action Codes:** _(none)_';

  const block = [
    '### 3. KPI & Action Code Overview',
    '',
    ...tableRows,
    '',
    actionLine,
    '',
    '> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).',
    '',
  ].join('\n');

  if (/###\s+3\.\s+KPI\s*&\s*Action Code Overview/.test(markdown)) {
    return markdown.replace(
      /###\s+3\.\s+KPI\s*&\s*Action Code Overview[\s\S]*?(?=\n## |$)/,
      `${block}---\n\n`,
    );
  }

  const insertBefore = markdown.search(/^##\s+4\./m);
  if (insertBefore === -1) return `${markdown}\n\n${block}`;
  return `${markdown.slice(0, insertBefore)}${block}\n${markdown.slice(insertBefore)}`;
}

/** Rule-based reconcile when AI is unavailable. */
export function reconcileDeterministic(req: ReconcileRequest): ReconcileProposal | null {
  const orch = parseBracketOrchestration(req.bracketYaml);
  if (!orch) return null;

  if (req.editedSource === 'factsheet') {
    const roles = extractFactsheetKpiRoles(req.prose);
    const strategic = roles.find((r) => /strategic/i.test(r.role))?.kpi_id;
    const influencing = roles
      .filter((r) => /influencing/i.test(r.role))
      .map((r) => r.kpi_id);
    const supporting = roles
      .filter((r) => /supporting/i.test(r.role))
      .map((r) => r.kpi_id);
    const actionCodes = extractActionCodesLine(req.prose);

    let yaml = req.bracketYaml;
    const hints: string[] = [];

    if (strategic && strategic !== orch.strategic_kpi_id) {
      yaml = yaml.replace(
        /^(\s*strategic_kpi_id:\s*).+$/m,
        `$1${strategic}`,
      );
      hints.push(`Set strategic_kpi_id → ${strategic}`);
    }
    if (listChanged(influencing, orch.influencing_kpi_ids)) {
      yaml = upsertYamlList(yaml, 'influencing_kpi_ids', influencing);
      hints.push(
        influencing.length
          ? `Sync influencing_kpi_ids (${influencing.length} items)`
          : 'Clear influencing_kpi_ids (removed from factsheet)',
      );
    }
    if (listChanged(supporting, orch.supporting_kpi_ids)) {
      yaml = upsertYamlList(yaml, 'supporting_kpi_ids', supporting);
      hints.push(
        supporting.length
          ? `Sync supporting_kpi_ids (${supporting.length} items)`
          : 'Clear supporting_kpi_ids (removed from factsheet)',
      );
    }
    if (listChanged(actionCodes, orch.action_code_ids)) {
      yaml = upsertYamlList(yaml, 'action_code_ids', actionCodes);
      hints.push(
        actionCodes.length
          ? `Sync action_code_ids: ${actionCodes.join(', ')}`
          : 'Clear action_code_ids (removed from factsheet)',
      );
    }

    if (yaml === req.bracketYaml) return null;

    return {
      target: 'bracket',
      summary: 'Factsheet KPI table differs from bracket orchestration.',
      patch: yaml,
      hints,
    };
  }

  const proposed = rebuildFactsheetSection3(req.prose, orch);
  if (proposed === req.prose) return null;

  return {
    target: 'factsheet',
    summary: 'Bracket orchestration differs from factsheet §3 KPI table.',
    patch: proposed,
    hints: [
      `Strategic: ${orch.strategic_kpi_id ?? '—'}`,
      `${(orch.influencing_kpi_ids ?? []).length} influencing KPIs`,
      `${(orch.action_code_ids ?? []).length} action codes`,
    ],
  };
}
