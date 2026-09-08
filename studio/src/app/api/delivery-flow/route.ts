/**
 * GET /api/delivery-flow?bracketId=COM-001&target=tmdl
 *
 * The customer-without-builder E2E flow (I-6.4): assembles the existing pieces —
 * bracket existence (Authoring), approval lifecycle (Freigabe-Schleuse), and the
 * governed Generate/Gate bridge — into one flow state. The deliverable can be
 * handed off only when approved AND gate-green; the response says exactly which
 * step blocks, so a non-builder can drive the journey.
 */

import { computeDeliveryFlow } from '@/lib/studio/delivery-flow';
import { getLifecycle } from '@/lib/governance/approval-workflow';
import { resolveBridgeBracket, runGenerate } from '@/lib/bridge/superversion-bridge';
import { apiSuccess, apiValidationError } from '@/lib/api/response';

export async function GET(request: Request): Promise<Response> {
  const { searchParams } = new URL(request.url);
  const bracketId = searchParams.get('bracketId');
  if (!bracketId) {
    return apiValidationError(['bracketId query parameter is required']);
  }
  const target = searchParams.get('target') || 'tmdl';
  const projectId = searchParams.get('projectId') ?? 'default';

  const bracketResolution = await resolveBridgeBracket(bracketId);
  const bracketExists = bracketResolution.available && bracketResolution.exists;
  const approval = bracketExists ? getLifecycle(bracketId, projectId).status : null;
  // Only run the (subprocess) gate once the bracket is approved — no point
  // generating a deliverable the Freigabe-Schleuse has not cleared.
  const generate = approval === 'approved' ? await runGenerate(bracketId, target) : null;

  return apiSuccess({
    ...computeDeliveryFlow({ bracketId, bracketExists, approval, generate }),
    bracketResolution,
  });
}
