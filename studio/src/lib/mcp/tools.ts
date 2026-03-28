/**
 * MCP Tool Handlers — Thin wrappers around existing Studio loaders and adapters.
 */

import { loadKpiCatalog, loadKpiMap } from '@/lib/core/catalog-loader';
import { loadAllBrackets, loadBracket } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { validate } from '@/lib/validation/schema-validator';
import { parseYaml } from '@/lib/core/yaml-loader';
import { buildIRPackage } from '@/lib/delivery/ir-builder';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { generateTmdlMeasures } from '@/lib/delivery/fabric-adapter';
import { generateSqlViews, generateEvidencePage } from '@/lib/delivery/oss-adapter';

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
