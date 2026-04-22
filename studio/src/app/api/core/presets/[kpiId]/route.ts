/**
 * GET /api/core/presets/[kpiId]
 *
 * Loads the ROI preset YAML for a Golden-20 KPI from
 * core/templates/business_case/presets/<kpiId>.yaml
 *
 * Returns 200 { preset } or 404 if no preset exists for that KPI.
 */

import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { parse } from 'yaml';
import { apiSuccess, apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

const PRESETS_DIR = join(process.cwd(), '..', 'core', 'templates', 'business_case', 'presets');

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ kpiId: string }> }
) {
  const { kpiId } = await params;

  // Sanitise: only allow kpi_id characters (alphanumeric, dot, underscore)
  if (!/^[\w.]+$/.test(kpiId)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid kpiId', 400);
  }

  const filePath = join(PRESETS_DIR, `${kpiId}.yaml`);

  try {
    const raw = await readFile(filePath, 'utf-8');
    const preset = parse(raw) as Record<string, unknown>;
    return apiSuccess({ preset });
  } catch {
    return apiError(ErrorCode.NOT_FOUND, `No ROI preset found for KPI: ${kpiId}`, 404);
  }
}
