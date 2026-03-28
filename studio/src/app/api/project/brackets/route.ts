import { NextResponse } from 'next/server';
import { saveBracketEdit, getAllBracketEdits, getBracketEdit } from '@/lib/db/project-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';

export async function GET() {
  const edits = getAllBracketEdits();
  return NextResponse.json({ edits });
}

export async function PUT(request: Request) {
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
  });

  return NextResponse.json({ ok: true });
}
