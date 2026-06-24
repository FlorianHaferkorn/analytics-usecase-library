/**
 * GET /api/generate?bracketId=COM-001&target=tmdl
 *
 * "Nach dem Core" generation (I-6.3): emits the chosen target through the
 * Superversion bridge and returns the artifact manifest + the Gate-Report
 * (Golden-Thread gate I-3.4 + E2E smoke I-3.5). Always 200 with the structured
 * result; `available: false` signals a transport failure for an honest banner.
 */

import { runGenerate } from '@/lib/bridge/superversion-bridge';
import { apiSuccess, apiValidationError } from '@/lib/api/response';

export async function GET(request: Request): Promise<Response> {
  const { searchParams } = new URL(request.url);
  const bracketId = searchParams.get('bracketId');
  if (!bracketId) {
    return apiValidationError(['bracketId query parameter is required']);
  }
  const target = searchParams.get('target') || 'tmdl';
  const result = await runGenerate(bracketId, target);
  return apiSuccess(result);
}
