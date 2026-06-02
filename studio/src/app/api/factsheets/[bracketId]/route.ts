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
import { loadFactsheet, loadFactsheetMarkdown, saveFactsheetMarkdown } from '@/lib/core/factsheet-loader';
import { logAuditEvent } from '@/lib/db/audit-repo';

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

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ bracketId: string }> }
) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const { bracketId } = await params;
  if (!/^[A-Za-z0-9-]+$/.test(bracketId)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid use case ID', 400);
  }

  let markdown: string;
  try {
    const body = (await request.json()) as { markdown?: unknown };
    if (typeof body.markdown !== 'string' || body.markdown.trim().length === 0) {
      return apiError(ErrorCode.VALIDATION_ERROR, 'Body must contain non-empty "markdown"', 400);
    }
    markdown = body.markdown;
  } catch {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid JSON body', 400);
  }

  const before = await loadFactsheetMarkdown(bracketId);
  if (before === null) {
    return apiError(ErrorCode.NOT_FOUND, `No factsheet found for: ${bracketId}`, 404);
  }

  const saved = await saveFactsheetMarkdown(bracketId, markdown);
  if (!saved) {
    return apiError(ErrorCode.NOT_FOUND, `Could not save factsheet: ${bracketId}`, 404);
  }

  logAuditEvent(
    'factsheet',
    bracketId,
    'update',
    {
      before: { length: before.length },
      after: { length: markdown.length },
    },
    'default',
    user!.email,
  );

  return apiSuccess({ saved: true, id: bracketId });
}
