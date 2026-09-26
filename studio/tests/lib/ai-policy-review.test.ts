import { beforeEach, describe, expect, it, vi } from 'vitest';
import Database from 'better-sqlite3';
import { createHash } from 'node:crypto';
import { stringify } from 'yaml';
import type { PackageSnapshot } from '@/lib/bridge/project-package-repository';

let db: Database.Database;
vi.mock('@/lib/db/sqlite', () => ({ getDb: () => db }));
vi.mock('@/lib/db/audit-repo', () => ({ logAuditEvent: vi.fn() }));

const projectId = 'project_demo';
const revisionHash = 'a'.repeat(64);

function file(path: string, value: unknown) {
  const text = stringify(value);
  return { path, sha256: createHash('sha256').update(text).digest('hex'), size: Buffer.byteLength(text),
    encoding: 'base64' as const, contentBase64: Buffer.from(text).toString('base64') };
}

function candidateSnapshot(options: { state?: string; approval?: string; expired?: boolean; wrongHash?: boolean } = {}): PackageSnapshot {
  const route = {
    id: 'discovery_public', task_role: 'source-discovery', decision_ref: 'ai_decision',
    profile: { provider: 'local', base_url: 'http://localhost:11434', data_handling: {
      processing_boundary: 'local', boundary_evidence_ref: 'evidence://local',
      allowed_classifications: ['public'], allowed_data_forms: ['metadata'], allowed_purposes: ['studio_authoring'],
      provider_training_allowed: false, prompt_retention_days: 0, require_redaction_for_egress: false,
    } },
    allowed_inputs: [{ classification: 'public', data_form: 'metadata', purpose: 'studio_authoring', source_refs: ['evidence://source'] }],
    provider_region: 'local', provider_geography: 'local', credential_ref: null,
    provider_terms_evidence_refs: ['evidence://terms'],
    expires_at: options.expired ? '2020-01-01T00:00:00Z' : '2030-01-01T00:00:00Z',
  };
  const hashedRoute: Record<string, unknown> = { ...route };
  delete hashedRoute.decision_ref;
  const stable = (input: unknown): unknown => Array.isArray(input) ? input.map(stable)
    : input && typeof input === 'object'
      ? Object.fromEntries(Object.entries(input).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([key, value]) => [key, stable(value)]))
      : input;
  const routeHash = createHash('sha256').update(JSON.stringify(stable(hashedRoute))).digest('hex');
  const policy = { project_ref: projectId, routes: [route] };
  const decisions = {
    definitions: [{ id: 'ai_definition', adr: { affected_artifact_refs: ['discovery_public'] } }],
    instances: [{ id: 'ai_decision', definition_ref: 'ai_definition', scope_refs: ['discovery_public'],
      approval: { state: options.approval ?? 'approved', decided_at: '2026-09-01T00:00:00Z', evidence_refs: ['evidence://approval'] },
      selection: { state: 'confirmed', custom_value: `sha256:${options.wrongHash ? 'b'.repeat(64) : routeHash}` } }],
  };
  return { revision: { revision_hash: revisionHash, package_id: 'package_demo', project_ref: projectId,
    revision: 1, parent_revision_hash: null }, files: [
    file('package.yaml', { project_ref: projectId, revision: 1, state: options.state ?? 'in_review', modules: [
      { module_type: 'ai_data_handling', path: 'governance/ai.yaml' },
      { module_type: 'decision_set', path: 'discovery/decisions.yaml' },
    ] }), file('governance/ai.yaml', policy), file('discovery/decisions.yaml', decisions),
  ] };
}

beforeEach(() => {
  db = new Database(':memory:');
  db.exec(`CREATE TABLE ai_policy_reviews (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, revision_hash TEXT NOT NULL, route_id TEXT NOT NULL,
    route_hash TEXT NOT NULL, decision_ref TEXT NOT NULL, status TEXT NOT NULL, submitted_by TEXT NOT NULL,
    submitted_at TEXT NOT NULL DEFAULT (datetime('now')), reviewed_by TEXT, reviewed_at TEXT, rationale TEXT
  )`);
});

describe('separate AI policy review', () => {
  it('binds the candidate to an approved, exact-hash decision and a non-expired package revision', async () => {
    const { aiPolicyReviewCandidate } = await import('@/lib/ai/policy-review');
    const candidate = aiPolicyReviewCandidate(projectId, candidateSnapshot(), 'discovery_public');
    expect(candidate.revisionHash).toBe(revisionHash);
    expect(candidate.routeHash).toMatch(/^[a-f0-9]{64}$/);
    expect(candidate.provider).toBe('local');
    expect(() => aiPolicyReviewCandidate(projectId, candidateSnapshot({ wrongHash: true }), 'discovery_public')).toThrow(/exact route/);
    expect(() => aiPolicyReviewCandidate(projectId, candidateSnapshot({ approval: 'proposed' }), 'discovery_public')).toThrow(/not approved/);
    expect(() => aiPolicyReviewCandidate(projectId, candidateSnapshot({ expired: true }), 'discovery_public')).toThrow(/expired/);
    expect(() => aiPolicyReviewCandidate(projectId, candidateSnapshot({ state: 'working' }), 'discovery_public')).toThrow(/in review/);
  });

  it('requires a different reviewer and rejects stale or tampered candidates', async () => {
    const { aiPolicyReviewCandidate } = await import('@/lib/ai/policy-review');
    const { submitAiPolicyReview, finishAiPolicyReview, getAiPolicyReview, listAiPolicyReviews } = await import('@/lib/db/ai-policy-review-repo');
    const candidate = aiPolicyReviewCandidate(projectId, candidateSnapshot(), 'discovery_public');
    const review = submitAiPolicyReview(candidate, 'author@example.com');
    expect(review.status).toBe('pending');
    expect(getAiPolicyReview('other_project', review.id)).toBeNull();
    expect(() => finishAiPolicyReview('other_project', review.id, 'approve', 'reviewer@example.com', 'A sufficiently long rationale.', candidate)).toThrow(/Pending/);
    expect(() => submitAiPolicyReview(candidate, 'author@example.com')).toThrow(/already/);
    expect(() => finishAiPolicyReview(projectId, review.id, 'approve', 'AUTHOR@example.com', 'A sufficiently long rationale.', candidate)).toThrow(/second person/);
    expect(() => finishAiPolicyReview(projectId, review.id, 'approve', 'reviewer@example.com', 'A sufficiently long rationale.',
      { ...candidate, routeHash: 'b'.repeat(64) })).toThrow(/changed/);
    expect(finishAiPolicyReview(projectId, review.id, 'approve', 'reviewer@example.com', 'A sufficiently long rationale.', candidate).status).toBe('approved');
    expect(listAiPolicyReviews(projectId)).toHaveLength(1);
    expect(() => finishAiPolicyReview(projectId, review.id, 'approve', 'reviewer@example.com', 'Again.', candidate)).toThrow(/Pending/);
  });

  it('permits a new review only after a rejection', async () => {
    const { aiPolicyReviewCandidate } = await import('@/lib/ai/policy-review');
    const { submitAiPolicyReview, finishAiPolicyReview } = await import('@/lib/db/ai-policy-review-repo');
    const candidate = aiPolicyReviewCandidate(projectId, candidateSnapshot(), 'discovery_public');
    const first = submitAiPolicyReview(candidate, 'author@example.com');
    finishAiPolicyReview(projectId, first.id, 'reject', 'reviewer@example.com', 'The provider terms are insufficient.');
    expect(submitAiPolicyReview(candidate, 'author@example.com').id).not.toBe(first.id);
  });
});
