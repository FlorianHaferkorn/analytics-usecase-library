/**
 * Refinement Workflow — Wirkungs-Loop proposal review (ADR-0009 §5,
 * Studio-Approval-Verdrahtung).
 *
 * Proposals are re-derived from the Python core on every compute
 * (`bridge.py attribute`) — this module only persists the human decision so a
 * recompute doesn't lose it, and only ever writes on approve/reject. Nothing
 * here mutates the governed core (ADR-0009's "kein Auto-Mutate" invariant).
 */

import { getDb } from '@/lib/db/sqlite';
import { logAuditEvent } from '@/lib/db/audit-repo';
import type { RefinementDecision, RefinementLifecycleRecord } from './refinement-types';
import { proposalKey } from './refinement-types';

export interface FreshProposal {
  actionCodeId: string;
  kpiId: string;
  triggerKind: 'no_effect' | 'material_effect';
  relChange: number;
  rationale: string;
}

/**
 * Upsert a freshly-computed proposal into the lifecycle table. Only updates
 * the derived fields (rel_change/rationale/trigger) while the proposal is
 * still `pending_review` — an already-decided proposal's history is never
 * silently overwritten by a later recompute with a different rel_change.
 */
export function upsertPendingProposal(p: FreshProposal): RefinementLifecycleRecord {
  const db = getDb();
  const key = proposalKey(p.actionCodeId, p.kpiId);

  db.prepare(`
    INSERT INTO refinement_lifecycle (proposal_key, action_code_id, kpi_id, trigger_kind, rel_change, rationale)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(proposal_key) DO UPDATE SET
      trigger_kind = excluded.trigger_kind,
      rel_change = excluded.rel_change,
      rationale = excluded.rationale,
      updated_at = datetime('now')
    WHERE refinement_lifecycle.status = 'pending_review'
  `).run(key, p.actionCodeId, p.kpiId, p.triggerKind, p.relChange, p.rationale);

  return db.prepare('SELECT * FROM refinement_lifecycle WHERE proposal_key = ?').get(key) as RefinementLifecycleRecord;
}

/** List all persisted refinement lifecycle rows (for a history/overview view). */
export function listRefinements(): RefinementLifecycleRecord[] {
  const db = getDb();
  return db.prepare('SELECT * FROM refinement_lifecycle ORDER BY updated_at DESC').all() as RefinementLifecycleRecord[];
}

export function getRefinement(key: string): RefinementLifecycleRecord | undefined {
  const db = getDb();
  return db.prepare('SELECT * FROM refinement_lifecycle WHERE proposal_key = ?').get(key) as RefinementLifecycleRecord | undefined;
}

/** Approve or reject a pending proposal. Throws on an unknown key or a proposal that's already decided. */
export function decideRefinement(
  key: string,
  decision: RefinementDecision,
  actor: string,
  justification: string,
): RefinementLifecycleRecord {
  const current = getRefinement(key);
  if (!current) {
    throw new Error(`Unknown refinement proposal: ${key}`);
  }
  if (current.status !== 'pending_review') {
    throw new Error(`Proposal already ${current.status}: ${key}`);
  }

  const newStatus = decision === 'approve' ? 'approved' : 'rejected';
  const db = getDb();
  db.prepare(`
    UPDATE refinement_lifecycle
    SET status = ?, decided_by = ?, justification = ?, updated_at = datetime('now')
    WHERE proposal_key = ?
  `).run(newStatus, actor, justification, key);

  logAuditEvent('refinement', key, decision, {
    before: { status: current.status },
    after: { status: newStatus },
    justification,
  }, 'default', actor);

  return getRefinement(key) as RefinementLifecycleRecord;
}
