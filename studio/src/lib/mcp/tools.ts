/**
 * MCP Tool Handlers — Thin wrappers around existing Studio loaders and adapters.
 */

import { loadKpiCatalog, loadKpiMap } from '@/lib/core/catalog-loader';
import { loadAllBrackets, loadBracket } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { validate } from '@/lib/validation/schema-validator';
import { parseYaml } from '@/lib/core/yaml-loader';
import { buildIRPackage } from '@/lib/delivery/ir-builder';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { resolve, join } from 'node:path';
import { generateTmdlMeasures } from '@/lib/delivery/fabric-adapter';
import { generateSqlViews, generateEvidencePage } from '@/lib/delivery/oss-adapter';
import { submitForReview } from '@/lib/governance/approval-workflow';
import { getDb } from '@/lib/db/sqlite';

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
  const schemaPath = resolve(process.cwd(), '..', 'tooling', 'ai', 'schemas', `${schemaName}.schema.json`);
  const schema = JSON.parse(readFileSync(schemaPath, 'utf-8')) as Record<string, unknown>;
  const data = parseYaml(yaml);
  return validate(schema, data);
}

export async function exportFabric(useCaseId: string) {
  const bracket = await loadBracket(useCaseId);
  if (!bracket) return { error: `Bracket ${useCaseId} not found` };

  const kpiMap = await loadKpiMap();
  const ir = buildIRPackage(bracket, kpiMap);
  const outputs = generateTmdlMeasures(ir);
  return { useCaseId, files: outputs };
}

export async function exportOss(useCaseId: string) {
  const bracket = await loadBracket(useCaseId);
  if (!bracket) return { error: `Bracket ${useCaseId} not found` };

  const kpiMap = await loadKpiMap();
  const ir = buildIRPackage(bracket, kpiMap);
  const sqlViews = generateSqlViews(ir);
  const evidencePage = generateEvidencePage(ir);
  return { useCaseId, files: [sqlViews, evidencePage] };
}

// ── Write tools ──────────────────────────────────────────────────────────────

/**
 * Save a bracket YAML draft to the bracket_edits table.
 * The draft is visible in Studio and survives across sessions.
 */
export async function createBracket(bracketId: string, yamlContent: string, projectId = 'default') {
  const schemaPath = resolve(process.cwd(), '..', 'tooling', 'ai', 'schemas', 'usecase_bracket.schema.json');
  const schema = JSON.parse(readFileSync(schemaPath, 'utf-8')) as Record<string, unknown>;
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
  const repoRoot = resolve(process.cwd(), '..');
  const script = join(repoRoot, 'products', 'fabric', 'powerbi', 'tooling', 'validate_bindings.py');
  try {
    const flags = strict ? '--strict' : '';
    const output = execSync(`python3 "${script}" ${flags}`, {
      cwd: repoRoot,
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
  const repoRoot = resolve(process.cwd(), '..');
  const script = join(repoRoot, 'products', 'fabric', 'powerbi', 'tooling', 'scripts', 'execute_dax.py');
  const isGuid = (s: string) => /^[0-9a-f-]{36}$/i.test(s);
  const wsFlag = isGuid(workspaceId) ? `--workspace-id "${workspaceId}"` : `--workspace "${workspaceId}"`;
  const dsFlag = isGuid(datasetId) ? `--dataset-id "${datasetId}"` : `--dataset "${datasetId}"`;
  const cmd = `python3 "${script}" ${wsFlag} ${dsFlag} --query "${daxQuery.replace(/"/g, '\\"')}" --output ${outputFormat}`;
  try {
    const output = execSync(cmd, { cwd: repoRoot, encoding: 'utf-8', timeout: 60_000 });
    return { output, exitCode: 0 };
  } catch (err) {
    const e = err as { stdout?: string; stderr?: string; status?: number };
    return { output: (e.stdout ?? '') + (e.stderr ?? '') || String(err), exitCode: e.status ?? 1 };
  }
}

/**
 * Deploy a PBIP report to a Fabric workspace by running the IR generator
 * and then importing via `fab import`.
 *
 * Steps:
 *   1. Build PBIP from bracket YAML via generate_full_report.py --bracket
 *   2. Import using `fab import <workspace>/<item.SemanticModel> -i <dist_path> -f`
 */
export function deployPbip(
  useCaseId: string,
  workspaceName: string,
  distPath?: string,
): { output: string; exitCode: number } {
  const repoRoot = resolve(process.cwd(), '..');
  const resolvedDist = distPath ?? join(repoRoot, 'products', 'fabric', 'powerbi', 'dist');

  // Step 1: generate from IR
  const generatorScript = join(
    repoRoot, 'products', 'fabric', 'powerbi', 'tooling',
    'page_scaffold_generator', 'generate_full_report.py',
  );
  const bracketPath = join(repoRoot, 'core', 'usecases', 'core');
  const genCmd = `python3 "${generatorScript}" --use-case "${useCaseId}" --output "${resolvedDist}"`;
  try {
    execSync(genCmd, { cwd: repoRoot, encoding: 'utf-8', timeout: 60_000 });
  } catch (err) {
    const e = err as { stdout?: string; status?: number };
    return { output: `Generation failed: ${e.stdout ?? String(err)}`, exitCode: e.status ?? 1 };
  }

  // Step 2: fab import
  // Derive domain from use case prefix (COM→Commercial, FIN→Finance, etc.)
  const domainMap: Record<string, string> = {
    COM: 'Commercial', FIN: 'Finance', OPS: 'Operations',
    SCM: 'SupplyChain', XD: 'Experience',
  };
  const prefix = useCaseId.split('-')[0]?.toUpperCase() ?? 'XD';
  const domain = domainMap[prefix] ?? 'Commercial';
  const modelPath = join(resolvedDist, `${domain}.SemanticModel`);
  const fabCmd = `fab import "${workspaceName}.Workspace/${domain}.SemanticModel" -i "${modelPath}" -f`;
  try {
    const output = execSync(fabCmd, { cwd: repoRoot, encoding: 'utf-8', timeout: 120_000 });
    return { output, exitCode: 0 };
  } catch (err) {
    const e = err as { stdout?: string; stderr?: string; status?: number };
    return { output: (e.stdout ?? '') + (e.stderr ?? '') || String(err), exitCode: e.status ?? 1 };
  }
  void bracketPath; // suppress unused warning
}

/**
 * Trigger a Full dataset refresh via `fab api`.
 * Requires fab CLI authenticated.
 */
export function refreshDataset(
  workspaceId: string,
  datasetId: string,
): { output: string; exitCode: number } {
  const repoRoot = resolve(process.cwd(), '..');
  const cmd = `fab api -A powerbi "groups/${workspaceId}/datasets/${datasetId}/refreshes" -X post -i '{"type":"Full"}'`;
  try {
    const output = execSync(cmd, { cwd: repoRoot, encoding: 'utf-8', timeout: 30_000 });
    return { output: output || '{"status":"accepted"}', exitCode: 0 };
  } catch (err) {
    const e = err as { stdout?: string; stderr?: string; status?: number };
    return { output: (e.stdout ?? '') + (e.stderr ?? '') || String(err), exitCode: e.status ?? 1 };
  }
}

/**
 * Run validate_bindings.py, parse its output, and auto-patch broken visual.json bindings.
 *
 * For each broken binding the patcher:
 *   1. Locates the visual.json file in the PBIP dist folder
 *   2. Reads the current queryState
 *   3. Re-wires the measure reference to the correct _Measures table
 *   4. Writes the patched file back
 *
 * Returns a summary of patched files and any errors.
 */
export function autofixBindings(distPath?: string): {
  patchedFiles: string[];
  errors: string[];
  bindingsOutput: string;
} {
  const repoRoot = resolve(process.cwd(), '..');
  const resolvedDist = distPath ?? join(repoRoot, 'products', 'fabric', 'powerbi', 'dist');
  const patchedFiles: string[] = [];
  const errors: string[] = [];

  // Run validator to get broken bindings
  const { output: bindingsOutput } = validateBindings(true);

  // Parse lines like: ERROR: <path/to/visual.json> — measure '<name>' not found in _Measures
  const errorPattern = /ERROR[^\n]*?([^\s]+\.json)[^\n]*?measure '([^']+)'/g;
  let match: RegExpExecArray | null;
  while ((match = errorPattern.exec(bindingsOutput)) !== null) {
    const [, relPath, measureName] = match;
    const fullPath = relPath.startsWith('/') ? relPath : join(resolvedDist, relPath);
    try {
      const raw = readFileSync(fullPath, 'utf-8');
      const visual = JSON.parse(raw) as Record<string, unknown>;

      // Re-wire: find any Measure reference with the wrong entity and fix to _Measures
      const patched = JSON.stringify(visual, (_, value: unknown) => {
        if (
          typeof value === 'object' && value !== null &&
          'Measure' in (value as Record<string, unknown>)
        ) {
          const m = value as { Measure: { Expression: { SourceRef: { Entity: string } }; Property: string } };
          if (m.Measure.Property === measureName) {
            m.Measure.Expression.SourceRef.Entity = '_Measures';
            return m;
          }
        }
        return value;
      }, 2);

      writeFileSync(fullPath, patched, 'utf-8');
      patchedFiles.push(fullPath);
    } catch (e) {
      errors.push(`Failed to patch ${fullPath}: ${e instanceof Error ? e.message : String(e)}`);
    }
  }

  return { patchedFiles, errors, bindingsOutput };
}

/**
 * Create or update a KPI definition YAML in core/kpi_catalog/.
 * id: the kpi_id (e.g. com.net_sales.amount), yamlContent: full YAML string.
 */
export function createKpi(kpiId: string, yamlContent: string): { kpiId: string; path: string } {
  const repoRoot = resolve(process.cwd(), '..');
  const outDir = join(repoRoot, 'core', 'kpi_catalog', 'kpis');
  mkdirSync(outDir, { recursive: true });
  const fileName = `${kpiId.replace(/\./g, '_')}.yaml`;
  const filePath = join(outDir, fileName);
  writeFileSync(filePath, yamlContent, 'utf-8');
  return { kpiId, path: `core/kpi_catalog/kpis/${fileName}` };
}

/**
 * Update an action code YAML in core/action_codes/.
 * actionId: the action code id (e.g. C-M2.1), yamlContent: full YAML string.
 */
export function updateAction(actionId: string, yamlContent: string): { actionId: string; path: string } {
  const repoRoot = resolve(process.cwd(), '..');
  // Infer domain prefix from actionId
  const prefix = actionId.split('-')[0]?.toLowerCase() ?? 'x';
  const domainMap: Record<string, string> = { c: 'commercial', f: 'finance', o: 'operations', s: 'supply_chain', x: 'service' };
  const domain = domainMap[prefix] ?? 'misc';
  const outDir = join(repoRoot, 'core', 'action_codes', domain);
  mkdirSync(outDir, { recursive: true });
  const fileName = `${actionId.replace(/\./g, '_')}.yaml`;
  const filePath = join(outDir, fileName);
  writeFileSync(filePath, yamlContent, 'utf-8');
  return { actionId, path: `core/action_codes/${domain}/${fileName}` };
}
