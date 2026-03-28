import { NextResponse } from 'next/server';
import { saveBracketEdit, getAllBracketEdits } from '@/lib/db/project-repo';

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

  saveBracketEdit(bracketId, yamlContent);
  return NextResponse.json({ ok: true });
}
