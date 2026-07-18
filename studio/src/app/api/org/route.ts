/**
 * Organizations API — list + create (ADR-0014, I-9.2).
 *
 * Any authenticated user can list orgs and create a new one, same trust level
 * as /api/project today (this app has no cross-project isolation boundary yet
 * for any authenticated local user — an org is a grouping layer, not a new
 * security perimeter on top of what already exists).
 */

import { requireAuth } from '@/lib/auth/session';
import { findOrCreateUser } from '@/lib/db/user-repo';
import { listOrganizations, createOrganization, addOrgMember } from '@/lib/db/org-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { apiSuccess, apiCreated, apiValidationError } from '@/lib/api/response';

export async function GET() {
  const [, authErr] = await requireAuth();
  if (authErr) return authErr;

  return apiSuccess({ organizations: listOrganizations() });
}

export async function POST(request: Request) {
  const [user, authErr] = await requireAuth();
  if (authErr) return authErr;

  const body = await request.json();
  const { name } = body as { name?: string };
  if (!name?.trim()) {
    return apiValidationError(['Name is required']);
  }

  const org = createOrganization(name.trim());

  const dbUser = findOrCreateUser(user.email, user.name);
  addOrgMember(org.id, dbUser.id, 'owner');

  logAuditEvent('org', org.id, 'create', {
    before: null,
    after: { name: name.trim() },
  }, 'default', user.email);

  return apiCreated({ organization: org });
}
