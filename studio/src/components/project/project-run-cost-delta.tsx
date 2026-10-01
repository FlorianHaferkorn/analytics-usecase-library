'use client';

import { useEffect, useState } from 'react';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import type { RunCostDelta, RunCostSide } from '@/lib/bridge/project-run-cost';
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
      <p className={styles.note}>Fabric capacities and Power BI licences of baseline and alternative at Microsoft list price (USD). No tenant rate, margin or staffing.</p>
      <div><StudioButton onClick={() => setRequested(true)}>Show run cost</StudioButton></div>
    </div>;
  }
  if (!result) return <StudioEmptyState title={error ? 'Run cost unavailable' : 'Calculating run cost'} description={error || 'Pricing the capacities the selected environments use.'} />;
  if (result.status !== 'evaluated' || !result.baseline || !result.alternative || !result.delta) {
    return <StudioEmptyState title="No run cost" description={result.reason ?? 'The run cost could not be evaluated.'} />;
  }
  const { baseline, alternative, delta } = result;
  const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
  const signed = (value: number) => `${value > 0 ? '+' : ''}${money.format(value)}`;
  const licence = (side: RunCostSide) => side.licences ? money.format(side.licences.usd_per_month) : 'not evaluated';
  const unpriced = [...baseline.unpriced, ...alternative.unpriced];
  return <div className={styles.stack}>
    <table className={styles.parts}>
      <caption>Run cost per month · accepted baseline → alternative ({result.price_basis}, valid from {result.price_valid_from})</caption>
      <thead><tr><th scope="col">Figure</th><th scope="col">Baseline</th><th scope="col">Alternative</th><th scope="col">Delta</th></tr></thead>
      <tbody>
        <tr><td>Capacities</td><td>{money.format(baseline.capacity_usd_per_month)}</td><td>{money.format(alternative.capacity_usd_per_month)}</td><td>{signed(delta.capacity_usd_per_month)}</td></tr>
        <tr><td>Power BI licences</td><td>{licence(baseline)}</td><td>{licence(alternative)}</td><td>{signed(delta.licence_usd_per_month)}</td></tr>
        <tr><td>Total</td><td>{money.format(baseline.usd_per_month)}</td><td>{money.format(alternative.usd_per_month)}</td><td>{signed(delta.usd_per_month)}</td></tr>
      </tbody>
    </table>
    <dl className={styles.tiles} aria-label="Run-cost summary">
      <div><dt>Per year</dt><dd>{signed(delta.usd_per_year)}</dd></div>
      <div><dt>Capacities removed</dt><dd>{delta.capacities_removed.length}</dd></div>
      <div><dt>Overage ceiling, not in the total</dt><dd>{money.format(baseline.overage_ceiling_usd_per_month)} → {money.format(alternative.overage_ceiling_usd_per_month)}</dd></div>
    </dl>
    <table className={styles.parts}>
      <caption>Capacities used by the alternative</caption>
      <thead><tr><th scope="col">SKU</th><th scope="col">Billing</th><th scope="col">Environments</th><th scope="col">Per month</th></tr></thead>
      <tbody>{alternative.capacities.map(row => <tr key={row.capacity_id}>
        <td>{row.sku}</td><td>{row.billing === 'reservation' ? 'Reservation' : 'Pay-as-you-go'}</td><td>{row.environments.join(', ')}</td><td>{money.format(row.usd_per_month)}</td>
      </tr>)}</tbody>
    </table>
    {alternative.licences && <p className={styles.note}>Licences: {alternative.licences.basis} ({alternative.licences.pro_users} Pro users).</p>}
    {!result.comparable && <p className={styles.note}>Not fully comparable: some capacities are unpriced.</p>}
    {unpriced.length > 0 && <StudioPanel title="Not priced">
      <ul className={styles.list}>{unpriced.map((row, index) => <li key={`${row.capacity_id}-${index}`}><strong>{row.capacity_id}</strong><span>{row.reason}</span></li>)}</ul>
    </StudioPanel>}
  </div>;
}
