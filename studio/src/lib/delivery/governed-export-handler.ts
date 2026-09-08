/**
 * Governed export handler — the only production export seam used by Studio.
 *
 * Target mechanics stay in the Python Superversion adapters.  Studio requests
 * deterministic artifact content plus the shared gate report and packages the
 * response for download; it does not reimplement TMDL, PBIR, OSI, or Metric
 * View syntax.
 */

import { runGenerate, type GenerateResult } from '@/lib/bridge/superversion-bridge';
import { apiError, apiSuccess, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import { auditWithActor } from '@/lib/db/audit-helpers';

export type GovernedTarget = 'tmdl' | 'pbir' | 'osi' | 'databricks';

interface ExportFile {
  filename: string;
  content: string;
}

interface ExportResult {
  useCaseId: string;
  outputs?: Record<string, ExportFile[]>;
  error?: string;
}

const USE_CASE_ID = /^[A-Z]{2,3}-(?:EXT-|IND-[A-Z])?\d{3}$/;

function gateManifest(useCaseId: string, generated: GenerateResult[]): ExportFile {
  return {
    filename: `${useCaseId}/delivery-manifest.json`,
    content: `${JSON.stringify({
      useCaseId,
      outputType: 'library_preview',
      projectApproval: null,
      warning: 'Generated from the mutable library catalog, not an approved project revision. Not a project release.',
      generatedAt: new Date().toISOString(),
      targets: generated.map((result) => ({
        id: result.target,
        label: result.targetLabel,
        status: result.targetStatus,
        gate: result.gate,
        artifacts: result.artifacts.map(({ path, bytes }) => ({ path, bytes })),
      })),
    }, null, 2)}\n`,
  };
}

/** Process one or more use cases through existing governed target adapters. */
export async function processGovernedExportRequest(
  request: Request,
  targets: readonly GovernedTarget[],
  exportFormat: string,
): Promise<Response> {
  if (new URL(request.url).pathname.startsWith('/api/projects/')) {
    return apiError(ErrorCode.UNSUPPORTED, 'Project target compilation is not revision-bound yet. Use the approved Project Package input export; library generation is preview-only.', 409);
  }
  const body = await request.json() as { useCaseIds?: unknown };
  if (!Array.isArray(body.useCaseIds) || body.useCaseIds.length === 0) {
    return apiValidationError(['No use case IDs provided']);
  }
  if (body.useCaseIds.length > 20) {
    return apiValidationError(['At most 20 use cases may be packaged in one request']);
  }
  const useCaseIds = body.useCaseIds.filter((id): id is string => typeof id === 'string');
  const invalid = useCaseIds.filter((id) => !USE_CASE_ID.test(id));
  if (useCaseIds.length !== body.useCaseIds.length || invalid.length > 0) {
    return apiValidationError([`Invalid use case IDs: ${invalid.join(', ') || 'non-string value'}`]);
  }
  if (new Set(useCaseIds).size !== useCaseIds.length) {
    return apiValidationError(['Duplicate use case IDs are not allowed in one package']);
  }

  const results: ExportResult[] = [];
  // Deliberately sequential: every target executes the full governed gate.  A
  // bounded request must not fan out dozens of Python validation processes.
  for (const useCaseId of useCaseIds) {
    const generated: GenerateResult[] = [];
    for (const target of targets) {
      generated.push(await runGenerate(useCaseId, target, true));
    }
    const failed = generated.find((result) => !result.available || !result.ok);
    if (failed) {
      results.push({
        useCaseId,
        error: failed.error
          ?? `${failed.target ?? 'core'} export blocked: governed gate is not green`,
      });
      continue;
    }

    const outputs: Record<string, ExportFile[]> = {};
    let contentError: string | null = null;
    for (const result of generated) {
      const files = result.artifacts
        .filter((artifact) => typeof artifact.content === 'string')
        .map((artifact) => ({ filename: artifact.path, content: artifact.content! }));
      if (files.length !== result.artifacts.length) {
        contentError = `${result.target}: artifact content missing from core response`;
        break;
      }
      outputs[result.target ?? 'target'] = files;
    }
    if (contentError) {
      results.push({ useCaseId, error: contentError });
      continue;
    }
    outputs.manifest = [gateManifest(useCaseId, generated)];
    results.push({ useCaseId, outputs });
  }

  try {
    await auditWithActor('export', exportFormat, 'export', {
      before: null,
      after: { format: exportFormat, useCaseIds, targets, resultCount: results.length },
    });
  } catch {
    // Export truth is the core gate; an unavailable audit sink must not corrupt
    // artifacts that have already passed the deterministic delivery gate.
  }

  return apiSuccess({ results, outputType: 'library_preview', projectApproval: null });
}
