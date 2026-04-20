/**
 * RBAC enforcement helper for Route Handlers.
 *
 * Usage:
 *   const [user, errResp] = await requireRole('admin');
 *   if (errResp) return errResp;
 *   // user is SessionUser, guaranteed to have at least admin role in 'default' project
 */

import { requireAuth } from './session';
import { checkAccess } from '@/lib/db/rbac-repo';
import { findOrCreateUser } from '@/lib/db/user-repo';
import { apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import type { SessionUser } from './session';
import type { ProjectRole } from './rbac-types';

/**
 * Require that the caller is authenticated AND has at least `minRole`
 * in the given project (defaults to 'default').
 *
 * Returns `[SessionUser, null]` on success, or `[null, Response]` on failure.
 */
export async function requireRole(
  minRole: ProjectRole,
  projectId = 'default',
): Promise<[SessionUser, null] | [null, Response]> {
  const [user, authErr] = await requireAuth();
  if (authErr) return [null, authErr];

  const dbUser = findOrCreateUser(user.email, user.name);
  const member = checkAccess(projectId, dbUser.id, minRole);
  if (!member) {
    return [
      null,
      apiError(
        ErrorCode.FORBIDDEN,
        `Role '${minRole}' or higher required for project '${projectId}'`,
        403,
      ),
    ];
  }

  return [user, null];
}
