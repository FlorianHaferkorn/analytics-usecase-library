/**
 * Wirkungs-Loop Attribution API — compute AttributionRecords + RefinementProposals
 * via the Python bridge (I-8.2/I-8.3, ADR-0009 §5, Studio-Approval-Verdrahtung).
 *
 * POST { useCase, actionCodeId, t1, method?, controlT0?, controlT1? }
 *
 * Read-only against the governed core, but persists any freshly-derived
 * proposal as `pending_review` so the approve/reject endpoint has something to
 * decide against — never mutates the core itself (ADR-0009 "kein Auto-Mutate").
 */

import { requireRole } from '@/lib/auth/require-role';
import { runAttribute } from '@/lib/bridge/superversion-bridge';
import { upsertPendingProposal, getRefinement } from '@/lib/governance/refinement-workflow';
import { proposalKey } from '@/lib/governance/refinement-types';
import { apiSuccess, apiValidationError } from '@/lib/api/response';

export async function POST(request: Request) {
  // 'editor', not 'viewer': this persists (upserts pending refinement-lifecycle rows),
  // even though nothing reaches 'approved' without a separate admin decision.
  const [, authErr] = await requireRole('editor');
  if (authErr) return authErr;

  const body = await request.json() as {
    useCase?: string;
    actionCodeId?: string;
    t1?: Record<string, number>;
    method?: 'before_after' | 'diff_in_diff' | 'holdout';
    controlT0?: Record<string, number>;
    controlT1?: Record<string, number>;
  };

  if (!body.useCase || !body.actionCodeId || !body.t1) {
    return apiValidationError(['useCase, actionCodeId and t1 required']);
  }

  const result = await runAttribute(body.useCase, body.actionCodeId, body.t1, {
    method: body.method,
    controlT0: body.controlT0,
    controlT1: body.controlT1,
  });

  const refinements = result.refinements.map((p) => {
    upsertPendingProposal({
      actionCodeId: p.actionCodeId,
      kpiId: p.kpiId,
      triggerKind: p.trigger,
      relChange: p.relChange,
      rationale: p.rationale,
    });
    return {
      ...p,
      lifecycle: getRefinement(proposalKey(p.actionCodeId, p.kpiId)),
    };
  });

  return apiSuccess({ ...result, refinements });
}
