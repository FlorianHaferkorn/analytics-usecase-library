import type { DeploymentPlan } from '@/lib/bridge/project-deployment';
import type { RunnerApproval, RunnerResult } from '@/lib/bridge/project-runner';

export type AcceptanceState = 'not_run' | 'review_required' | 'evidence_available' | 'out_of_scope';
export interface AcceptanceCase {
  id: string;
  title: string;
  state: AcceptanceState;
  procedure: string;
  expected: string;
  evidence: string;
}

/** Review protocol, never an attestation, approval document or execution input. */
export function buildRunnerAcceptance(projectId: string, revision: string, plan: DeploymentPlan | null,
  approval: RunnerApproval | null, result: RunnerResult | null) {
  const scopedPlan = plan?.project_ref === projectId && plan.revision_hash === revision ? plan : null;
  const scopedApproval = approval?.project_ref === projectId && approval.revision_hash === revision ? approval : null;
  const scopedResult = scopedApproval && result?.project_ref === projectId && result.revision_hash === revision
    && result.approval_id === scopedApproval.approval_id && result.plan_sha256 === scopedApproval.plan_sha256 ? result : null;
  const nonProduction = !!scopedPlan && ['dev', 'test'].includes(scopedPlan.environment);
  const oneCreate = nonProduction && scopedPlan.workspace_apply_ready && !!scopedPlan.principal_id
    && scopedPlan.operations.length === 1 && scopedPlan.operations[0].action === 'create';
  const noChange = nonProduction && scopedPlan.operations.length > 0 && scopedPlan.operations.every(row => row.action === 'noop');
  const cases: AcceptanceCase[] = [
    { id: 'scope', title: 'Authorize the non-production test', state: scopedPlan ? nonProduction && oneCreate ? 'review_required' : 'out_of_scope' : 'not_run',
      procedure: 'Agree one disposable workspace in DEV or TEST, its exact tenant, execution principal, capacity/domain assignments and recovery owner. Build the plan in Deployment preflight; obtain explicit authorization before saving its approval.',
      expected: 'The first create test contains exactly one create operation in the approved non-production scope. Production, a larger plan or an existing conflicting object requires a different reviewed test scope.',
      evidence: 'Record the authorizer, date, exact plan hash, target IDs and approved workspace name. A generated plan does not establish customer authorization.' },
    { id: 'host', title: 'Confirm host and identity prerequisites', state: 'not_run',
      procedure: 'Resolve configuration blockers above. The host administrator checks private storage ACLs, key handling, shared locks and recovery responsibility; confirm the intended identity and operation-specific permission evidence.',
      expected: 'References and dependencies are configured; operational controls are independently reviewed. Configuration checks alone never prove a usable credential or tenant permission.',
      evidence: 'Dated host review and identity/permission evidence. Do not include tokens, client secrets or signing keys.' },
    { id: 'create', title: 'Create once and verify readback', state: scopedResult?.outcome.status === 'workspace_verified' && oneCreate && scopedResult.plan_sha256 === scopedPlan?.plan_sha256 ? 'evidence_available' : scopedResult ? 'review_required' : 'not_run',
      procedure: 'For the explicitly authorized test only, save the exact plan approval and confirm execution separately. Retrieve the saved outcome and download the receipt. Compare returned workspace IDs, names and assignments with the approved plan.',
      expected: 'The signed runner outcome reports workspace_verified and matches the intended scope. A completed attempt alone is not success. Review actual tenant evidence before accepting this case.',
      evidence: 'Signed host approval, consumption and outcome records plus per-operation create/readback receipts. The Studio download is a review copy, not a replacement for signed host records.' },
    { id: 'repeat', title: 'Re-plan without duplicate creation', state: noChange ? 'review_required' : 'not_run',
      procedure: 'After verified creation, collect a fresh observation with the same trusted identity and build a new plan for the same released contract. Do not replay the consumed approval. Compare inventory with the original created IDs.',
      expected: 'Every operation is No change and the same workspace IDs remain. An uploaded no-op plan is supporting evidence only, not an independently observed live test.',
      evidence: 'Original creation IDs, fresh dated observation, new plan hash and reviewer confirmation. Keep the first signed outcome when rebuilding the plan.' },
    { id: 'recovery', title: 'Prove reload and interruption recovery', state: 'not_run',
      procedure: 'Reload Studio and retrieve the saved outcome using the scoped approval ID. Separately rehearse an interrupted attempt in an isolated host test with a fake tenant client; inspect the consumed claim and lock. Do not inject failures into a customer run.',
      expected: 'Reload does not execute again. An interrupted claim cannot be replayed and remains available for controlled reconciliation. Disable writes using the full configuration and confirm authorized evidence remains readable.',
      evidence: 'Before/after receipt IDs, request counts and isolated interruption test report. Record rehearsal evidence separately from actual tenant execution evidence.' },
    { id: 'close', title: 'Reconcile and accept the bounded result', state: 'not_run',
      procedure: 'Review scope, create/readback, repeat planning and recovery evidence. Record the acceptance owner and remaining gaps. Agree whether to retain or explicitly remove the test workspace; this runner never performs automatic cleanup.',
      expected: 'No unexplained resources or uncertain attempts remain. Acceptance covers workspace creation only, not items, data, security, stage promotion or overall project delivery.',
      evidence: 'Dated acceptance decision, evidence references and approved retention/cleanup action. No checkbox in this protocol grants deployment authority.' },
  ];
  return {
    schema_version: '1.0.0', kind: 'workspace_acceptance_review_protocol', project_ref: projectId, revision_hash: revision,
    acceptance_status: 'not_accepted', authoritative: false, tenant_actions_performed_by_protocol: false,
    scope: scopedPlan ? { tenant_id: scopedPlan.tenant_id, principal_id: scopedPlan.principal_id ?? null,
      environment: scopedPlan.environment, plan_sha256: scopedPlan.plan_sha256,
      operations: scopedPlan.operations.map(row => ({ id: row.id, name: row.desired.name, action: row.action, existing_id: row.existing_id })) } : null,
    runner_evidence_reference: scopedApproval ? { approval_id: scopedApproval.approval_id, plan_sha256: scopedApproval.plan_sha256,
      outcome_status: scopedResult?.outcome.status ?? null } : null,
    cases,
  };
}
