import { NextResponse } from 'next/server';
import { getProject, updateProject, createProject } from '@/lib/db/project-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { requireAuth } from '@/lib/auth/session';

export async function GET() {
  const project = getProject();
  if (!project) {
    return NextResponse.json({ error: 'Project not found' }, { status: 404 });
  }
  return NextResponse.json({
    ...project,
    theme: JSON.parse(project.theme_json || '{}'),
  });
}

export async function PATCH(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

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

  return NextResponse.json({ ok: true });
}

export async function POST(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const { name, strategyAnchor } = body as { name: string; strategyAnchor?: string };

  if (!name?.trim()) {
    return NextResponse.json({ error: 'Name is required' }, { status: 400 });
  }

  const project = createProject(name.trim(), strategyAnchor?.trim() ?? '');
  logAuditEvent('project', project.id, 'create', {
    before: null,
    after: { name: name.trim(), strategy_anchor: strategyAnchor?.trim() ?? '' },
  }, project.id, user.email);

  return NextResponse.json({ project }, { status: 201 });
}
