/**
 * GET /api/precore?bracketId=COM-001
 *
 * "Vor dem Core" reality check (I-6.2): runs the governed gov/eng/arch engines
 * against a bracket through the Superversion bridge (ADR-0007). Always returns
 * 200 with the structured result — `available: false` signals a transport
 * failure so the UI can render an honest "not gate-validated" banner rather than
 * a fabricated empty pass.
 */

import { runPreCore } from '@/lib/bridge/superversion-bridge';
import { apiSuccess, apiValidationError } from '@/lib/api/response';

export async function GET(request: Request): Promise<Response> {
  const { searchParams } = new URL(request.url);
  const bracketId = searchParams.get('bracketId');
  if (!bracketId) {
    return apiValidationError(['bracketId query parameter is required']);
  }
  const result = await runPreCore(bracketId);
  return apiSuccess(result);
}
