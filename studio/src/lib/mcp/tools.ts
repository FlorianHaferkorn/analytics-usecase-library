/**
 * MCP Tool Handlers — Thin wrappers around existing Studio loaders and adapters.
 */

import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllBrackets, loadBracket } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { validate } from '@/lib/validation/schema-validator';
import { parseYaml } from '@/lib/core/yaml-loader';
import { runGenerate, type GenerateResult } from '@/lib/bridge/superversion-bridge';
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, relative, resolve, join } from 'node:path';
import { submitForReview } from '@/lib/governance/approval-workflow';
import { getDb } from '@/lib/db/sqlite';

const REPO_ROOT = resolve(process.cwd(), '..');
const PYTHON = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
const PYTHON_PREFIX = process.env.SUPERVERSION_PYTHON || process.platform !== 'win32' ? [] : ['-3'];
const KPI_ID = /^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$/;
const ACTION_ID = /^[A-Z]-[A-Z]\d+\.\d+$/;

function schemaPath(name: 'usecase_bracket' | 'kpi_definition' | 'action_code'): string {
  return join(REPO_ROOT, 'tooling', 'generator', 'schemas', `${name}.schema.json`);
}

function generatedFiles(result: GenerateResult) {
  if (!result.available || !result.ok) {
    return { error: result.error ?? `${result.target ?? 'core'} gate is not green`, gate: result.gate };
  }
  const files = result.artifacts
    .filter((artifact) => typeof artifact.content === 'string')
    .map((artifact) => ({ filename: artifact.path, content: artifact.content! }));
  if (files.length !== result.artifacts.length) {
    return { error: `${result.target}: artifact content missing from governed core`, gate: result.gate };
  }
  return { target: result.target, targetStatus: result.targetStatus, gate: result.gate, files };
}

export async function listKpis() {
  const kpis = await loadKpiCatalog();
  return kpis.map((k) => ({
    kpi_id: k.kpi_id,
    name: k.kpi_key,
    type: k.kpi_type,
    role: k.kpi_role,
    domains: k.domain_tag,
    purpose: k.business?.purpose,
  }));
}

export async function listBrackets() {
  const brackets = await loadAllBrackets();
  return brackets.map((b) => ({
    id: b.id,
    title: b.title,
    domain: b.domain,
    strategicKpiId: b.orchestration.strategic_kpi_id,
    driverCount: b.orchestration.influencing_kpi_ids.length,
    actionCount: b.orchestration.action_code_ids.length,
  }));
}

export async function listActions() {
  const actions = await loadAllActionCodes();
  return actions.map((a) => ({
    id: a.id,
    name: a.name,
    status: a.status,
    domain: a.owner_domain,
    triggerKpis: a.kpis.trigger_kpis,
  }));
}

export async function getBracket(id: string) {
  const bracket = await loadBracket(id);
  if (!bracket) return { error: `Bracket ${id} not found` };
  return bracket;
}

export async function validateYaml(yaml: string, schemaName: string) {
  const supported = new Set(['usecase_bracket', 'kpi_definition', 'action_code']);
  if (!supported.has(schemaName)) return { valid: false, errors: [`Unsupported schema: ${schemaName}`] };
  const schema = JSON.parse(readFileSync(schemaPath(schemaName as 'usecase_bracket' | 'kpi_definition' | 'action_code'), 'utf-8')) as Record<string, unknown>;
  const data = parseYaml(yaml);
  return validate(schema, data);
}

export async function exportFabric(useCaseId: string) {
  const [tmdl, pbir] = await Promise.all([
    runGenerate(useCaseId, 'tmdl', true),
    runGenerate(useCaseId, 'pbir', true),
  ]);
  return { useCaseId, outputs: { tmdl: generatedFiles(tmdl), pbir: generatedFiles(pbir) } };
}

export async function exportOss(useCaseId: string) {
  const osi = await runGenerate(useCaseId, 'osi', true);
  return { useCaseId, output: generatedFiles(osi) };
}

// ── Write tools ──────────────────────────────────────────────────────────────

/**
 * Save a bracket YAML draft to the bracket_edits table.
 * The draft is visible in Studio and survives across sessions.
 */
export async function createBracket(bracketId: string, yamlContent: string, projectId = 'default') {
  const schema = JSON.parse(readFileSync(schemaPath('usecase_bracket'), 'utf-8')) as Record<string, unknown>;
  const data = parseYaml(yamlContent);
  const validation = validate(schema, data);
  if (!validation.valid) return { error: 'Validation failed', details: validation.errors };

  const db = getDb();
  db.prepare(
    `INSERT OR REPLACE INTO bracket_edits (bracket_id, project_id, yaml_content, updated_at)
     VALUES (?, ?, ?, datetime('now'))`,
  ).run(bracketId, projectId, yamlContent);

  return { bracketId, projectId, status: 'saved' };
}

/**
 * Submit a bracket draft for governance review.
 * The bracket must already exist in bracket_edits or as a Core YAML file.
 */
export async function publishDraft(bracketId: string, actorEmail: string, justification = '', projectId = 'default') {
  const lifecycle = submitForReview(bracketId, actorEmail, justification, projectId);
  return { bracketId, lifecycle };
}

/**
 * Run the export generator for a use case.
 * connector: 'fabric' | 'oss'
 */
export async function runGenerator(useCaseId: string, connector: 'fabric' | 'oss') {
  if (connector === 'fabric') return exportFabric(useCaseId);
  if (connector === 'oss') return exportOss(useCaseId);
  return { error: `Unknown connector: ${connector}` };
}

/**
 * Run the Python validate_bindings.py script and return its output.
 */
export function validateBindings(strict = false): { output: string; exitCode: number } {
  const script = join(REPO_ROOT, 'products', 'fabric', 'powerbi', 'tooling', 'validate_bindings.py');
  try {
    const output = execFileSync(PYTHON, [...PYTHON_PREFIX, script, ...(strict ? ['--strict'] : [])], {
      cwd: REPO_ROOT,
      encoding: 'utf-8',
      timeout: 30_000,
    });
    return { output, exitCode: 0 };
  } catch (err) {
    const e = err as { stdout?: string; status?: number };
    return { output: e.stdout ?? String(err), exitCode: e.status ?? 1 };
  }
}

/**
 * Execute a DAX query against a Fabric semantic model via execute_dax.py.
 * Requires fab CLI authenticated and az CLI logged in.
 * Accepts either workspace/dataset GUIDs or friendly names.
 */
export function executeDax(
  workspaceId: string,
  datasetId: string,
  daxQuery: string,
  outputFormat: 'json' | 'csv' | 'table' = 'json',
): { output: string; exitCode: number } {
  const script = join(REPO_ROOT, 'products', 'fabric', 'powerbi', 'tooling', 'scripts', 'execute_dax.py');
  const isGuid = (s: string) => /^[0-9a-f-]{36}$/i.test(s);
  const workspaceArgs = isGuid(workspaceId) ? ['--workspace-id', workspaceId] : ['--workspace', workspaceId];
  const datasetArgs = isGuid(datasetId) ? ['--dataset-id', datasetId] : ['--dataset', datasetId];
  try {
    const output = execFileSync(PYTHON, [
      ...PYTHON_PREFIX,
      script,
      ...workspaceArgs,
      ...datasetArgs,
      '--query',
      daxQuery,
      '--output',
      outputFormat,
    ], { cwd: REPO_ROOT, encoding: 'utf-8', timeout: 60_000 });
    return { output, exitCode: 0 };
  } catch (err) {
    const e = err as { stdout?: string; stderr?: string; status?: number };
    return { output: (e.stdout ?? '') + (e.stderr ?? '') || String(err), exitCode: e.status ?? 1 };
  }
}

/**
 * Package a PBIP report via the governed core and import it with the official
 * Fabric CLI only when every required target is marked live.
 */
export async function deployPbip(
  useCaseId: string,
  workspaceName: string,
  distPath?: string,
): Promise<{ output: string; exitCode: number }> {
  if (!/^[A-Z]{2,3}-(?:EXT-|IND-[A-Z])?\d{3}$/.test(useCaseId)) {
    return { output: `Invalid use case ID: ${useCaseId}`, exitCode: 2 };
  }
  if (!workspaceName.trim() || workspaceName.length > 128) {
    return { output: 'workspaceName must contain 1–128 characters', exitCode: 2 };
  }

  const resolvedDist = resolve(distPath ?? join(
    REPO_ROOT, 'products', 'fabric', 'powerbi', 'dist', 'mcp', useCaseId,
  ));
  const distRelative = relative(REPO_ROOT, resolvedDist);
  if (!distRelative || distRelative.startsWith('..')) {
    return { output: 'distPath must resolve to a dedicated directory inside the repository', exitCode: 2 };
  }

  const generated = await Promise.all([
    runGenerate(useCaseId, 'tmdl', true),
    runGenerate(useCaseId, 'pbir', true),
  ]);
  const failed = generated.find((result) => !result.available || !result.ok);
  if (failed) {
    return { output: failed.error ?? `${failed.target ?? 'core'} gate is not green`, exitCode: 1 };
  }

  for (const result of generated) {
    for (const artifact of result.artifacts) {
      if (typeof artifact.content !== 'string') {
        return { output: `${result.target}: artifact content missing from governed core`, exitCode: 1 };
      }
      const outputPath = resolve(resolvedDist, artifact.path);
      const outputRelative = relative(resolvedDist, outputPath);
      if (!outputRelative || outputRelative.startsWith('..')) {
        return { output: `Unsafe artifact path rejected: ${artifact.path}`, exitCode: 2 };
      }
      mkdirSync(dirname(outputPath), { recursive: true });
      writeFileSync(outputPath, artifact.content, 'utf-8');
    }
  }

  const nonLive = generated.filter((result) => result.targetStatus !== 'live');
  if (nonLive.length > 0) {
    return {
      output: `Package created at ${resolvedDist}; Fabric import blocked because ${nonLive.map((result) => `${result.target} is ${result.targetStatus ?? 'unclassified'}`).join(', ')}.`,
      exitCode: 2,
    };
  }

  const itemRoots = [...new Set(generated.flatMap((result) => result.artifacts.map((artifact) => artifact.path.split('/')[0])))];
  try {
    const output = itemRoots.map((itemRoot) => execFileSync('fab', [
      'import', `${workspaceName}.Workspace/${itemRoot}`, '-i', join(resolvedDist, itemRoot), '-f',
    ], { cwd: REPO_ROOT, encoding: 'utf-8', timeout: 120_000 })).join('\n');
    return { output: output || 'Fabric import completed', exitCode: 0 };
  } catch (err) {
    const e = err as { stdout?: string; stderr?: string; status?: number };
    return { output: (e.stdout ?? '') + (e.stderr ?? '') || String(err), exitCode: e.status ?? 1 };
  }
}

/**
 * Trigger a Full dataset refresh via `fab api`.
 * Requires fab CLI authenticated.
 */
export function refreshDataset(
  workspaceId: string,
  datasetId: string,
): { output: string; exitCode: number } {
  if (!/^[0-9a-f-]{36}$/i.test(workspaceId) || !/^[0-9a-f-]{36}$/i.test(datasetId)) {
    return { output: 'workspaceId and datasetId must be GUIDs', exitCode: 2 };
  }
  try {
    const output = execFileSync('fab', [
      'api', '-A', 'powerbi',
      `groups/${workspaceId}/datasets/${datasetId}/refreshes`,
      '-X', 'post', '-i', '{"type":"Full"}',
    ], { cwd: REPO_ROOT, encoding: 'utf-8', timeout: 30_000 });
    return { output: output || '{"status":"accepted"}', exitCode: 0 };
  } catch (err) {
    const e = err as { stdout?: string; stderr?: string; status?: number };
    return { output: (e.stdout ?? '') + (e.stderr ?? '') || String(err), exitCode: e.status ?? 1 };
  }
}

/**
 * Backward-compatible audit tool. Generated PBIR is never patched in place:
 * binding defects must be corrected in the bracket, KPI catalog, or adapter.
 */
export function autofixBindings(distPath?: string): {
  patchedFiles: string[];
  errors: string[];
  bindingsOutput: string;
} {
  const { output: bindingsOutput } = validateBindings(true);
  return {
    patchedFiles: [],
    errors: [
      `Automatic PBIR mutation is disabled${distPath ? ` for ${distPath}` : ''}; fix the governed source or target adapter and regenerate.`,
    ],
    bindingsOutput,
  };
}

/**
 * Create or update a KPI definition YAML in core/kpi_catalog/.
 * id: the kpi_id (e.g. com.net_sales.amount), yamlContent: full YAML string.
 */
export function createKpi(kpiId: string, yamlContent: string): { kpiId: string; path?: string; error?: string; details?: unknown } {
  if (!KPI_ID.test(kpiId)) return { kpiId, error: 'Invalid KPI ID' };
  const parsed = parseYaml(yamlContent) as Record<string, unknown>;
  if (parsed.kpi_id !== kpiId) return { kpiId, error: `YAML kpi_id must equal ${kpiId}` };
  const schema = JSON.parse(readFileSync(schemaPath('kpi_definition'), 'utf-8')) as Record<string, unknown>;
  const validation = validate(schema, parsed);
  if (!validation.valid) return { kpiId, error: 'Validation failed', details: validation.errors };
  const outDir = join(REPO_ROOT, 'core', 'kpi_catalog', 'kpis');
  const fileName = `${kpiId}.yaml`;
  const filePath = join(outDir, fileName);
  writeFileSync(filePath, yamlContent, 'utf-8');
  return { kpiId, path: `core/kpi_catalog/kpis/${fileName}` };
}

/**
 * Update an action code YAML in core/action_codes/.
 * actionId: the action code id (e.g. C-M2.1), yamlContent: full YAML string.
 */
export function updateAction(actionId: string, yamlContent: string): { actionId: string; path?: string; error?: string; details?: unknown } {
  if (!ACTION_ID.test(actionId)) return { actionId, error: 'Invalid action code ID' };
  const parsed = parseYaml(yamlContent) as Record<string, unknown>;
  if (parsed.id !== actionId) return { actionId, error: `YAML id must equal ${actionId}` };
  const schema = JSON.parse(readFileSync(schemaPath('action_code'), 'utf-8')) as Record<string, unknown>;
  const validation = validate(schema, parsed);
  if (!validation.valid) return { actionId, error: 'Validation failed', details: validation.errors };

  const actionRoot = join(REPO_ROOT, 'core', 'action_codes');
  const fileName = `${actionId}.yaml`;
  const findExisting = (directory: string): string | null => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const candidate = join(directory, entry.name);
      if (entry.isDirectory()) {
        const nested = findExisting(candidate);
        if (nested) return nested;
      } else if (entry.isFile() && entry.name === fileName) {
        return candidate;
      }
    }
    return null;
  };

  const existing = findExisting(actionRoot);
  const prefixDomains: Record<string, string> = {
    C: 'Commercial', F: 'Finance', O: 'Operations', S: 'SupplyChain',
  };
  let domain = prefixDomains[actionId[0]];
  if (!domain && actionId.startsWith('X-')) {
    const owner = String(parsed.owner_domain ?? '').toLowerCase();
    domain = /people|workforce|human resources|\bhr\b/.test(owner)
      ? 'People'
      : /enterprise|strategy|executive|pmo/.test(owner)
        ? 'Enterprise'
        : /service|customer|\bcx\b/.test(owner)
          ? 'Service'
          : '';
  }
  if (!existing && !domain) {
    return { actionId, error: 'Cannot derive the canonical action-code domain from ID and owner_domain' };
  }
  const filePath = existing ?? join(actionRoot, domain!, fileName);
  mkdirSync(dirname(filePath), { recursive: true });
  writeFileSync(filePath, yamlContent, 'utf-8');
  return { actionId, path: relative(REPO_ROOT, filePath).replace(/\\/g, '/') };
}
