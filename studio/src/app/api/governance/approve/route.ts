/**
 * Governance Approval API — bracket lifecycle transitions.
 *
 * POST { bracketId, action, justification }
 */

import { requireAuth } from '@/lib/auth/session';
import { requireRole } from '@/lib/auth/require-role';
import { checkAccess } from '@/lib/db/rbac-repo';
import { findOrCreateUser } from '@/lib/db/user-repo';
import {
  getLifecycle,
  submitForReview,
  approve,
  reject,
  deprecate,
  reopen,
} from '@/lib/governance/approval-workflow';
import type { ApprovalAction } from '@/lib/governance/approval-types';
import { apiSuccess, apiError, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function handleApproveGET(request: Request, overrideProjectId?: string) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const { searchParams } = new URL(request.url);
  const bracketId = searchParams.get('bracketId');
  if (!bracketId) return apiValidationError(['bracketId required']);
  const projectId = overrideProjectId ?? searchParams.get('projectId') ?? 'default';

  const lifecycle = getLifecycle(bracketId, projectId);
  return apiSuccess({ lifecycle });
}

export async function GET(request: Request) {
  return handleApproveGET(request);
}

export async function handleApprovePOST(request: Request, overrideProjectId?: string) {
  const body = await request.json();
  const { bracketId, action, justification = '', projectId: bodyProjectId = 'default' } = body as {
    bracketId: string;
    action: ApprovalAction;
    justification?: string;
    projectId?: string;
  };
  // Resolved before the role check so a caller can't pass a body.projectId
  // that differs from the project they're actually authorized against —
  // requireRole's checkAccess() must run against the SAME project the
  // handlers below operate on, not an implicit 'default'.
  const projectId = overrideProjectId ?? bodyProjectId;

  const [user, authError] = await requireRole('editor', projectId);
  if (authError) return authError;

  if (!bracketId || !action) {
    return apiValidationError(['bracketId and action required']);
  }

  // Approve requires admin role (stricter than the baseline editor gate above)
  if (action === 'approve') {
    const dbUser = findOrCreateUser(user.email, user.name);
    if (!checkAccess(projectId, dbUser.id, 'admin')) {
      return apiError(ErrorCode.FORBIDDEN, 'Admin role required for approval', 403);
    }
  }

  try {
    const handlers: Record<ApprovalAction, () => ReturnType<typeof approve>> = {
      submit: () => submitForReview(bracketId, user.email, justification, projectId),
      approve: () => approve(bracketId, user.email, justification, projectId),
      reject: () => reject(bracketId, user.email, justification, projectId),
      deprecate: () => deprecate(bracketId, user.email, justification, projectId),
      reopen: () => reopen(bracketId, user.email, justification, projectId),
    };

    const handler = handlers[action];
    if (!handler) {
      return apiValidationError([`Unknown action: ${action}`]);
    }

    const lifecycle = handler();
    return apiSuccess({ lifecycle });
  } catch (e) {
    return apiError(ErrorCode.CONFLICT, (e as Error).message, 409);
  }
}

export async function POST(request: Request) {
  return handleApprovePOST(request);
}
