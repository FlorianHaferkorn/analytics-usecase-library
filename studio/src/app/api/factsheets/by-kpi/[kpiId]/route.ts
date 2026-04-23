/**
 * GET /api/factsheets/by-kpi/[kpiId]
 *
 * Finds which factsheet references a given KPI ID and with what role.
 * Response: { factsheet: FactsheetSummary; role: string }
 * On 404: { error: { code: 'NOT_FOUND', message: '...' } }
 */

import { NextRequest } from 'next/server';
import { requireAuth } from '@/lib/auth/session';
import { apiSuccess, apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import { getFactsheetForKpi } from '@/lib/core/factsheet-loader';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ kpiId: string }> }
) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const { kpiId } = await params;
  const decodedKpiId = decodeURIComponent(kpiId);

  const result = await getFactsheetForKpi(decodedKpiId);
  if (!result) {
    return apiError(ErrorCode.NOT_FOUND, `No factsheet found referencing KPI: ${decodedKpiId}`, 404);
  }

  return apiSuccess(result);
}
