import { aiPolicyReviewCandidate } from '@/lib/ai/policy-review';
import { requireRole } from '@/lib/auth/require-role';
import { loadProjectPackage, getPackageHead } from '@/lib/bridge/project-package-repository';
import { apiError, apiSuccess } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import { getProject } from '@/lib/db/project-repo';
import {
  AiPolicyReviewError, finishAiPolicyReview, getAiPolicyReview,
  listAiPolicyReviews, submitAiPolicyReview,
} from '@/lib/db/ai-policy-review-repo';
import { packageRepositoryError } from '@/lib/project-package/http';

type Context = { params: Promise<{ projectId: string }> };
const HASH = /^[a-f0-9]{64}$/;
const ROUTE_ID = /^[a-z][a-z0-9_]{0,63}$/;
const UUID = /^[a-f0-9-]{36}$/i;

export async function GET(_request: Request, { params }: Context) {
  const { projectId } = await params;
  const [, denied] = await requireRole('viewer', projectId);
  if (denied) return denied;
  if (!getProject(projectId)) return apiError(ErrorCode.NOT_FOUND, 'Project not found', 404);
  return apiSuccess({ reviews: listAiPolicyReviews(projectId), egressEnabled: false });
}

export async function POST(request: Request, { params }: Context) {
  const { projectId } = await params;
  let body: Record<string, unknown>;
  try {
    const raw = await request.text();
    if (raw.length > 4096) return apiError(ErrorCode.VALIDATION_ERROR, 'Request too large', 413);
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error();
    body = parsed as Record<string, unknown>;
  } catch { return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid review request', 400); }
  const action = body.action;
  if (action !== 'submit' && action !== 'approve' && action !== 'reject') {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Action must be submit, approve or reject', 422);
  }
  const [user, denied] = await requireRole(action === 'submit' ? 'editor' : 'admin', projectId);
  if (denied) return denied;
  if (!getProject(projectId)) return apiError(ErrorCode.NOT_FOUND, 'Project not found', 404);

  try {
    if (action === 'submit') {
      if (Object.keys(body).some((key) => !['action', 'revisionHash', 'routeId'].includes(key))
        || typeof body.revisionHash !== 'string' || !HASH.test(body.revisionHash)
        || typeof body.routeId !== 'string' || !ROUTE_ID.test(body.routeId)) {
        return apiError(ErrorCode.VALIDATION_ERROR, 'Pinned revision and route ID are required', 422);
      }
      const loaded = await loadProjectPackage(projectId);
      if (!loaded.ok || !loaded.value) return packageRepositoryError(loaded);
      if (loaded.value.revision.revision_hash !== body.revisionHash) {
        return apiError(ErrorCode.CONFLICT, 'Only the current package revision can be submitted', 409);
      }
      const candidate = aiPolicyReviewCandidate(projectId, loaded.value, body.routeId);
      return apiSuccess({ review: submitAiPolicyReview(candidate, user.email), egressEnabled: false }, 201);
    }
    if (Object.keys(body).some((key) => !['action', 'reviewId', 'rationale'].includes(key))
      || typeof body.reviewId !== 'string' || !UUID.test(body.reviewId)
      || typeof body.rationale !== 'string' || body.rationale.trim().length < 20 || body.rationale.length > 2000) {
      return apiError(ErrorCode.VALIDATION_ERROR, 'Review ID and a 20–2000 character rationale are required', 422);
    }
    const review = getAiPolicyReview(projectId, body.reviewId);
    if (!review || review.status !== 'pending') return apiError(ErrorCode.NOT_FOUND, 'Pending review not found', 404);
    let candidate;
    if (action === 'approve') {
      const loaded = await loadProjectPackage(projectId);
      if (!loaded.ok || !loaded.value) return packageRepositoryError(loaded);
      if (loaded.value.revision.revision_hash !== review.revision_hash) {
        return apiError(ErrorCode.CONFLICT, 'Package HEAD changed; submit a new review', 409);
      }
      candidate = aiPolicyReviewCandidate(projectId, loaded.value, review.route_id);
      const head = await getPackageHead(projectId);
      if (!head.ok || !head.value) return packageRepositoryError(head);
      if (head.value.revision_hash !== review.revision_hash) {
        return apiError(ErrorCode.CONFLICT, 'Package HEAD changed; submit a new review', 409);
      }
    }
    const result = finishAiPolicyReview(projectId, review.id, action, user.email, body.rationale.trim(), candidate);
    return apiSuccess({ review: result, egressEnabled: false });
  } catch (error) {
    if (error instanceof AiPolicyReviewError) return apiError(ErrorCode.CONFLICT, error.message, 409);
    return apiError(ErrorCode.VALIDATION_ERROR,
      error instanceof Error ? error.message : 'AI policy review failed', 422);
  }
}
