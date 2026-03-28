/**
 * Shared export handler — processes use case IDs through the IR pipeline.
 *
 * Both Fabric and OSS export routes share the same loading/iteration logic.
 * Only the adapter-specific generation differs.
 */

import { NextResponse } from 'next/server';
import { loadBracket } from '@/lib/core/bracket-loader';
import { loadKpiMap } from '@/lib/core/catalog-loader';
import { buildIRPackage, type IRPackage } from '@/lib/delivery/ir-builder';

export interface ExportResult {
  useCaseId: string;
  ir?: IRPackage;
  outputs?: Record<string, unknown>;
  error?: string;
}

type AdapterFn = (ir: IRPackage) => Record<string, unknown>;

/** Process an export request: load brackets, build IR, apply adapter. */
export async function processExportRequest(
  request: Request,
  adapter: AdapterFn
): Promise<NextResponse> {
  const body = await request.json();
  const { useCaseIds } = body as { useCaseIds: string[] };

  if (!useCaseIds?.length) {
    return NextResponse.json({ error: 'No use case IDs provided' }, { status: 400 });
  }

  const kpiMap = await loadKpiMap();

  const results: ExportResult[] = await Promise.all(
    useCaseIds.map(async (useCaseId) => {
      const bracket = await loadBracket(useCaseId);
      if (!bracket) {
        return { useCaseId, error: `Bracket not found: ${useCaseId}` };
      }

      const ir = buildIRPackage(bracket, kpiMap);
      const outputs = adapter(ir);

      return { useCaseId, ir, outputs };
    })
  );

  return NextResponse.json({ results });
}
