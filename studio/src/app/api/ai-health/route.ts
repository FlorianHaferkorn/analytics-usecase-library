/**
 * GET /api/ai-health?projectId=default
 *
 * AI budget/usage + ROI health metric (I-6.6 V4). Returns the local telemetry
 * summary, the ROI verdict (UNCOMPUTED unless L2 value proxies are configured),
 * and honest warnings about incomplete/unverified cost. Read-only.
 */

import { buildAiHealth } from '@/lib/ai/health';
import { apiSuccess } from '@/lib/api/response';

export async function GET(request: Request): Promise<Response> {
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get('projectId') || 'default';
  return apiSuccess(buildAiHealth({ projectId }));
}
