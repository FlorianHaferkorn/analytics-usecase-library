/**
 * ai-config-repo — governed L1/L2 AI-config override layers (I-6.6 V5, ADR-0008 §1/§9).
 *
 * Customers tighten the universal L0 via L1 (tenant) and L2 (domain) layers. Each layer
 * is validated against `ai_config.schema.json` on save, then flows through the approval
 * lifecycle (draft → review → approved) with the two-person rule + audit, reusing the
 * same pattern as bracket governance. Only **approved** layers are served to the resolver
 * (`getApprovedLayers`), so a pending draft never affects live routing.
 */

import { randomUUID, createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { getDb } from './sqlite';
import { logAuditEvent } from './audit-repo';
import { validate } from '@/lib/validation/schema-validator';
import type { AiConfigLayer } from '@/lib/ai/config/resolve';
import { VALID_TRANSITIONS, type LayerStatus, type LayerAction } from '@/lib/ai/config/governance-types';

export type { LayerStatus } from '@/lib/ai/config/governance-types';

export interface AiConfigLayerRow {
  id: string;
  project_id: string;
  layer: string;
  domain_id: string;
  config_json: string;
  schema_version: string;
  status: LayerStatus;
  submitted_by: string | null;
  approved_by: string | null;
  justification: string | null;
  effective_hash: string | null;
  created_at: string;
  updated_at: string;
}

const SCHEMA_PATH = join(process.cwd(), '..', 'tooling', 'generator', 'schemas', 'ai_config.schema.json');
let _schema: Record<string, unknown> | null = null;
function aiConfigSchema(): Record<string, unknown> {
  if (!_schema) _schema = JSON.parse(readFileSync(SCHEMA_PATH, 'utf-8')) as Record<string, unknown>;
  return _schema as Record<string, unknown>;
}

export class AiConfigGovernanceError extends Error {}

/** Validate a layer config against the schema; throws AiConfigGovernanceError on failure. */
export function validateLayer(config: AiConfigLayer): void {
  const result = validate(aiConfigSchema(), config);
  if (!result.valid) {
    throw new AiConfigGovernanceError(
      `ai_config layer invalid: ${result.errors.map((e) => `${e.path} ${e.message}`).join('; ')}`,
    );
  }
}

/**
 * Create or replace the (project, layer, domain) override as a fresh DRAFT. Validates
 * first. Resets approval state — an edited layer must be re-approved before it serves.
 */
export function upsertConfigLayer(input: {
  projectId?: string;
  layer: 'L1' | 'L2';
  domainId?: string;
  config: AiConfigLayer;
}): AiConfigLayerRow {
  validateLayer(input.config);
  if (input.layer === 'L2' && !input.domainId) {
    throw new AiConfigGovernanceError('L2 layer requires a domainId');
  }
  const db = getDb();
  const projectId = input.projectId ?? 'default';
  const domainId = input.layer === 'L2' ? input.domainId! : '';
  const id = randomUUID();
  db.prepare(`
    INSERT INTO ai_config_layers (id, project_id, layer, domain_id, config_json, schema_version, status)
    VALUES (@id, @project_id, @layer, @domain_id, @config_json, @schema_version, 'draft')
    ON CONFLICT (project_id, layer, domain_id) DO UPDATE SET
      config_json = excluded.config_json, schema_version = excluded.schema_version,
      status = 'draft', submitted_by = NULL, approved_by = NULL, justification = NULL,
      effective_hash = NULL, updated_at = datetime('now')
  `).run({
    id, project_id: projectId, layer: input.layer, domain_id: domainId,
    config_json: JSON.stringify(input.config), schema_version: input.config.schema_version,
  });
  return getConfigLayer(projectId, input.layer, domainId)!;
}

export function getConfigLayer(projectId: string, layer: 'L1' | 'L2', domainId = ''): AiConfigLayerRow | null {
  return (getDb()
    .prepare('SELECT * FROM ai_config_layers WHERE project_id = ? AND layer = ? AND domain_id = ?')
    .get(projectId, layer, domainId) as AiConfigLayerRow | undefined) ?? null;
}

/** Drive the approval lifecycle. Two-person rule on approve; every step audited. */
export function transitionConfigLayer(
  projectId: string, layer: 'L1' | 'L2', domainId: string, action: LayerAction, actor: string, justification: string,
): AiConfigLayerRow {
  const row = getConfigLayer(projectId, layer, domainId);
  if (!row) throw new AiConfigGovernanceError(`no ${layer} layer for ${projectId}/${domainId || '(tenant)'}`);
  const allowed = VALID_TRANSITIONS[row.status];
  if (!allowed.includes(action)) {
    throw new AiConfigGovernanceError(`cannot ${action} from ${row.status} (allowed: ${allowed.join(', ') || 'none'})`);
  }
  if (action === 'approve' && row.submitted_by === actor) {
    throw new AiConfigGovernanceError('cannot approve your own config change (two-person rule)');
  }
  const newStatus: LayerStatus =
    action === 'submit' ? 'review' : action === 'approve' ? 'approved' : action === 'reject' ? 'rejected' : 'draft';
  const hash = action === 'approve' ? createHash('sha256').update(row.config_json).digest('hex') : row.effective_hash;
  getDb().prepare(`
    UPDATE ai_config_layers
    SET status = ?, submitted_by = COALESCE(?, submitted_by), approved_by = ?,
        justification = ?, effective_hash = ?, updated_at = datetime('now')
    WHERE id = ?
  `).run(newStatus, action === 'submit' ? actor : null, action === 'approve' ? actor : null,
        justification, hash, row.id);
  logAuditEvent('governance', `ai-config:${layer}:${domainId || 'tenant'}`, action, {
    before: { status: row.status },
    after: { status: newStatus, schema_version: row.schema_version, effective_hash: hash },
    justification,
  }, projectId, actor);
  return getConfigLayer(projectId, layer, domainId)!;
}

/** The approved L1 (+ matching L2 for a domain), parsed — what the resolver consumes. */
export function getApprovedLayers(projectId = 'default', domainId?: string): { l1?: AiConfigLayer; l2?: AiConfigLayer } {
  const out: { l1?: AiConfigLayer; l2?: AiConfigLayer } = {};
  const l1 = getConfigLayer(projectId, 'L1', '');
  if (l1 && l1.status === 'approved') out.l1 = JSON.parse(l1.config_json) as AiConfigLayer;
  if (domainId) {
    const l2 = getConfigLayer(projectId, 'L2', domainId);
    if (l2 && l2.status === 'approved') out.l2 = JSON.parse(l2.config_json) as AiConfigLayer;
  }
  return out;
}
