import { getProject, updateProject, createProject } from '@/lib/db/project-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { requireAuth } from '@/lib/auth/session';
import { checkAccess, addProjectMember } from '@/lib/db/rbac-repo';
import { findOrCreateUser } from '@/lib/db/user-repo';
import { apiSuccess, apiCreated, apiError, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import { requireRole } from '@/lib/auth/require-role';

export async function GET() {
  const [, accessError] = await requireRole('viewer', 'default');
  if (accessError) return accessError;
  const project = getProject();
  if (!project) {
    return apiError(ErrorCode.NOT_FOUND, 'Project not found', 404);
  }
  return apiSuccess({
    ...project,
    theme: JSON.parse(project.theme_json || '{}'),
  });
}

export async function PATCH(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const dbUser = findOrCreateUser(user.email, user.name);
  if (!checkAccess('default', dbUser.id, 'editor')) {
    return apiError(ErrorCode.FORBIDDEN, 'Editor role required', 403);
  }

  const body = await request.json();
  const { name, strategy_anchor, theme } = body as {
    name?: string;
    strategy_anchor?: string;
    theme?: Record<string, unknown>;
  };

  const before = getProject();
  updateProject('default', {
    name,
    strategy_anchor,
    theme_json: theme ? JSON.stringify(theme) : undefined,
  });
  logAuditEvent('project', 'default', 'update', {
    before: before ? { name: before.name, strategy_anchor: before.strategy_anchor } : null,
    after: { name, strategy_anchor },
  }, 'default', user.email);

  return apiSuccess({ ok: true });
}

export async function POST(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const { name, strategyAnchor } = body as { name: string; strategyAnchor?: string };

  if (!name?.trim()) {
    return apiValidationError(['Name is required']);
  }

  const project = createProject(name.trim(), strategyAnchor?.trim() ?? '');

  const dbUser = findOrCreateUser(user.email, user.name);
  addProjectMember(project.id, dbUser.id, 'admin');

  logAuditEvent('project', project.id, 'create', {
    before: null,
    after: { name: name.trim(), strategy_anchor: strategyAnchor?.trim() ?? '' },
  }, project.id, user.email);

  return apiCreated({ project });
}
