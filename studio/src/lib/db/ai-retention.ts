/**
 * Retention for AI egress evidence and AI policy reviews (C-22, M-22.1/M-22.2/M-22.5).
 *
 * The periods are the PROPOSAL from compliance/ai_egress_measures.md 2.3. Legal/DSB have not
 * confirmed them (E-22.1); every report says so. Deployments may override them through
 * environment variables, which is where a confirmed value goes.
 *
 * Deleting an event from the hash chain would break verification of every later event. The run
 * therefore attests each gap it creates in its own chained `audit_retention` event, and
 * `verifyChain` accepts a gap only where that attestation names the resume event and the hash it
 * continues from. Any other deletion is still tampering.
 *
 * Content-free by construction: the report and the attestation carry counts, ids, hashes and
 * cutoffs; never an actor, a rationale or a diff.
 */
import 'server-only';
import { randomUUID } from 'node:crypto';
import { getDb } from './sqlite';
import { logAuditEvent } from './audit-repo';
import { verifyChain } from './audit-chain';

export interface AiRetentionPolicy {
  /** Category A/B: `ai_egress` evidence, from `created_at`. */
  egressMonths: number;
  /** Category E: rejected or expired reviews and their audit events, from `reviewed_at`. */
  closedReviewMonths: number;
  /** Category F: a pending review without decision becomes `expired`, from `submitted_at`. */
  pendingMonths: number;
  /** Category D: approved reviews, years after the end of the year the route expires. */
  approvedYearsAfterRouteEnd: number;
}

/** Proposal 26.09.2026, not legally confirmed (E-22.1). */
export const AI_RETENTION_PROPOSAL: Readonly<AiRetentionPolicy> = Object.freeze({
  egressMonths: 13,
  closedReviewMonths: 13,
  pendingMonths: 6,
  approvedYearsAfterRouteEnd: 3,
});

export const AI_RETENTION_POLICY_STATUS = 'proposal_pending_legal_confirmation';

const ENV_KEYS: Record<keyof AiRetentionPolicy, string> = {
  egressMonths: 'STUDIO_AI_RETENTION_EGRESS_MONTHS',
  closedReviewMonths: 'STUDIO_AI_RETENTION_CLOSED_REVIEW_MONTHS',
  pendingMonths: 'STUDIO_AI_RETENTION_PENDING_MONTHS',
  approvedYearsAfterRouteEnd: 'STUDIO_AI_RETENTION_APPROVED_YEARS',
};

export class AiRetentionError extends Error {}

/** Proposal defaults, each overridable by a whole number between 1 and 120. */
export function resolveAiRetentionPolicy(env: Record<string, string | undefined> = process.env): {
  policy: AiRetentionPolicy; overridden: (keyof AiRetentionPolicy)[];
} {
  const policy: AiRetentionPolicy = { ...AI_RETENTION_PROPOSAL };
  const overridden: (keyof AiRetentionPolicy)[] = [];
  for (const [field, key] of Object.entries(ENV_KEYS) as [keyof AiRetentionPolicy, string][]) {
    const raw = env[key];
    if (raw === undefined || raw === '') continue;
    if (!/^\d+$/.test(raw) || Number(raw) < 1 || Number(raw) > 120) {
      throw new AiRetentionError(`${key} must be a whole number between 1 and 120.`);
    }
    policy[field] = Number(raw);
    overridden.push(field);
  }
  return { policy, overridden };
}

/** SQLite `datetime('now')` form, UTC. */
function sqlTime(date: Date): string {
  return date.toISOString().slice(0, 19).replace('T', ' ');
}

function monthsBefore(now: Date, months: number): Date {
  const d = new Date(now.getTime());
  d.setUTCMonth(d.getUTCMonth() - months);
  return d;
}

/** End of the calendar year of `expiresAt` plus `years`; null if the date cannot be read. */
export function approvedRetentionEnd(expiresAt: string | null, years: number): Date | null {
  if (!expiresAt) return null;
  const parsed = Date.parse(expiresAt);
  if (!Number.isFinite(parsed)) return null;
  const year = new Date(parsed).getUTCFullYear();
  return new Date(Date.UTC(year + years + 1, 0, 1));
}

export interface LegalHold {
  id: string;
  project_id: string;
  reference: string;
  created_by: string;
  created_at: string;
  released_by: string | null;
  released_at: string | null;
}

const HOLD_REFERENCE = /^[A-Za-z0-9._:/-]{3,80}$/;

/** A hold names a case or ticket reference, not a free-text reason (no personal data). */
export function placeLegalHold(projectId: string, reference: string, actor: string): LegalHold {
  if (!HOLD_REFERENCE.test(reference)) {
    throw new AiRetentionError('A legal hold needs a case or ticket reference (3-80 characters: letters, digits, . _ : / -).');
  }
  const db = getDb();
  const id = randomUUID();
  db.transaction(() => {
    db.prepare('INSERT INTO audit_legal_holds (id, project_id, reference, created_by) VALUES (?, ?, ?, ?)')
      .run(id, projectId, reference, actor);
    logAuditEvent('audit_retention', id, 'create', { before: null, after: { legal_hold: id, reference } }, projectId, actor);
  })();
  return db.prepare('SELECT * FROM audit_legal_holds WHERE id = ?').get(id) as LegalHold;
}

export function releaseLegalHold(holdId: string, actor: string): LegalHold {
  const db = getDb();
  const hold = db.prepare('SELECT * FROM audit_legal_holds WHERE id = ?').get(holdId) as LegalHold | undefined;
  if (!hold || hold.released_at) throw new AiRetentionError('Active legal hold not found.');
  db.transaction(() => {
    db.prepare("UPDATE audit_legal_holds SET released_by = ?, released_at = datetime('now') WHERE id = ?").run(actor, holdId);
    logAuditEvent('audit_retention', holdId, 'delete', { before: { legal_hold: holdId }, after: null }, hold.project_id, actor);
  })();
  return db.prepare('SELECT * FROM audit_legal_holds WHERE id = ?').get(holdId) as LegalHold;
}

export function activeLegalHolds(): LegalHold[] {
  return getDb().prepare('SELECT * FROM audit_legal_holds WHERE released_at IS NULL ORDER BY created_at').all() as LegalHold[];
}

interface ChainRow { id: string; project_id: string; entity_type: string; entity_id: string; created_at: string; hash: string | null; prev_hash: string | null }
interface ReviewRow { id: string; project_id: string; status: string; submitted_at: string; reviewed_at: string | null; route_expires_at: string | null }

export interface AiRetentionGap { resume_event_id: string; expected_prev_hash: string }

export interface AiRetentionProjectResult {
  project_id: string;
  state: 'pruned' | 'nothing_due' | 'legal_hold' | 'chain_invalid';
  expire_pending_reviews: number;
  delete_ai_egress_events: number;
  delete_reviews: number;
  delete_review_events: number;
  gaps: AiRetentionGap[];
  /** Approved reviews stored before `route_expires_at` existed: kept, cannot be evaluated. */
  approved_without_route_expiry: number;
}

export interface AiRetentionReport {
  run_id: string;
  dry_run: boolean;
  at: string;
  policy: AiRetentionPolicy;
  policy_status: typeof AI_RETENTION_POLICY_STATUS;
  overridden: (keyof AiRetentionPolicy)[];
  cutoffs: { ai_egress_before: string; closed_review_before: string; pending_submitted_before: string };
  projects: AiRetentionProjectResult[];
}

function gapsFor(chain: ChainRow[], deleted: Set<string>): AiRetentionGap[] {
  const gaps: AiRetentionGap[] = [];
  let lastDeletedHash: string | null = null;
  for (const row of chain) {
    if (deleted.has(row.id)) {
      if (row.hash) lastDeletedHash = row.hash;
      continue;
    }
    if (lastDeletedHash !== null && row.hash) {
      gaps.push({ resume_event_id: row.id, expected_prev_hash: lastDeletedHash });
    }
    if (row.hash) lastDeletedHash = null;
  }
  return gaps;
}

/**
 * Apply the retention periods. `dryRun` (the default) computes the same report and writes
 * nothing. A project under legal hold or with an already broken chain is left untouched; a
 * broken chain is reported, not laundered by a deletion.
 */
export function runAiRetention(options: {
  now?: Date; dryRun?: boolean; policy?: AiRetentionPolicy; overridden?: (keyof AiRetentionPolicy)[];
} = {}): AiRetentionReport {
  const db = getDb();
  const now = options.now ?? new Date();
  const dryRun = options.dryRun ?? true;
  const policy = options.policy ?? { ...AI_RETENTION_PROPOSAL };
  const runId = randomUUID();
  const cutoffs = {
    ai_egress_before: sqlTime(monthsBefore(now, policy.egressMonths)),
    closed_review_before: sqlTime(monthsBefore(now, policy.closedReviewMonths)),
    pending_submitted_before: sqlTime(monthsBefore(now, policy.pendingMonths)),
  };
  const held = new Set(activeLegalHolds().map((h) => h.project_id));

  const reviews = db.prepare('SELECT id, project_id, status, submitted_at, reviewed_at, route_expires_at FROM ai_policy_reviews').all() as ReviewRow[];
  const egressProjects = db.prepare("SELECT DISTINCT project_id FROM audit_events WHERE entity_type = 'ai_egress'").all() as { project_id: string }[];
  const projectIds = [...new Set([...reviews.map((r) => r.project_id), ...egressProjects.map((r) => r.project_id)])].sort();

  const results: AiRetentionProjectResult[] = [];
  for (const projectId of projectIds) {
    const own = reviews.filter((r) => r.project_id === projectId);
    const expire = own.filter((r) => r.status === 'pending' && r.submitted_at < cutoffs.pending_submitted_before);
    const approvedUnknown = own.filter((r) => r.status === 'approved' && !approvedRetentionEnd(r.route_expires_at, policy.approvedYearsAfterRouteEnd)).length;
    const deleteReviews = own.filter((r) => {
      if ((r.status === 'rejected' || r.status === 'expired') && r.reviewed_at) return r.reviewed_at < cutoffs.closed_review_before;
      if (r.status === 'approved') {
        const end = approvedRetentionEnd(r.route_expires_at, policy.approvedYearsAfterRouteEnd);
        return end !== null && end.getTime() <= now.getTime();
      }
      return false;
    });
    const reviewIds = new Set(deleteReviews.map((r) => r.id));
    const chain = db.prepare(
      'SELECT id, project_id, entity_type, entity_id, created_at, hash, prev_hash FROM audit_events WHERE project_id = ? ORDER BY created_at ASC, rowid ASC',
    ).all(projectId) as ChainRow[];
    const egress = chain.filter((e) => e.entity_type === 'ai_egress' && e.created_at < cutoffs.ai_egress_before);
    const reviewEvents = chain.filter((e) => e.entity_type === 'ai_policy_review' && reviewIds.has(e.entity_id));
    const deleted = new Set([...egress, ...reviewEvents].map((e) => e.id));
    const result: AiRetentionProjectResult = {
      project_id: projectId,
      state: 'nothing_due',
      expire_pending_reviews: expire.length,
      delete_ai_egress_events: egress.length,
      delete_reviews: deleteReviews.length,
      delete_review_events: reviewEvents.length,
      gaps: gapsFor(chain, deleted),
      approved_without_route_expiry: approvedUnknown,
    };
    const due = expire.length + deleted.size + deleteReviews.length > 0;
    if (held.has(projectId)) {
      result.state = 'legal_hold';
    } else if (due && !verifyChain(projectId).valid) {
      result.state = 'chain_invalid';
    } else if (due) {
      result.state = 'pruned';
    }
    results.push(result);

    if (dryRun || result.state !== 'pruned') continue;
    db.transaction(() => {
      const at = sqlTime(now);
      for (const review of expire) {
        db.prepare("UPDATE ai_policy_reviews SET status = 'expired', reviewed_by = 'system', reviewed_at = ? WHERE id = ? AND status = 'pending'")
          .run(at, review.id);
        logAuditEvent('ai_policy_review', review.id, 'expire', {
          before: { status: 'pending' }, after: { status: 'expired', retention_run: runId },
        }, projectId, 'system');
      }
      const deleteEvent = db.prepare('DELETE FROM audit_events WHERE id = ?');
      for (const id of deleted) deleteEvent.run(id);
      const deleteReview = db.prepare('DELETE FROM ai_policy_reviews WHERE id = ?');
      for (const id of reviewIds) deleteReview.run(id);
      if (deleted.size > 0 || reviewIds.size > 0) {
        logAuditEvent('audit_retention', runId, 'delete', {
          before: null,
          after: {
            run_id: runId, policy, policy_status: AI_RETENTION_POLICY_STATUS, cutoffs,
            deleted: { ai_egress_events: egress.length, reviews: reviewIds.size, review_events: reviewEvents.length },
            gaps: result.gaps,
          },
        }, projectId, 'system');
      }
      const check = verifyChain(projectId);
      if (!check.valid) {
        throw new AiRetentionError(`Retention would break the audit chain of ${projectId}; rolled back.`);
      }
    })();
  }

  return {
    run_id: runId, dry_run: dryRun, at: sqlTime(now), policy,
    policy_status: AI_RETENTION_POLICY_STATUS, overridden: options.overridden ?? [], cutoffs, projects: results,
  };
}
