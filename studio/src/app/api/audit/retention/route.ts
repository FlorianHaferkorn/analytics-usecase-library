/**
 * Retention run for AI egress evidence and AI policy reviews (C-22, M-22.2).
 *
 * GET  /api/audit/retention            dry run: what the run would expire and delete
 * POST /api/audit/retention            { action: 'run', confirm: true }
 *                                      { action: 'hold', projectId, reference }
 *                                      { action: 'release', holdId }
 *
 * Admin of the default project only. The periods are a proposal pending Legal/DSB
 * confirmation (E-22.1); the report says so on every call.
 */
import { requireRole } from '@/lib/auth/require-role';
import { apiError, apiSuccess } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import {
  AiRetentionError, activeLegalHolds, placeLegalHold, releaseLegalHold, resolveAiRetentionPolicy, runAiRetention,
} from '@/lib/db/ai-retention';

function policyOrError() {
  try {
    return [resolveAiRetentionPolicy(), null] as const;
  } catch (error) {
    return [null, apiError(ErrorCode.VALIDATION_ERROR, (error as Error).message, 500)] as const;
  }
}

export async function GET() {
  const [, roleError] = await requireRole('admin');
  if (roleError) return roleError;
  const [resolved, policyError] = policyOrError();
  if (policyError) return policyError;
  const report = runAiRetention({ dryRun: true, policy: resolved.policy, overridden: resolved.overridden });
  return apiSuccess({ report, legalHolds: activeLegalHolds().map(({ id, project_id, reference, created_at }) => ({ id, project_id, reference, created_at })) });
}

export async function POST(request: Request) {
  const [user, roleError] = await requireRole('admin');
  if (roleError) return roleError;
  let body: { action?: unknown; confirm?: unknown; projectId?: unknown; reference?: unknown; holdId?: unknown };
  try {
    body = await request.json();
  } catch {
    return apiError(ErrorCode.VALIDATION_ERROR, 'JSON body required.', 400);
  }
  try {
    if (body.action === 'run') {
      if (body.confirm !== true) {
        return apiError(ErrorCode.VALIDATION_ERROR, 'Run the dry run (GET) first, then confirm with { confirm: true }.', 400);
      }
      const [resolved, policyError] = policyOrError();
      if (policyError) return policyError;
      return apiSuccess({ report: runAiRetention({ dryRun: false, policy: resolved.policy, overridden: resolved.overridden }) });
    }
    if (body.action === 'hold' && typeof body.projectId === 'string' && typeof body.reference === 'string') {
      return apiSuccess({ hold: placeLegalHold(body.projectId, body.reference, user.email) }, 201);
    }
    if (body.action === 'release' && typeof body.holdId === 'string') {
      return apiSuccess({ hold: releaseLegalHold(body.holdId, user.email) });
    }
  } catch (error) {
    if (error instanceof AiRetentionError) return apiError(ErrorCode.CONFLICT, error.message, 409);
    throw error;
  }
  return apiError(ErrorCode.VALIDATION_ERROR, "action must be 'run', 'hold' or 'release' with its fields.", 400);
}
