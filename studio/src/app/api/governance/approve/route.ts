/**
 * Governance Approval API — bracket lifecycle transitions.
 *
 * POST { bracketId, action, justification }
 */

import { requireAuth } from '@/lib/auth/session';
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

export async function GET(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const { searchParams } = new URL(request.url);
  const bracketId = searchParams.get('bracketId');
  if (!bracketId) return apiValidationError(['bracketId required']);

  const lifecycle = getLifecycle(bracketId);
  return apiSuccess({ lifecycle });
}

export async function POST(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const { bracketId, action, justification = '' } = body as {
    bracketId: string;
    action: ApprovalAction;
    justification?: string;
  };

  if (!bracketId || !action) {
    return apiValidationError(['bracketId and action required']);
  }

  // Approve requires admin role
  if (action === 'approve') {
    const dbUser = findOrCreateUser(user.email, user.name);
    if (!checkAccess('default', dbUser.id, 'admin')) {
      return apiError(ErrorCode.FORBIDDEN, 'Admin role required for approval', 403);
    }
  }

  try {
    const handlers: Record<ApprovalAction, () => ReturnType<typeof approve>> = {
      submit: () => submitForReview(bracketId, user.email, justification),
      approve: () => approve(bracketId, user.email, justification),
      reject: () => reject(bracketId, user.email, justification),
      deprecate: () => deprecate(bracketId, user.email, justification),
      reopen: () => reopen(bracketId, user.email, justification),
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
