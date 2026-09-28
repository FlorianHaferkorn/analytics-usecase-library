import 'server-only';
import { randomUUID } from 'node:crypto';
import type { AiPolicyReviewCandidate } from '@/lib/ai/policy-review';
import { getDb } from './sqlite';
import { logAuditEvent } from './audit-repo';

export type AiPolicyReviewStatus = 'pending' | 'approved' | 'rejected' | 'expired';
export interface AiPolicyReview {
  id: string;
  project_id: string;
  revision_hash: string;
  route_id: string;
  route_hash: string;
  decision_ref: string;
  status: AiPolicyReviewStatus;
  submitted_by: string;
  submitted_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  rationale: string | null;
  route_expires_at: string | null;
}

export class AiPolicyReviewError extends Error {}

export function listAiPolicyReviews(projectId: string): AiPolicyReview[] {
  return getDb().prepare(`
    SELECT * FROM ai_policy_reviews WHERE project_id = ? ORDER BY rowid DESC LIMIT 100
  `).all(projectId) as AiPolicyReview[];
}

export function getAiPolicyReview(projectId: string, reviewId: string): AiPolicyReview | null {
  return (getDb().prepare(`
    SELECT * FROM ai_policy_reviews WHERE project_id = ? AND id = ?
  `).get(projectId, reviewId) as AiPolicyReview | undefined) ?? null;
}

export function submitAiPolicyReview(candidate: AiPolicyReviewCandidate, actor: string): AiPolicyReview {
  const db = getDb();
  return db.transaction(() => {
    const current = db.prepare(`
      SELECT * FROM ai_policy_reviews
      WHERE project_id = ? AND revision_hash = ? AND route_id = ?
      ORDER BY rowid DESC LIMIT 1
    `).get(candidate.projectId, candidate.revisionHash, candidate.routeId) as AiPolicyReview | undefined;
    if (current && current.status !== 'rejected' && current.status !== 'expired') throw new AiPolicyReviewError('This exact policy is already under review or approved.');
    const id = randomUUID();
    db.prepare(`
      INSERT INTO ai_policy_reviews
        (id, project_id, revision_hash, route_id, route_hash, decision_ref, status, submitted_by,
         route_expires_at)
      VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
    `).run(id, candidate.projectId, candidate.revisionHash, candidate.routeId,
      candidate.routeHash, candidate.decisionRef, actor, candidate.expiresAt);
    logAuditEvent('ai_policy_review', id, 'submit', {
      before: null,
      after: { revision_hash: candidate.revisionHash, route_id: candidate.routeId,
        route_hash: candidate.routeHash, status: 'pending' },
    }, candidate.projectId, actor);
    return getAiPolicyReview(candidate.projectId, id)!;
  })();
}

export function finishAiPolicyReview(
  projectId: string,
  reviewId: string,
  action: 'approve' | 'reject',
  actor: string,
  rationale: string,
  candidate?: AiPolicyReviewCandidate,
): AiPolicyReview {
  const db = getDb();
  return db.transaction(() => {
    const review = getAiPolicyReview(projectId, reviewId);
    if (!review || review.status !== 'pending') throw new AiPolicyReviewError('Pending review not found.');
    if (review.submitted_by.toLowerCase() === actor.toLowerCase()) {
      throw new AiPolicyReviewError('A second person must review this AI policy.');
    }
    if (action === 'approve' && (!candidate || candidate.projectId !== projectId
      || candidate.revisionHash !== review.revision_hash || candidate.routeId !== review.route_id
      || candidate.routeHash !== review.route_hash || candidate.decisionRef !== review.decision_ref)) {
      throw new AiPolicyReviewError('Policy or package revision changed; approval is not valid.');
    }
    const result = db.prepare(`
      UPDATE ai_policy_reviews SET status = ?, reviewed_by = ?, reviewed_at = datetime('now'), rationale = ?
      WHERE id = ? AND project_id = ? AND status = 'pending'
    `).run(action === 'approve' ? 'approved' : 'rejected', actor, rationale, reviewId, projectId);
    if (result.changes !== 1) throw new AiPolicyReviewError('Review changed concurrently.');
    logAuditEvent('ai_policy_review', reviewId, action, {
      before: { status: 'pending' },
      after: { status: action === 'approve' ? 'approved' : 'rejected',
        revision_hash: review.revision_hash, route_id: review.route_id, route_hash: review.route_hash },
      justification: rationale,
    }, projectId, actor);
    return getAiPolicyReview(projectId, reviewId)!;
  })();
}
