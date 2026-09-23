import { describe, expect, it } from 'vitest';
import { buildRunnerAcceptance } from '@/lib/project/runner-acceptance';
import type { DeploymentPlan } from '@/lib/bridge/project-deployment';
import type { RunnerApproval } from '@/lib/bridge/project-runner';

const revision = 'a'.repeat(64), planHash = 'b'.repeat(64), approvalId = 'c'.repeat(64);
const plan: DeploymentPlan = { project_ref: 'alpha', revision_hash: revision, tenant_id: 'tenant', principal_id: 'principal', environment: 'test',
  plan_sha256: planHash, workspace_apply_ready: true, whole_project_apply_ready: false,
  operations: [{ id: 'bronze', action: 'create', reason: 'Absent', desired: { name: 'alpha_bronze_test' }, existing_id: null }], capabilities: [] };
const approval: RunnerApproval = { project_ref: 'alpha', revision_hash: revision, plan_sha256: planHash, approval_id: approvalId, expires_at: '2026-09-08T14:00:00Z' };
describe('workspace acceptance review protocol', () => {
  it('starts without acceptance or implied execution and provides six actionable cases', () => {
    const protocol = buildRunnerAcceptance('alpha', revision, null, null, null);
    expect(protocol.acceptance_status).toBe('not_accepted');
    expect(protocol.authoritative).toBe(false); expect(protocol.tenant_actions_performed_by_protocol).toBe(false);
    expect(protocol.cases).toHaveLength(6);
    for (const item of protocol.cases) { expect(item.state).toBe('not_run'); expect(item.procedure.length).toBeGreaterThan(80); expect(item.evidence.length).toBeGreaterThan(40); }
  });
  it('requires review of an exact single non-production create, not auto approval', () => {
    const protocol = buildRunnerAcceptance('alpha', revision, plan, null, null);
    expect(protocol.cases[0].state).toBe('review_required'); expect(protocol.acceptance_status).toBe('not_accepted');
    expect(protocol.scope?.plan_sha256).toBe(planHash);
  });
  it.each([
    { ...plan, environment: 'prod' }, { ...plan, operations: [] }, { ...plan, operations: [...plan.operations, ...plan.operations] },
    { ...plan, workspace_apply_ready: false }, { ...plan, principal_id: undefined },
  ])('does not qualify an unsuitable first-create plan', candidate => {
    expect(buildRunnerAcceptance('alpha', revision, candidate, null, null).cases[0].state).toBe('out_of_scope');
  });
  it('ignores foreign project and revision inputs in exported context and result evidence', () => {
    const protocol = buildRunnerAcceptance('beta', revision, plan, approval, { ...approval, outcome: { status: 'workspace_verified' } });
    expect(protocol.scope).toBeNull(); expect(protocol.runner_evidence_reference).toBeNull();
    expect(protocol.cases.every(row => row.state === 'not_run')).toBe(true);
    expect(buildRunnerAcceptance('alpha', 'd'.repeat(64), plan, approval, null).scope).toBeNull();
  });
  it('reports verified runner output only as evidence requiring acceptance', () => {
    const protocol = buildRunnerAcceptance('alpha', revision, plan, approval, { ...approval, outcome: { status: 'workspace_verified' } });
    expect(protocol.cases[2].state).toBe('evidence_available'); expect(protocol.acceptance_status).toBe('not_accepted');
    expect(protocol.cases[5].state).toBe('not_run');
  });
  it.each(['completed', 'stopped_requires_reconciliation', 'drift'])('never treats outcome %s as success', status => {
    expect(buildRunnerAcceptance('alpha', revision, plan, approval, { ...approval, outcome: { status } }).cases[2].state).toBe('review_required');
  });
  it('drops mismatched outcome binding', () => {
    const protocol = buildRunnerAcceptance('alpha', revision, plan, approval, { ...approval, plan_sha256: 'd'.repeat(64), outcome: { status: 'workspace_verified' } });
    expect(protocol.cases[2].state).toBe('not_run'); expect(protocol.runner_evidence_reference?.outcome_status).toBeNull();
  });
  it('requires independent review of no-op evidence and preserves workspace IDs', () => {
    const noop: DeploymentPlan = { ...plan, operations: [{ ...plan.operations[0], action: 'noop', existing_id: 'actual-workspace-id' }] };
    const protocol = buildRunnerAcceptance('alpha', revision, noop, null, null);
    expect(protocol.cases[3].state).toBe('review_required');
    expect(protocol.scope?.operations[0].existing_id).toBe('actual-workspace-id');
  });
  it('does not transfer create proof from a different plan or production', () => {
    for (const candidate of [{ ...plan, environment: 'prod' }, { ...plan, plan_sha256: 'd'.repeat(64) }]) {
      expect(buildRunnerAcceptance('alpha', revision, candidate, approval, { ...approval, outcome: { status: 'workspace_verified' } }).cases[2].state).toBe('review_required');
    }
  });
});
