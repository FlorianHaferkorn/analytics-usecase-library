import { NextResponse } from 'next/server';
import { loadBracket } from '@/lib/core/bracket-loader';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { buildIRPackage } from '@/lib/delivery/ir-builder';
import { generateTmdlMeasures, generatePbipLayout } from '@/lib/delivery/fabric-adapter';

export async function POST(request: Request) {
  const body = await request.json();
  const { useCaseIds } = body as { useCaseIds: string[] };

  if (!useCaseIds?.length) {
    return NextResponse.json({ error: 'No use case IDs provided' }, { status: 400 });
  }

  const kpis = await loadKpiCatalog();
  const kpiMap = new Map(kpis.map((k) => [k.kpi_id, k]));

  const results = [];

  for (const useCaseId of useCaseIds) {
    const bracket = await loadBracket(useCaseId);
    if (!bracket) {
      results.push({ useCaseId, error: `Bracket not found: ${useCaseId}` });
      continue;
    }

    const ir = buildIRPackage(bracket, kpiMap);
    const tmdlFiles = generateTmdlMeasures(ir);
    const pbipLayout = generatePbipLayout(ir);

    results.push({
      useCaseId,
      ir,
      outputs: {
        tmdl: tmdlFiles,
        pbip: pbipLayout,
      },
    });
  }

  return NextResponse.json({ results });
}
