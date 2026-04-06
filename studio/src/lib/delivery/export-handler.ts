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
import { auditWithActor } from '@/lib/db/audit-helpers';
import { apiSuccess, apiValidationError } from '@/lib/api/response';

export interface ExportResult {
  useCaseId: string;
  ir?: IRPackage;
  outputs?: Record<string, unknown>;
  error?: string;
}

type AdapterFn = (ir: IRPackage) => Record<string, unknown>;

/** Process an export request: load brackets, build IR, apply adapter, log audit. */
export async function processExportRequest(
  request: Request,
  adapter: AdapterFn,
  exportFormat = 'generic',
): Promise<NextResponse> {
  const body = await request.json();
  const { useCaseIds } = body as { useCaseIds: string[] };

  if (!useCaseIds?.length) {
    return apiValidationError(['No use case IDs provided']);
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

  // Log audit event for the export (non-fatal)
  try {
    await auditWithActor('export', exportFormat, 'export', {
      before: null,
      after: { format: exportFormat, useCaseIds, resultCount: results.length },
    });
  } catch {
    // Audit failure must not block export delivery
  }

  return apiSuccess({ results });
}
