/**
 * Approval Workflow — bracket lifecycle management.
 *
 * Brackets follow: draft → review → approved/rejected → deprecated.
 * Each transition is audit-logged with the actor and justification.
 *
 * Scoped by (bracket_id, project_id) — a bracket_id is only unique within a
 * project (bracket_lifecycle's PK is composite, not bracket_id alone; see
 * sqlite.ts::migrateBracketLifecyclePrimaryKey for why). projectId defaults to
 * 'default' everywhere, matching the same convention used by checkAccess/
 * requireRole/createBracket — existing single-project callers are unaffected.
 */

import { getDb } from '@/lib/db/sqlite';
import { logAuditEvent } from '@/lib/db/audit-repo';
import type { ApprovalStatus, ApprovalRecord, ApprovalAction } from './approval-types';
import { VALID_TRANSITIONS } from './approval-types';

/** Get or initialize the lifecycle record for a bracket within a project. */
export function getLifecycle(bracketId: string, projectId = 'default'): ApprovalRecord {
  const db = getDb();
  const row = db.prepare(
    'SELECT * FROM bracket_lifecycle WHERE bracket_id = ? AND project_id = ?',
  ).get(bracketId, projectId) as ApprovalRecord | undefined;

  if (row) return row;

  // Initialize as draft
  db.prepare(
    'INSERT INTO bracket_lifecycle (bracket_id, project_id, status) VALUES (?, ?, ?)',
  ).run(bracketId, projectId, 'draft');

  return db.prepare(
    'SELECT * FROM bracket_lifecycle WHERE bracket_id = ? AND project_id = ?',
  ).get(bracketId, projectId) as ApprovalRecord;
}

/** Submit a bracket for review. */
export function submitForReview(
  bracketId: string,
  submittedBy: string,
  justification: string,
  projectId = 'default',
): ApprovalRecord {
  return transition(bracketId, 'submit', submittedBy, justification, projectId);
}

/** Approve a bracket. */
export function approve(
  bracketId: string,
  approvedBy: string,
  justification: string,
  projectId = 'default',
): ApprovalRecord {
  return transition(bracketId, 'approve', approvedBy, justification, projectId);
}

/** Reject a bracket. */
export function reject(
  bracketId: string,
  rejectedBy: string,
  justification: string,
  projectId = 'default',
): ApprovalRecord {
  return transition(bracketId, 'reject', rejectedBy, justification, projectId);
}

/** Deprecate a bracket. */
export function deprecate(
  bracketId: string,
  actor: string,
  justification: string,
  projectId = 'default',
): ApprovalRecord {
  return transition(bracketId, 'deprecate', actor, justification, projectId);
}

/** Reopen a bracket to draft. */
export function reopen(
  bracketId: string,
  actor: string,
  justification: string,
  projectId = 'default',
): ApprovalRecord {
  return transition(bracketId, 'reopen', actor, justification, projectId);
}

function transition(
  bracketId: string,
  action: ApprovalAction,
  actor: string,
  justification: string,
  projectId: string,
): ApprovalRecord {
  const current = getLifecycle(bracketId, projectId);
  const allowed = VALID_TRANSITIONS[current.status];

  if (!allowed.includes(action)) {
    throw new Error(
      `Invalid transition: cannot ${action} from ${current.status}. Allowed: ${allowed.join(', ')}`,
    );
  }

  // Block self-approval
  if (action === 'approve' && current.submitted_by === actor) {
    throw new Error('Cannot approve your own submission');
  }

  const newStatus = resolveStatus(action);
  const db = getDb();

  db.prepare(`
    UPDATE bracket_lifecycle
    SET status = ?, submitted_by = COALESCE(?, submitted_by), approved_by = ?,
        justification = ?, updated_at = datetime('now')
    WHERE bracket_id = ? AND project_id = ?
  `).run(
    newStatus,
    action === 'submit' ? actor : null,
    action === 'approve' ? actor : null,
    justification,
    bracketId,
    projectId,
  );

  logAuditEvent('governance', bracketId, action, {
    before: { status: current.status },
    after: { status: newStatus },
    justification,
  }, projectId, actor);

  return getLifecycle(bracketId, projectId);
}

function resolveStatus(action: ApprovalAction): ApprovalStatus {
  switch (action) {
    case 'submit': return 'review';
    case 'approve': return 'approved';
    case 'reject': return 'rejected';
    case 'deprecate': return 'deprecated';
    case 'reopen': return 'draft';
  }
}
