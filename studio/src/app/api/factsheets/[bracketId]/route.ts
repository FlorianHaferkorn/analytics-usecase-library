/**
 * GET /api/factsheets/[bracketId]
 *
 * Returns the parsed FactsheetSummary for a given use case ID (e.g. "COM-001").
 * Response: FactsheetSummary
 * On 404: { error: { code: 'NOT_FOUND', message: '...' } }
 */

import { NextRequest } from 'next/server';
import { requireAuth } from '@/lib/auth/session';
import { apiSuccess, apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import { loadFactsheet } from '@/lib/core/factsheet-loader';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ bracketId: string }> }
) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const { bracketId } = await params;

  if (!/^[A-Za-z0-9-]+$/.test(bracketId)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid use case ID', 400);
  }

  const factsheet = await loadFactsheet(bracketId);
  if (!factsheet) {
    return apiError(ErrorCode.NOT_FOUND, `No factsheet found for: ${bracketId}`, 404);
  }

  return apiSuccess(factsheet);
}
