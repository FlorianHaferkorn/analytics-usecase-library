/**
 * Audit Repository — Event sourcing for change tracking.
 *
 * Every mutation (bracket edit, project update, theme save, rule change,
 * plugin action, export) logs an event with before/after diff.
 */

import { getDb } from './sqlite';
import { chainEvent } from './audit-chain';

export type AuditEntityType =
  | 'bracket'
  | 'factsheet'
  | 'kpi'
  | 'project'
  | 'theme'
  | 'discovery'
  | 'notification_rule'
  | 'plugin'
  | 'export'
  | 'governance'
  | 'refinement'
  | 'org'
  | 'org_member'
  | 'project_member'
  | 'ai_egress'
  | 'ai_policy_review'
  | 'audit_retention';

export type AuditAction = 'create' | 'update' | 'delete' | 'export' | 'approve' | 'reject' | 'submit' | 'deprecate' | 'reopen' | 'add_member' | 'remove_member' | 'update_business_role' | 'break_glass_override' | 'break_glass_revert' | 'allow' | 'block' | 'expire';

export interface AuditEvent {
  id: string;
  project_id: string;
  actor: string;
  entity_type: AuditEntityType;
  entity_id: string;
  action: AuditAction;
  diff_json: string;
  created_at: string;
}

export interface AuditDiff {
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  justification?: string;
}

function generateId(): string {
  return `aud-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

/**
 * Log an audit event. Actor is required — pass user email or 'system' for cron/background jobs.
 */
export function logAuditEvent(
  entityType: AuditEntityType,
  entityId: string,
  action: AuditAction,
  diff: AuditDiff,
  projectId: string,
  actor: string,
): AuditEvent {
  const db = getDb();
  const id = generateId();
  const diffJson = JSON.stringify(diff);

  db.prepare(`
    INSERT INTO audit_events (id, project_id, actor, entity_type, entity_id, action, diff_json)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(id, projectId, actor, entityType, entityId, action, diffJson);

  // Chain the event for tamper detection
  chainEvent(id, projectId);

  return db.prepare('SELECT * FROM audit_events WHERE id = ?').get(id) as AuditEvent;
}

export function getAuditEvents(
  projectId = 'default',
  limit = 50,
  offset = 0,
): AuditEvent[] {
  const db = getDb();
  return db.prepare(
    'SELECT * FROM audit_events WHERE project_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
  ).all(projectId, limit, offset) as AuditEvent[];
}

export function getAuditEventsByEntity(
  entityType: AuditEntityType,
  entityId: string,
  limit = 50,
): AuditEvent[] {
  const db = getDb();
  return db.prepare(
    'SELECT * FROM audit_events WHERE entity_type = ? AND entity_id = ? ORDER BY created_at DESC LIMIT ?',
  ).all(entityType, entityId, limit) as AuditEvent[];
}

export function getAuditEventCount(projectId = 'default'): number {
  const db = getDb();
  const row = db.prepare(
    'SELECT COUNT(*) as count FROM audit_events WHERE project_id = ?',
  ).get(projectId) as { count: number };
  return row.count;
}
