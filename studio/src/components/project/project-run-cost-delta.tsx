'use client';

import { useEffect, useState } from 'react';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import type { RunCostDelta } from '@/lib/bridge/project-run-cost';
import styles from './project-alternative-impact.module.css';

/** Run cost of baseline and alternative at Microsoft list price. Fetches only on explicit request. */
export function ProjectRunCostDelta({ projectId, revisionHash, decisionRef, optionRef }: {
  projectId: string; revisionHash: string; decisionRef: string; optionRef: string;
}) {
  const [requested, setRequested] = useState(false);
  const [result, setResult] = useState<RunCostDelta | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!requested) return;
    const abort = new AbortController();
    const query = new URLSearchParams({ revision: revisionHash, decision: decisionRef, option: optionRef });
    void fetch(`/api/projects/${encodeURIComponent(projectId)}/architecture/run-cost?${query}`, { cache: 'no-store', signal: abort.signal })
      .then(async response => {
        const value = await response.json();
        if (!response.ok) throw new Error(typeof value.error === 'string' ? value.error : 'Run-cost comparison unavailable');
        if (value.project_ref !== projectId || value.baseline_revision_hash !== revisionHash || value.alternative_option_ref !== optionRef || value.persist !== false) {
          throw new Error('Run-cost comparison project, revision or option mismatch');
        }
        if (!abort.signal.aborted) setResult(value as RunCostDelta);
      }).catch(reason => { if (!abort.signal.aborted) setError(reason instanceof Error ? reason.message : 'Run-cost comparison unavailable'); });
    return () => abort.abort();
  }, [requested, projectId, revisionHash, decisionRef, optionRef]);

  if (!requested) {
    return <div className={styles.stack}>
      <p className={styles.note}>Fabric capacities, Power BI licences and monitoring storage of baseline and alternative at Microsoft list price, in the package region and currency. No tenant rate, margin or staffing.</p>
      <div><StudioButton onClick={() => setRequested(true)}>Show run cost</StudioButton></div>
    </div>;
  }
  if (!result) return <StudioEmptyState title={error ? 'Run cost unavailable' : 'Calculating run cost'} description={error || 'Pricing the capacities the selected environments use.'} />;
  if (result.status !== 'evaluated' || !result.baseline || !result.alternative || !result.delta) {
    return <StudioEmptyState title="No run cost" description={result.reason ?? 'The run cost could not be evaluated.'} />;
  }
  const { baseline, alternative, delta } = result;
  const money = new Intl.NumberFormat('en-GB', { style: 'currency', currency: result.currency ?? 'USD', maximumFractionDigits: 0 });
  const signed = (value: number) => `${value > 0 ? '+' : ''}${money.format(value)}`;
  const part = (value: { per_month: number | null } | null) => !value ? 'not evaluated' : value.per_month === null ? 'not priced' : money.format(value.per_month);
  const unpriced = [...baseline.unpriced, ...alternative.unpriced];
  return <div className={styles.stack}>
    <table className={styles.parts}>
      <caption>Run cost per month · accepted baseline → alternative ({result.region}; {result.price_basis}, as of {result.price_valid_from})</caption>
      <thead><tr><th scope="col">Figure</th><th scope="col">Baseline</th><th scope="col">Alternative</th><th scope="col">Delta</th></tr></thead>
      <tbody>
        <tr><td>Capacities</td><td>{money.format(baseline.capacity_per_month)}</td><td>{money.format(alternative.capacity_per_month)}</td><td>{signed(delta.capacity_per_month)}</td></tr>
        <tr><td>Power BI licences</td><td>{part(baseline.licences)}</td><td>{part(alternative.licences)}</td><td>{signed(delta.licence_per_month)}</td></tr>
        <tr><td>Monitoring storage</td><td>{part(baseline.monitoring_storage)}</td><td>{part(alternative.monitoring_storage)}</td><td>{signed(delta.monitoring_storage_per_month)}</td></tr>
        <tr><td>Total</td><td>{money.format(baseline.per_month)}</td><td>{money.format(alternative.per_month)}</td><td>{signed(delta.per_month)}</td></tr>
      </tbody>
    </table>
    <dl className={styles.tiles} aria-label="Run-cost summary">
      <div><dt>Per year</dt><dd>{signed(delta.per_year)}</dd></div>
      <div><dt>Capacities removed</dt><dd>{delta.capacities_removed.length}</dd></div>
      <div><dt>Overage ceiling, not in the total</dt><dd>{money.format(baseline.overage_ceiling_per_month)} → {money.format(alternative.overage_ceiling_per_month)}</dd></div>
    </dl>
    <table className={styles.parts}>
      <caption>Capacities used by the alternative</caption>
      <thead><tr><th scope="col">SKU</th><th scope="col">Billing</th><th scope="col">Environments</th><th scope="col">Per month</th></tr></thead>
      <tbody>{alternative.capacities.map(row => <tr key={row.capacity_id}>
        <td>{row.sku}</td><td>{row.billing === 'reservation' ? 'Reservation' : 'Pay-as-you-go'}</td><td>{row.environments.join(', ')}</td><td>{money.format(row.per_month)}</td>
      </tr>)}</tbody>
    </table>
    {alternative.licences && <p className={styles.note}>Licences: {alternative.licences.basis} ({alternative.licences.pro_users} Pro users).</p>}
    {!result.comparable && <p className={styles.note}>Not fully comparable: some positions are unpriced.</p>}
    {unpriced.length > 0 && <StudioPanel title="Not priced">
      <ul className={styles.list}>{unpriced.map((row, index) => <li key={`${row.item}-${index}`}><strong>{row.item.replaceAll('_', ' ')}</strong><span>{row.reason}</span></li>)}</ul>
    </StudioPanel>}
  </div>;
}
