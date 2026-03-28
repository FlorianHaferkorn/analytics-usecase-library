/**
 * Theme API — GET/PUT for persisting theme config to SQLite.
 */

import { getProject, updateProject } from '@/lib/db/project-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get('projectId') ?? 'default';

  const project = getProject(projectId);
  if (!project) {
    return new Response(JSON.stringify({ error: 'Project not found' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const theme = project.theme_json ? JSON.parse(project.theme_json) : {};
  return Response.json(theme);
}

export async function PUT(request: Request) {
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
  }, projectId);
  return Response.json({ ok: true });
}
