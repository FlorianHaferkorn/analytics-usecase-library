/**
 * Refinement Lifecycle Types — Wirkungs-Loop proposal review (ADR-0009 §5).
 *
 * Unlike bracket lifecycle (draft→review→...), proposals are derived by the
 * Python core, not authored by a human — there is no "submit" step and no
 * self-approval lock (there's no human submitter to self-approve against).
 * A proposal starts `pending_review` and ends `approved` or `rejected`.
 */

export type RefinementStatus = 'pending_review' | 'approved' | 'rejected';

export interface RefinementLifecycleRecord {
  proposal_key: string;
  project_id: string;
  action_code_id: string;
  kpi_id: string;
  status: RefinementStatus;
  trigger_kind: 'no_effect' | 'material_effect';
  rel_change: number;
  rationale: string;
  decided_by: string | null;
  justification: string | null;
  created_at: string;
  updated_at: string;
}

export type RefinementDecision = 'approve' | 'reject';

export function proposalKey(actionCodeId: string, kpiId: string): string {
  return `${actionCodeId}::${kpiId}`;
}
