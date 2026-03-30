import { NextResponse } from 'next/server';
import { saveBracketEdit, getAllBracketEdits, getBracketEdit } from '@/lib/db/project-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { requireAuth } from '@/lib/auth/session';
import { checkAccess } from '@/lib/db/rbac-repo';
import { findOrCreateUser } from '@/lib/db/user-repo';

export async function GET() {
  const edits = getAllBracketEdits();
  return NextResponse.json({ edits });
}

export async function PUT(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const dbUser = findOrCreateUser(user.email, user.name);
  if (!checkAccess('default', dbUser.id, 'editor')) {
    return NextResponse.json({ error: 'Forbidden: editor role required' }, { status: 403 });
  }

  const body = await request.json();
  const { bracketId, yamlContent } = body as { bracketId: string; yamlContent: string };

  if (!bracketId || !yamlContent) {
    return NextResponse.json({ error: 'bracketId and yamlContent required' }, { status: 400 });
  }

  const before = getBracketEdit(bracketId);
  saveBracketEdit(bracketId, yamlContent);
  logAuditEvent('bracket', bracketId, before ? 'update' : 'create', {
    before: before ? { yaml: before.yaml_content } : null,
    after: { yaml: yamlContent },
  }, 'default', user.email);

  return NextResponse.json({ ok: true });
}
