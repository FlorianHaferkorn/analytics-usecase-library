/**
 * AI-Config layer governance API (I-6.6 UI). Wraps the V5 repo:
 *   GET  ?layer=L1[&domainId=]            → current layer row (status + config)
 *   POST { op, layer, domainId, config?, justification? }
 *        op = save | submit | approve | reject | reopen
 *
 * Auth required; actor = user.email. Approve requires admin (two-person rule is also
 * enforced in the repo). Only approved layers ever reach the resolver.
 */

import { requireAuth } from '@/lib/auth/session';
import { checkAccess } from '@/lib/db/rbac-repo';
import { findOrCreateUser } from '@/lib/db/user-repo';
import {
  getConfigLayer,
  upsertConfigLayer,
  transitionConfigLayer,
  AiConfigGovernanceError,
} from '@/lib/db/ai-config-repo';
import type { AiConfigLayer } from '@/lib/ai/config/resolve';
import { apiSuccess, apiError, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

const PROJECT = 'default';

export async function GET(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;
  const { searchParams } = new URL(request.url);
  const layer = searchParams.get('layer');
  if (layer !== 'L1' && layer !== 'L2') return apiValidationError(['layer must be L1 or L2']);
  const domainId = searchParams.get('domainId') ?? '';
  return apiSuccess({ layer: getConfigLayer(PROJECT, layer, domainId) });
}

export async function POST(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json() as {
    op?: string; layer?: 'L1' | 'L2'; domainId?: string; config?: AiConfigLayer; justification?: string;
  };
  const { op, layer, domainId = '', config, justification = '' } = body;
  if (!op || (layer !== 'L1' && layer !== 'L2')) {
    return apiValidationError(['op and layer (L1|L2) required']);
  }

  if (op === 'approve') {
    const dbUser = findOrCreateUser(user.email, user.name);
    if (!checkAccess(PROJECT, dbUser.id, 'admin')) {
      return apiError(ErrorCode.FORBIDDEN, 'Admin role required to approve config', 403);
    }
  }

  try {
    if (op === 'save') {
      if (!config) return apiValidationError(['config required for save']);
      return apiSuccess({ layer: upsertConfigLayer({ projectId: PROJECT, layer, domainId, config }) });
    }
    if (op === 'submit' || op === 'approve' || op === 'reject' || op === 'reopen') {
      const row = transitionConfigLayer(PROJECT, layer, domainId, op, user.email, justification);
      return apiSuccess({ layer: row });
    }
    return apiValidationError([`Unknown op: ${op}`]);
  } catch (e) {
    if (e instanceof AiConfigGovernanceError) {
      return apiError(ErrorCode.CONFLICT, e.message, 409);
    }
    return apiError(ErrorCode.INTERNAL_ERROR, (e as Error).message, 500);
  }
}
