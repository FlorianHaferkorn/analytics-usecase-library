/**
 * Audit Helpers — convenience functions for audit logging with actor capture.
 *
 * Combines session extraction + audit logging into a single call for Route Handlers.
 */

import { getSessionUser } from '@/lib/auth/session';
import { logAuditEvent } from './audit-repo';
import type { AuditEntityType, AuditAction, AuditDiff } from './audit-repo';

/**
 * Log an audit event with the current session user as actor.
 * Falls back to 'system' for background/cron jobs where no session exists.
 */
export async function auditWithActor(
  entityType: AuditEntityType,
  entityId: string,
  action: AuditAction,
  diff: AuditDiff,
  projectId = 'default',
) {
  const user = await getSessionUser();
  const actor = user?.email ?? 'system';
  return logAuditEvent(entityType, entityId, action, diff, projectId, actor);
}

/**
 * Log an audit event with an explicit actor string.
 * Use when actor is already known (e.g., from a pre-extracted session).
 */
export function auditWithKnownActor(
  actor: string,
  entityType: AuditEntityType,
  entityId: string,
  action: AuditAction,
  diff: AuditDiff,
  projectId = 'default',
) {
  return logAuditEvent(entityType, entityId, action, diff, projectId, actor);
}
