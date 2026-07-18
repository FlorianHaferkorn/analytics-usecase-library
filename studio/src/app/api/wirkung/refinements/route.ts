/**
 * Wirkungs-Loop Refinement Approval API — Studio-Approval-Verdrahtung (ADR-0009 §5).
 *
 * GET  — list persisted refinement proposals (history + pending).
 * POST { proposalKey, action: 'approve'|'reject', justification } — decide a
 * pending proposal. Approve requires admin (same rule as bracket approval).
 */

import { requireAuth } from '@/lib/auth/session';
import { requireRole } from '@/lib/auth/require-role';
import { checkAccess } from '@/lib/db/rbac-repo';
import { findOrCreateUser } from '@/lib/db/user-repo';
import { decideRefinement, listRefinements } from '@/lib/governance/refinement-workflow';
import type { RefinementDecision } from '@/lib/governance/refinement-types';
import { apiSuccess, apiError, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function GET() {
  const [, authErr] = await requireRole('viewer');
  if (authErr) return authErr;

  return apiSuccess({ proposals: listRefinements() });
}

export async function POST(request: Request) {
  const [user, authErr] = await requireAuth();
  if (authErr) return authErr;

  const body = await request.json() as {
    proposalKey?: string;
    action?: RefinementDecision;
    justification?: string;
  };

  if (!body.proposalKey || !body.action) {
    return apiValidationError(['proposalKey and action required']);
  }

  if (body.action === 'approve' || body.action === 'reject') {
    const dbUser = findOrCreateUser(user.email, user.name);
    if (!checkAccess('default', dbUser.id, 'admin')) {
      return apiError(ErrorCode.FORBIDDEN, 'Admin role required for approval or rejection', 403);
    }
  }

  try {
    const record = decideRefinement(body.proposalKey, body.action, user.email, body.justification ?? '');
    return apiSuccess({ proposal: record });
  } catch (e) {
    return apiError(ErrorCode.CONFLICT, (e as Error).message, 409);
  }
}
