import { buildAiEgressEvidence, persistAiEgressEvidence } from './egress-preflight';

export interface AiEgressGateInput {
  projectId?: string;
  actor?: string;
  taskRole?: string;
  payload?: unknown;
  profile?: Record<string, unknown>;
  context?: Record<string, unknown>;
}

/** Default-deny approval gate with scanner and tamper-evident, content-free audit. */
export function requireApprovedAiEgress(input: AiEgressGateInput = {}): Response | null {
  const projectId = input.projectId ?? 'default';
  const message = input.projectId
    ? 'AI processing is paused for this project until its data-handling contract and outbound-content checks are approved. Saved evidence remains available.'
    : 'AI processing is paused on this projectless endpoint. Use a governed project workflow after its data-handling contract is approved.';
  const profile = input.profile ?? {
    provider: 'unresolved', model: '',
    data_handling: {
      processing_boundary: 'external_cloud',
      allowed_classifications: ['public', 'internal_generic'],
      allowed_data_forms: ['metadata', 'aggregates', 'schema', 'code', 'document_excerpt', 'raw_rows', 'synthetic'],
      allowed_purposes: ['studio_authoring', 'enduser_question', 'analytics_reasoning', 'analytics_advisory'],
      provider_training_allowed: false, prompt_retention_days: 0,
      require_redaction_for_egress: true,
    },
  };
  const context = input.context ?? {
    classification: 'unknown', data_form: 'metadata', purpose: 'studio_authoring', redacted: false,
  };
  const evidence = buildAiEgressEvidence({
    profile, context,
    payload: input.payload ?? { missing_payload: true, task_role: input.taskRole ?? 'unknown' },
    approvalGranted: false,
  });
  try {
    persistAiEgressEvidence(evidence, projectId, input.actor ?? 'system');
  } catch {
    return Response.json(
      { error: 'AI processing is paused because the security evidence could not be persisted.', code: 'AI_EGRESS_AUDIT_FAILED' },
      { status: 503 },
    );
  }
  return Response.json(
    { error: message, code: 'AI_EGRESS_NOT_APPROVED', evidenceId: evidence.event_id },
    { status: 403 },
  );
}
