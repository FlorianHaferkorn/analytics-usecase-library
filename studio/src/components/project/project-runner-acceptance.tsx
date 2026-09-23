'use client';
import { StudioButton, StudioPanel } from '@/components/ui/studio-page';
import { buildRunnerAcceptance } from '@/lib/project/runner-acceptance';
import type { DeploymentPlan } from '@/lib/bridge/project-deployment';
import type { RunnerApproval, RunnerResult } from '@/lib/bridge/project-runner';
import styles from './project-runner-readiness.module.css';

const stateLabel = { not_run: 'Not run', review_required: 'Review required', evidence_available: 'Evidence available', out_of_scope: 'Outside first-test scope' };
export function ProjectRunnerAcceptance({ projectId, revision, plan, approval, result }: {
  projectId: string; revision: string; plan: DeploymentPlan | null; approval: RunnerApproval | null; result: RunnerResult | null;
}) {
  const protocol = buildRunnerAcceptance(projectId, revision, plan, approval, result);
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify({ ...protocol, exported_at: new Date().toISOString() }, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = `${projectId}-workspace-acceptance-${revision.slice(0, 12)}.json`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <StudioPanel title="First workspace acceptance" compactHeader description="A guided, bounded test in DEV or TEST. Preparing or downloading this protocol never executes a plan."
    action={<StudioButton onClick={download}>Download acceptance protocol</StudioButton>}>
    <div className={styles.stack}>
      <p className={styles.summary}>Not accepted · Six evidence-based checks before live workspace delivery is accepted.</p>
      <p className={styles.meta}>Start with one explicitly authorized non-production workspace. The protocol is a review aid, not a deployment approval. Retain signed host records and record acceptance in the project authority.</p>
      <details className={styles.group}><summary>Open the workspace acceptance procedure</summary>
        <div className={styles.checks}>{protocol.cases.map((item, index) => <details key={item.id} className={styles.check}>
          <summary><span>{index + 1}. {item.title}</span><span className={styles.state} data-state={item.state}>{stateLabel[item.state]}</span></summary>
          <p><strong>Procedure:</strong> {item.procedure}</p>
          <p><strong>Expected result:</strong> {item.expected}</p>
          <p><strong>Evidence to retain:</strong> {item.evidence}</p>
        </details>)}</div>
      </details>
    </div>
  </StudioPanel>;
}
