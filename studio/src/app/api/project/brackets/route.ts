import { saveBracketEdit, getAllBracketEdits, getBracketEdit } from '@/lib/db/project-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { requireAuth } from '@/lib/auth/session';
import { checkAccess } from '@/lib/db/rbac-repo';
import { findOrCreateUser } from '@/lib/db/user-repo';
import { apiSuccess, apiError, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function GET() {
  const edits = getAllBracketEdits();
  return apiSuccess({ edits });
}

export async function PUT(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const dbUser = findOrCreateUser(user.email, user.name);
  if (!checkAccess('default', dbUser.id, 'editor')) {
    return apiError(ErrorCode.FORBIDDEN, 'Editor role required', 403);
  }

  const body = await request.json();
  const { bracketId, yamlContent } = body as { bracketId: string; yamlContent: string };

  if (!bracketId || !yamlContent) {
    return apiValidationError(['bracketId and yamlContent required']);
  }

  const before = getBracketEdit(bracketId);
  saveBracketEdit(bracketId, yamlContent);
  logAuditEvent('bracket', bracketId, before ? 'update' : 'create', {
    before: before ? { yaml: before.yaml_content } : null,
    after: { yaml: yamlContent },
  }, 'default', user.email);

  return apiSuccess({ ok: true });
}
