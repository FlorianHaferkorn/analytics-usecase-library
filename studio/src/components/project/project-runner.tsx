'use client';
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { StudioButton, StudioPanel } from '@/components/ui/studio-page';
import { useProjectStore } from '@/lib/store/project-store';
import type { DeploymentPlan } from '@/lib/bridge/project-deployment';
import type { RunnerApproval, RunnerCheck, RunnerEvidence, RunnerResult, RunnerStatus } from '@/lib/bridge/project-runner';
import { ProjectRunnerReadiness } from './project-runner-readiness';
import { ProjectRunnerAcceptance } from './project-runner-acceptance';
import { EvidenceLabel } from './evidence-label';
import styles from './project-automation.module.css';

const errorText = (value: { error?: string | { message?: string } }, fallback: string) => typeof value.error === 'string' ? value.error : value.error?.message ?? fallback;

export function ProjectRunner({ projectId, revision, plan, children }: { projectId: string; revision: string; plan: DeploymentPlan | null; children?: ReactNode }) {
  const [status, setStatus] = useState<RunnerStatus | null>(null);
  const [error, setError] = useState('');
  const [accessError, setAccessError] = useState('');
  const [checking, setChecking] = useState(true);
  const [checks, setChecks] = useState<RunnerCheck[]>([]);
  const [checkedAt, setCheckedAt] = useState<string>();
  const [attempt, setAttempt] = useState(0);
  const [rationale, setRationale] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [executeConfirmed, setExecuteConfirmed] = useState(false);
  const [approval, setApproval] = useState<RunnerApproval | null>(null);
  const [lookup, setLookup] = useState('');
  const [busy, setBusy] = useState(false);
  const [attempted, setAttempted] = useState(false);
  const [result, setResult] = useState<RunnerResult | null>(null);
  const [evidenceState, setEvidenceState] = useState('');
  const [now, setNow] = useState(Date.now());
  const mounted = useRef(true);
  const requestSequence = useRef(0);
  // Invalidate intent without remounting the planning form or losing input focus.
  useLayoutEffect(() => {
    requestSequence.current += 1;
    setApproval(null); setResult(null); setConfirmed(false); setExecuteConfirmed(false);
    setRationale(''); setAttempted(false); setEvidenceState(''); setBusy(false); setError('');
  }, [plan?.plan_sha256]);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; requestSequence.current += 1; }; }, []);
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, []);
  useEffect(() => {
    const query = new URL(window.location.href).searchParams;
    const saved = query.get('runner_approval');
    if (query.get('runner_project') === projectId && query.get('runner_revision') === revision && saved && /^[a-f0-9]{64}$/.test(saved)) setLookup(saved);
  }, [projectId, revision]);
  function remember(receipt: RunnerApproval) {
    // Opaque IDs are not bearer credentials. Protected evidence still requires
    // OAuth, project-admin access, an exact actor policy and signature checks.
    const url = new URL(window.location.href);
    url.searchParams.set('runner_project', receipt.project_ref);
    url.searchParams.set('runner_revision', receipt.revision_hash);
    url.searchParams.set('runner_approval', receipt.approval_id);
    window.history.replaceState(window.history.state, '', url);
  }
  const current = () => {
    const selected = useProjectStore.getState();
    return mounted.current && selected.projectId === projectId && selected.packageRevisionHash === revision;
  };
  useEffect(() => {
    const controller = new AbortController();
    setStatus(null); setAccessError(''); setChecking(true); setChecks([]); setCheckedAt(undefined);
    void fetch(`/api/projects/${encodeURIComponent(projectId)}/runner?revision=${revision}`, { cache: 'no-store', signal: controller.signal })
      .then(async response => {
        const value = await response.json();
        if (!controller.signal.aborted) { setChecks(Array.isArray(value.checks) ? value.checks : []); setCheckedAt(value.checked_at); }
        if (!response.ok) throw new Error(errorText(value, 'Runner status unavailable'));
        if (value.project_ref !== projectId) throw new Error('Runner project mismatch');
        if (!controller.signal.aborted) setStatus(value as RunnerStatus);
      }).catch(reason => { if (!controller.signal.aborted) setAccessError(reason instanceof Error ? reason.message : 'Runner unavailable'); })
      .finally(() => { if (!controller.signal.aborted) setChecking(false); });
    return () => controller.abort();
  }, [projectId, revision, attempt]);

  const matches = Boolean(approval && plan && approval.plan_sha256 === plan.plan_sha256 && approval.project_ref === projectId && approval.revision_hash === revision);
  const expired = Boolean(approval && (!Number.isFinite(Date.parse(approval.expires_at)) || Date.parse(approval.expires_at) <= now));
  // Approval and execution have separate actor allowlists. A missing permission
  // for the other role must not override the server's action-specific decision.
  const prerequisitesMet = !checking;
  const canApprove = prerequisitesMet && status?.enabled && status.can_approve && plan?.workspace_apply_ready && plan.principal_id && confirmed && rationale.trim().length >= 20 && !busy;
  const canExecute = prerequisitesMet && status?.enabled && status.can_execute && status.identity_broker_available && matches && !expired && !attempted && executeConfirmed && !busy;

  async function approve() {
    if (!canApprove || !current()) return;
    const sequence = ++requestSequence.current;
    setBusy(true); setError(''); setApproval(null); setExecuteConfirmed(false); setResult(null); setEvidenceState('');
    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/runner`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'approve', revisionHash: revision, plan, rationale: rationale.trim(), confirmed: true }) });
      const value = await response.json();
      if (!response.ok) throw new Error(errorText(value, 'Approval outcome is uncertain; inspect saved records before retrying.'));
      if (value.project_ref !== projectId || value.revision_hash !== revision || value.plan_sha256 !== plan?.plan_sha256 || !/^[a-f0-9]{64}$/.test(value.approval_id)) throw new Error('Approval identity mismatch');
      if (current() && sequence === requestSequence.current) { remember(value); setApproval(value); setLookup(value.approval_id); setAttempted(false); setConfirmed(false); }
    } catch (reason) { if (current() && sequence === requestSequence.current) setError(reason instanceof Error ? reason.message : 'Approval failed'); }
    finally { if (current() && sequence === requestSequence.current) setBusy(false); }
  }
  async function execute() {
    if (!canExecute || !approval || !current()) return;
    const sequence = ++requestSequence.current;
    setBusy(true); setError(''); setAttempted(true); setExecuteConfirmed(false);
    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/runner`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'execute', revisionHash: revision, approvalId: approval.approval_id, confirmed: true }) });
      const value = await response.json();
      if (!response.ok) throw new Error(errorText(value, 'Execution outcome is uncertain. Retrieve evidence; do not retry.'));
      if (value.project_ref !== projectId || value.revision_hash !== revision || value.approval_id !== approval.approval_id || value.plan_sha256 !== approval.plan_sha256) throw new Error('Execution identity mismatch; retrieve saved evidence before continuing.');
      if (current() && sequence === requestSequence.current) { setResult(value); setEvidenceState('completed'); }
    } catch (reason) { if (current() && sequence === requestSequence.current) setError(reason instanceof Error ? reason.message : 'Execution outcome uncertain; retrieve saved evidence.'); }
    finally { if (current() && sequence === requestSequence.current) setBusy(false); }
  }
  async function retrieve() {
    if (!/^[a-f0-9]{64}$/.test(lookup) || busy || !current()) return;
    const sequence = ++requestSequence.current;
    setBusy(true); setError(''); setExecuteConfirmed(false); setApproval(null); setResult(null);
    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/runner?revision=${revision}&approval=${lookup}`, { cache: 'no-store' });
      const value = await response.json() as RunnerEvidence & { error?: string };
      if (!response.ok) throw new Error(errorText(value, 'Saved evidence unavailable'));
      if (value.receipt?.project_ref !== projectId || value.receipt.revision_hash !== revision || value.receipt.approval_id !== lookup) throw new Error('Saved evidence identity mismatch');
      if (current() && sequence === requestSequence.current) { remember(value.receipt); setApproval(value.receipt); setResult(value.result ?? null); setEvidenceState(value.status); setAttempted(value.status !== 'approved_not_executed'); }
    } catch (reason) { if (current() && sequence === requestSequence.current) setError(reason instanceof Error ? reason.message : 'Evidence unavailable'); }
    finally { if (current() && sequence === requestSequence.current) setBusy(false); }
  }
  function download() {
    if (!approval) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify({ approval, result, evidenceState }, null, 2)], { type: 'application/json' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${projectId}-workspace-approval-${approval.approval_id}.json`; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <>
    <ProjectRunnerReadiness checks={checks} loading={checking} checkedAt={checkedAt} unavailable={!!accessError} busy={busy} refresh={() => setAttempt(n => n + 1)} />
    {accessError && <p role="alert">{accessError}</p>}
    {children}
    <StudioPanel title="Protected workspace execution" compactHeader description="Separate plan approval from execution. This runner creates workspaces only; it does not deploy items, data, security or CI/CD.">
    <p className={styles.note}>{status ? status.enabled ? 'Host policy is enabled. This does not prove tenant access; the runner checks identity and fresh inventory before writing.' : 'Live execution is disabled. An administrator must configure the protected host, identity broker and exact target policy.' : 'Checking protected host access. A supported OAuth session and project-admin membership are required.'}</p>
    {error && <p role="alert">{error}</p>}
    {status?.enabled && status.can_approve && plan && <>
      <dl className={styles.facts}><dt>Tenant</dt><dd>{plan.tenant_id}</dd><dt>Environment</dt><dd>{plan.environment}</dd><dt>Execution identity</dt><dd>{plan.principal_id ?? 'Not recorded'}</dd><dt>Plan SHA-256</dt><dd>{plan.plan_sha256}</dd></dl>
      <div className={styles.inputs}><label>Workspace approval rationale<input value={rationale} maxLength={2000} disabled={busy} onChange={event => { setRationale(event.target.value); setConfirmed(false); }} /></label></div>
      <label className={styles.confirm}><input type="checkbox" checked={confirmed} disabled={busy} onChange={event => setConfirmed(event.target.checked)} /> I approve the exact workspace operations above for this tenant and environment. Do not execute yet.</label>
      <div className={styles.actions}><StudioButton disabled={!canApprove} onClick={() => void approve()}>Save workspace approval</StudioButton></div>
    </>}
    {approval && <>
      <p className={styles.note}>Approval {approval.approval_id} · Expires {new Date(approval.expires_at).toLocaleString()} · {expired ? 'Expired' : 'Time-limited'}</p>
      {!matches && <p className={styles.note}>Build and review the matching workspace plan before execution. Saved approval evidence alone does not enable execution.</p>}
      <div className={styles.actions}><StudioButton onClick={download}>Download approval and evidence</StudioButton></div>
      {matches && !attempted && <><label className={styles.confirm}><input type="checkbox" disabled={busy || expired} checked={executeConfirmed} onChange={event => setExecuteConfirmed(event.target.checked)} /> Create the listed workspaces in the approved tenant now. Partial failure can leave created resources; do not retry automatically.</label><div className={styles.actions}><StudioButton variant="primary" disabled={!canExecute} onClick={() => void execute()}>Execute approved workspace plan</StudioButton></div></>}
    </>}
    {(attempted || result) && <p role="status"><EvidenceLabel kind={result?.outcome.status === 'workspace_verified' ? 'tenant_verified' : 'not_verified'} scope="workspace readback only" /> {result?.outcome.status === 'workspace_verified' ? 'Workspace readback verified. Items, security, data and project acceptance are not verified.' : result ? 'Execution stopped or was not verified. Inspect the evidence and reconcile before approving another plan.' : 'Execution was requested. Retrieve the saved outcome before any further action.'}</p>}
    {result?.outcome.recovery && <p className={styles.note}>{result.outcome.recovery}</p>}
    <details className={styles.fileDetails}><summary>Retrieve an existing approval or execution outcome</summary>
      <p className={styles.note}>The URL retains only project, version and approval IDs for reload recovery. Select the original project version and retrieve its protected records; this never retries execution. Save the receipt for longer-term handover.</p>
      <div className={styles.inputs}><label>Saved approval ID<input value={lookup} disabled={busy} onChange={event => { setLookup(event.target.value); setExecuteConfirmed(false); }} /></label></div>
      <StudioButton disabled={busy || !/^[a-f0-9]{64}$/.test(lookup)} onClick={() => void retrieve()}>Retrieve saved outcome</StudioButton>
      {evidenceState && <p className={styles.note}>Saved attempt state: {evidenceState.replaceAll('_', ' ')}</p>}
    </details>
    {!!status?.limitations?.length && <details className={styles.fileDetails}><summary>Execution boundaries</summary><ul className={styles.gaps}>{status.limitations.map(item => <li key={item}>{item}</li>)}</ul></details>}
  </StudioPanel>
  <ProjectRunnerAcceptance projectId={projectId} revision={revision} plan={plan} approval={approval} result={result} />
  </>;
}
