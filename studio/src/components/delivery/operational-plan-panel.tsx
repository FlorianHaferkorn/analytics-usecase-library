'use client';

import { StudioPanel } from '@/components/ui/studio-page';
import styles from './operational-plan-panel.module.css';

interface Props {
  selectedCount: number;
  selectedDomains: string[];
  adapterStatus: string;
  adapterName: string;
  readinessWarnings: string[];
  runbookSteps: string[];
}

export function OperationalPlanPanel({
  selectedCount,
  selectedDomains,
  adapterStatus,
  adapterName,
  readinessWarnings,
  runbookSteps,
}: Props) {
  const ready = readinessWarnings.length === 0;
  return (
    <StudioPanel
      title="Operational plan"
      description="Validation checks, target scope and execution steps for this delivery move."
      tone={ready ? 'success' : 'warning'}
      action={<span className={styles.status} data-ready={ready}>{ready ? 'Ready for validation' : `${readinessWarnings.length} checks before export`}</span>}
    >
      <div className={styles.summaryGrid}>
        <div><span>Scope</span><strong>{selectedCount}</strong><p>Use cases selected</p></div>
        <div><span>Domains</span><strong>{selectedDomains.length}</strong><p>{selectedDomains.join(', ') || 'None selected'}</p></div>
        <div><span>Target</span><strong>{adapterStatus}</strong><p>{adapterName}</p></div>
      </div>

      {readinessWarnings.length > 0 && (
        <section className={styles.checks} aria-labelledby="delivery-checks-heading">
          <h3 id="delivery-checks-heading">Checks to resolve</h3>
          <ul>{readinessWarnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
        </section>
      )}

      <details className={styles.runbook}>
        <summary>Execution runbook <span>{runbookSteps.length} steps</span></summary>
        <ol>{runbookSteps.map((step) => <li key={step}><code>{step}</code></li>)}</ol>
      </details>
    </StudioPanel>
  );
}
