/**
 * governance-types — client-safe lifecycle types for AI-config layers (I-6.6, ADR-0008 §9).
 *
 * No node/DB deps, so both the server repo (`db/ai-config-repo.ts`) and the client
 * panel can import the SAME transition rules — one source of truth for "which action
 * is allowed from which status".
 */

export type LayerStatus = 'draft' | 'review' | 'approved' | 'rejected';
export type LayerAction = 'submit' | 'approve' | 'reject' | 'reopen';

export const VALID_TRANSITIONS: Record<LayerStatus, LayerAction[]> = {
  draft: ['submit'],
  review: ['approve', 'reject'],
  approved: ['reopen'],
  rejected: ['reopen'],
};

/** Allowed lifecycle actions from a given status (UI affordance + server guard share this). */
export function allowedActions(status: LayerStatus): LayerAction[] {
  return VALID_TRANSITIONS[status] ?? [];
}
