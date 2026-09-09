'use client';
import { StudioButton, StudioPanel } from '@/components/ui/studio-page';
import type { RunnerCheck } from '@/lib/bridge/project-runner';
import styles from './project-runner-readiness.module.css';

const stateLabel = { configured: 'Configured', missing: 'Action needed', not_verified: 'Not verified' };
function Check({ check }: { check: RunnerCheck }) {
  return <details className={styles.check}>
    <summary><span>{check.title}</span><span className={styles.state} data-state={check.state}>{stateLabel[check.state]}</span></summary>
    <p>{check.detail}</p><p><strong>Next action:</strong> {check.action}</p>
  </details>;
}
export function ProjectRunnerReadiness({ checks, loading, checkedAt, unavailable, refresh, busy }: {
  checks: RunnerCheck[]; loading: boolean; checkedAt?: string; unavailable: boolean; refresh: () => void; busy: boolean;
}) {
  const missing = checks.filter(check => check.state === 'missing');
  const configured = checks.filter(check => check.state === 'configured');
  const unverified = checks.filter(check => check.state === 'not_verified');
  return <StudioPanel title="Runner readiness" compactHeader
    description="Read-only configuration checks. No login, token request or tenant operation is performed."
    action={<StudioButton disabled={busy || loading} onClick={refresh}>{loading ? 'Checking…' : 'Recheck readiness'}</StudioButton>}>
    <div className={styles.stack}>
      <p className={styles.summary} role="status">{loading ? 'Checking access and host prerequisites…' : unavailable ? 'Host checks are unavailable. Resolve access or host configuration, then recheck.' : missing.length ? `${missing.length} configuration ${missing.length === 1 ? 'prerequisite needs' : 'prerequisites need'} attention.` : checks.length ? 'Reported configuration checks are satisfied. Live acceptance is still required.' : 'Detailed host checks are unavailable. Recheck after updating the host adapter.'}</p>
      {checkedAt && <p className={styles.meta}>Checked {new Date(checkedAt).toLocaleString()} · Configuration only, not permission or deployment proof</p>}
      {!!missing.length && <div className={styles.checks}>{missing.map(check => <Check key={check.id} check={check} />)}</div>}
      {!!unverified.length && <details className={styles.group}><summary>Operational evidence still required ({unverified.length})</summary><div className={styles.checks}>{unverified.map(check => <Check key={check.id} check={check} />)}</div></details>}
      {!!configured.length && <details className={styles.group}><summary>Configured prerequisites ({configured.length})</summary><div className={styles.checks}>{configured.map(check => <Check key={check.id} check={check} />)}</div></details>}
      <p className={styles.meta}>Rechecking does not enable the runner or change host settings. Credentials and signing keys are managed outside the browser.</p>
    </div>
  </StudioPanel>;
}
