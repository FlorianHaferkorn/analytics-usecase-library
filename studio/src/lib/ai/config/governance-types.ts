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

/**
 * The lifecycle actions that dispose of governance state. Each one needs admin.
 *
 * `submit` is deliberately absent: proposing a change for review is not a decision,
 * and requiring admin for it would leave nobody to propose. `reopen` IS a decision —
 * it takes an approved layer back to `draft`, and `getApprovedLayers()` stops serving
 * it the moment that happens.
 */
export const ADMIN_ACTIONS: readonly LayerAction[] = ['approve', 'reject', 'reopen'];

/** Does this action need the admin role? Accepts unvalidated input from the wire. */
export function requiresAdmin(action: string): boolean {
  return (ADMIN_ACTIONS as readonly string[]).includes(action);
}
