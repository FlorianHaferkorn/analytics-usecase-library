/**
 * delivery-flow — the customer-without-builder E2E flow (I-6.4).
 *
 * Chains the pieces that already exist into one journey and encodes the single
 * guarantee that makes the cockpit safe for a non-builder to operate:
 *
 *   Authoring → Freigabe-Schleuse → Generate → Validate → Deliverable
 *
 * A deliverable may be handed off **only** when the bracket is approved
 * (Freigabe-Schleuse) AND the governed gate is green (Generate/Validate, ADR-0007).
 * This module is pure: it derives the flow state from inputs the route assembles
 * (bracket existence, approval status, the bridge GenerateResult); it performs no
 * I/O and runs nothing, so it is trivially testable and deterministic.
 */

import type { ApprovalStatus } from '@/lib/governance/approval-types';
import type { GenerateResult } from '@/lib/bridge/superversion-bridge';

export type FlowStepStatus = 'done' | 'current' | 'blocked' | 'pending';

export interface FlowStep {
  key: 'authoring' | 'approval' | 'generate' | 'validate' | 'deliverable';
  label: string;
  status: FlowStepStatus;
  detail: string;
}

export interface DeliveryFlowState {
  bracketId: string;
  steps: FlowStep[];
  /** True only when approved AND gate-green AND artifacts present. */
  canHandoff: boolean;
  /** First reason the handoff is blocked (null when canHandoff). */
  blockedReason: string | null;
}

export interface DeliveryFlowInputs {
  bracketId: string;
  bracketExists: boolean;
  approval: ApprovalStatus | null;
  /** The bridge result, or null when generation has not been run yet. */
  generate: GenerateResult | null;
}

function approvalStep(approval: ApprovalStatus | null): FlowStep {
  const base = { key: 'approval' as const, label: 'Freigabe-Schleuse' };
  switch (approval) {
    case 'approved':
      return { ...base, status: 'done', detail: 'freigegeben' };
    case 'review':
      return { ...base, status: 'current', detail: 'in Review — wartet auf Freigabe' };
    case 'rejected':
      return { ...base, status: 'blocked', detail: 'abgelehnt — überarbeiten und erneut einreichen' };
    case 'deprecated':
      return { ...base, status: 'blocked', detail: 'deprecated — reopen nötig' };
    case 'draft':
    case null:
    default:
      return { ...base, status: 'pending', detail: 'Entwurf — zur Review einreichen' };
  }
}

export function computeDeliveryFlow(inputs: DeliveryFlowInputs): DeliveryFlowState {
  const { bracketId, bracketExists, approval, generate } = inputs;
  const gateOk = generate?.available === true && generate.gate?.ok === true;
  const hasArtifacts = (generate?.artifacts?.length ?? 0) > 0;

  const authoring: FlowStep = bracketExists
    ? { key: 'authoring', label: 'Authoring', status: 'done', detail: `Bracket ${bracketId}` }
    : { key: 'authoring', label: 'Authoring', status: 'blocked', detail: `Bracket ${bracketId} fehlt` };

  const approvalS = approvalStep(approval);

  let generateS: FlowStep;
  if (!generate) {
    generateS = { key: 'generate', label: 'Generate', status: 'pending', detail: 'noch nicht ausgeführt' };
  } else if (!generate.available) {
    generateS = { key: 'generate', label: 'Generate', status: 'blocked', detail: generate.error || 'Bridge offline' };
  } else if (!hasArtifacts) {
    generateS = { key: 'generate', label: 'Generate', status: 'blocked', detail: 'keine Artefakte erzeugt' };
  } else {
    generateS = { key: 'generate', label: 'Generate', status: 'done', detail: `${generate.artifacts.length} Artefakt(e) · ${generate.target}` };
  }

  let validateS: FlowStep;
  if (!generate || !generate.available) {
    validateS = { key: 'validate', label: 'Validate (Gate)', status: 'pending', detail: 'Gate noch nicht gelaufen' };
  } else if (gateOk) {
    validateS = { key: 'validate', label: 'Validate (Gate)', status: 'done', detail: 'Gate grün — gate-validiert' };
  } else {
    const failed = generate.gate?.stages.filter((s) => s.status === 'FAIL').map((s) => s.name) ?? [];
    validateS = { key: 'validate', label: 'Validate (Gate)', status: 'blocked', detail: failed.length ? `Gate rot: ${failed.join(', ')}` : 'Gate rot' };
  }

  // Deliverable gate — the I-6.4 guarantee.
  let blockedReason: string | null = null;
  if (!bracketExists) blockedReason = 'Kein Bracket (Authoring offen)';
  else if (approval !== 'approved') blockedReason = 'Nicht freigegeben (Freigabe-Schleuse offen)';
  else if (!generate || !generate.available) blockedReason = 'Generierung nicht gelaufen';
  else if (!hasArtifacts) blockedReason = 'Keine Artefakte erzeugt';
  else if (!gateOk) blockedReason = 'Gate rot — nicht gate-validiert';

  const canHandoff = blockedReason === null;
  const deliverable: FlowStep = canHandoff
    ? { key: 'deliverable', label: 'Deliverable', status: 'done', detail: 'bereit zum Deploy-Handoff' }
    : { key: 'deliverable', label: 'Deliverable', status: 'blocked', detail: blockedReason! };

  return {
    bracketId,
    steps: [authoring, approvalS, generateS, validateS, deliverable],
    canHandoff,
    blockedReason,
  };
}
