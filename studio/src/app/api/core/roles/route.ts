/**
 * GET /api/core/roles
 *
 * Returns all resolved org roles from core/organization/org_roles.yaml.
 * Requires authentication.
 */

import { loadOrgRoles } from '@/lib/core/org-role-loader';
import { apiSuccess } from '@/lib/api/response';
import { requireAuth } from '@/lib/auth/session';

export async function GET(_request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const roleMap = await loadOrgRoles();
  const roles = [...roleMap.values()];

  return apiSuccess({ roles });
}
