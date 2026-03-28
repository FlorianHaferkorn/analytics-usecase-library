/**
 * Audit Repository — Event sourcing for change tracking.
 *
 * Every mutation (bracket edit, project update, theme save) logs an event
 * with before/after diff for accountability and rollback support.
 */

import { getDb } from './sqlite';

export interface AuditEvent {
  id: string;
  project_id: string;
  actor: string;
  entity_type: 'bracket' | 'project' | 'theme' | 'discovery';
  entity_id: string;
  action: 'create' | 'update' | 'delete';
  diff_json: string;
  created_at: string;
}

export interface AuditDiff {
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
}

function generateId(): string {
  return `aud-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

export function logAuditEvent(
  entityType: AuditEvent['entity_type'],
  entityId: string,
  action: AuditEvent['action'],
  diff: AuditDiff,
  projectId = 'default',
  actor = 'system',
): AuditEvent {
  const db = getDb();
  const id = generateId();
  const diffJson = JSON.stringify(diff);

  db.prepare(`
    INSERT INTO audit_events (id, project_id, actor, entity_type, entity_id, action, diff_json)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(id, projectId, actor, entityType, entityId, action, diffJson);

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
  entityType: AuditEvent['entity_type'],
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
