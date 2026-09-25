import 'server-only';
import { createHash } from 'node:crypto';
import type { PackageSnapshot } from '@/lib/bridge/project-package-repository';
import { projectProjection } from '@/lib/project-package/projection';

type JsonObject = Record<string, unknown>;

function object(value: unknown): JsonObject {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid AI policy review input.');
  return value as JsonObject;
}

function canonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') {
    const source = value as JsonObject;
    return Object.fromEntries(Object.keys(source).sort().map((key) => [key, canonical(source[key])]));
  }
  return value;
}

export interface AiPolicyReviewCandidate {
  projectId: string;
  revisionHash: string;
  routeId: string;
  routeHash: string;
  decisionRef: string;
  provider: string;
  processingBoundary: string;
  providerRegion: string;
  providerGeography: string;
  allowedInputs: unknown[];
  evidenceRefs: string[];
  expiresAt: string;
}

/** A reviewable, immutable package candidate; not a model-egress authorization. */
export function aiPolicyReviewCandidate(
  projectId: string,
  snapshot: PackageSnapshot,
  routeId: string,
  now = new Date(),
): AiPolicyReviewCandidate {
  const projection = projectProjection(projectId, snapshot);
  if (!['in_review', 'approved'].includes(projection.state)) throw new Error('Project Package must be in review or approved.');
  const policyModules = projection.modules.filter((entry) => entry.type === 'ai_data_handling');
  const decisionModules = projection.modules.filter((entry) => entry.type === 'decision_set');
  if (policyModules.length !== 1 || decisionModules.length !== 1) throw new Error('One AI policy and one decision set are required.');
  const policy = policyModules[0].data;
  if (policy.project_ref !== projectId || !Array.isArray(policy.routes)) throw new Error('AI policy project mismatch.');
  const routes = policy.routes.map(object);
  const route = routes.find((entry) => entry.id === routeId);
  if (!route || routes.filter((entry) => entry.id === routeId).length !== 1) throw new Error('Unique AI policy route not found.');
  const decisions = decisionModules[0].data;
  if (!Array.isArray(decisions.instances) || !Array.isArray(decisions.definitions)) throw new Error('Decision set is incomplete.');
  const decision = decisions.instances.map(object).find((entry) => entry.id === route.decision_ref);
  if (!decision) throw new Error('AI policy decision not found.');
  const definition = decisions.definitions.map(object).find((entry) => entry.id === decision.definition_ref);
  const adr = object(definition?.adr);
  if (!Array.isArray(decision.scope_refs) || !decision.scope_refs.includes(routeId)
    || !Array.isArray(adr.affected_artifact_refs) || !adr.affected_artifact_refs.includes(routeId)) {
    throw new Error('AI policy route is not in the decision and ADR scope.');
  }
  const approval = object(decision.approval);
  const selection = object(decision.selection);
  const hashedRoute = { ...route };
  delete hashedRoute.decision_ref;
  const routeHash = createHash('sha256').update(JSON.stringify(canonical(hashedRoute))).digest('hex');
  if (approval.state !== 'approved' || selection.state !== 'confirmed'
    || selection.custom_value !== `sha256:${routeHash}` || !approval.decided_at
    || !Array.isArray(approval.evidence_refs) || approval.evidence_refs.length === 0) {
    throw new Error('AI policy decision is not approved for this exact route.');
  }
  const profile = object(route.profile);
  const handling = object(profile.data_handling);
  const expiresAt = route.expires_at;
  if (typeof expiresAt !== 'string' || !Number.isFinite(Date.parse(expiresAt)) || Date.parse(expiresAt) <= now.getTime()) {
    throw new Error('AI policy review candidate has expired.');
  }
  if (typeof route.provider_region !== 'string' || !route.provider_region.trim()
    || typeof route.provider_geography !== 'string' || !route.provider_geography.trim()
    || !Array.isArray(route.provider_terms_evidence_refs) || route.provider_terms_evidence_refs.length === 0
    || !Array.isArray(route.allowed_inputs) || route.allowed_inputs.length === 0) {
    throw new Error('AI policy candidate lacks provider or input evidence.');
  }
  return {
    projectId,
    revisionHash: snapshot.revision.revision_hash,
    routeId,
    routeHash,
    decisionRef: String(route.decision_ref),
    provider: String(profile.provider),
    processingBoundary: String(handling.processing_boundary),
    providerRegion: route.provider_region,
    providerGeography: route.provider_geography,
    allowedInputs: route.allowed_inputs,
    evidenceRefs: [...approval.evidence_refs, ...route.provider_terms_evidence_refs] as string[],
    expiresAt,
  };
}
