import { NextResponse } from 'next/server';
import { loadBracket } from '@/lib/core/bracket-loader';
import { loadKpiMap } from '@/lib/core/catalog-loader';
import { buildIRPackage } from '@/lib/delivery/ir-builder';
import { generateSqlViews, generateEvidencePage } from '@/lib/delivery/oss-adapter';

export async function POST(request: Request) {
  const body = await request.json();
  const { useCaseIds } = body as { useCaseIds: string[] };

  if (!useCaseIds?.length) {
    return NextResponse.json({ error: 'No use case IDs provided' }, { status: 400 });
  }

  const kpiMap = await loadKpiMap();

  const results = [];

  for (const useCaseId of useCaseIds) {
    const bracket = await loadBracket(useCaseId);
    if (!bracket) {
      results.push({ useCaseId, error: `Bracket not found: ${useCaseId}` });
      continue;
    }

    const ir = buildIRPackage(bracket, kpiMap);
    const sqlViews = generateSqlViews(ir);
    const evidencePage = generateEvidencePage(ir);

    results.push({
      useCaseId,
      ir,
      outputs: {
        sql: sqlViews,
        evidence: evidencePage,
      },
    });
  }

  return NextResponse.json({ results });
}
