/**
 * Approval Workflow — bracket lifecycle management.
 *
 * Brackets follow: draft → review → approved/rejected → deprecated.
 * Each transition is audit-logged with the actor and justification.
 */

import { getDb } from '@/lib/db/sqlite';
import { logAuditEvent } from '@/lib/db/audit-repo';
import type { ApprovalStatus, ApprovalRecord, ApprovalAction } from './approval-types';
import { VALID_TRANSITIONS } from './approval-types';

/** Get or initialize the lifecycle record for a bracket. */
export function getLifecycle(bracketId: string): ApprovalRecord {
  const db = getDb();
  const row = db.prepare(
    'SELECT * FROM bracket_lifecycle WHERE bracket_id = ?',
  ).get(bracketId) as ApprovalRecord | undefined;

  if (row) return row;

  // Initialize as draft
  db.prepare(
    'INSERT INTO bracket_lifecycle (bracket_id, status) VALUES (?, ?)',
  ).run(bracketId, 'draft');

  return db.prepare(
    'SELECT * FROM bracket_lifecycle WHERE bracket_id = ?',
  ).get(bracketId) as ApprovalRecord;
}

/** Submit a bracket for review. */
export function submitForReview(
  bracketId: string,
  submittedBy: string,
  justification: string,
): ApprovalRecord {
  return transition(bracketId, 'submit', submittedBy, justification);
}

/** Approve a bracket. */
export function approve(
  bracketId: string,
  approvedBy: string,
  justification: string,
): ApprovalRecord {
  return transition(bracketId, 'approve', approvedBy, justification);
}

/** Reject a bracket. */
export function reject(
  bracketId: string,
  rejectedBy: string,
  justification: string,
): ApprovalRecord {
  return transition(bracketId, 'reject', rejectedBy, justification);
}

/** Deprecate a bracket. */
export function deprecate(
  bracketId: string,
  actor: string,
  justification: string,
): ApprovalRecord {
  return transition(bracketId, 'deprecate', actor, justification);
}

/** Reopen a bracket to draft. */
export function reopen(
  bracketId: string,
  actor: string,
  justification: string,
): ApprovalRecord {
  return transition(bracketId, 'reopen', actor, justification);
}

function transition(
  bracketId: string,
  action: ApprovalAction,
  actor: string,
  justification: string,
): ApprovalRecord {
  const current = getLifecycle(bracketId);
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
    WHERE bracket_id = ?
  `).run(
    newStatus,
    action === 'submit' ? actor : null,
    action === 'approve' ? actor : null,
    justification,
    bracketId,
  );

  logAuditEvent('governance', bracketId, action, {
    before: { status: current.status },
    after: { status: newStatus },
    justification,
  }, 'default', actor);

  return getLifecycle(bracketId);
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
