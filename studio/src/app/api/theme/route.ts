/**
 * Theme API — GET/PUT for persisting theme config to SQLite.
 */

import { getProject, updateProject } from '@/lib/db/project-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { requireAuth } from '@/lib/auth/session';
import { apiSuccess, apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get('projectId') ?? 'default';

  const project = getProject(projectId);
  if (!project) {
    return apiError(ErrorCode.NOT_FOUND, 'Project not found', 404);
  }

  const theme = project.theme_json ? JSON.parse(project.theme_json) : {};
  return apiSuccess(theme);
}

export async function PUT(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const { projectId = 'default', theme } = body as {
    projectId?: string;
    theme: Record<string, unknown>;
  };

  const before = getProject(projectId);
  const beforeTheme = before?.theme_json ? JSON.parse(before.theme_json) : null;
  updateProject(projectId, { theme_json: JSON.stringify(theme) });
  logAuditEvent('theme', projectId, 'update', {
    before: beforeTheme,
    after: theme,
  }, projectId, user.email);
  return apiSuccess({ ok: true });
}
