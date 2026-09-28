'use client';

import { useEffect, useState } from 'react';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import type { PriceDelta, PriceTotals } from '@/lib/bridge/project-price';
import styles from './project-alternative-impact.module.css';

const ROWS: Array<[keyof PriceTotals, string]> = [
  ['cost', 'Cost'], ['price_calculated', 'Price, calculated'], ['price_rounded', 'Price, rounded'], ['list_price', 'List price'],
];

/** Private money view of one alternative. Admin only, fetched on explicit request, never stored. */
export function ProjectPriceDelta({ projectId, revisionHash, decisionRef, optionRef }: {
  projectId: string; revisionHash: string; decisionRef: string; optionRef: string;
}) {
  const [requested, setRequested] = useState(false);
  const [result, setResult] = useState<PriceDelta | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!requested) return;
    const abort = new AbortController();
    const query = new URLSearchParams({ revision: revisionHash, decision: decisionRef, option: optionRef });
    void fetch(`/api/projects/${encodeURIComponent(projectId)}/architecture/commercial/price?${query}`, { cache: 'no-store', signal: abort.signal })
      .then(async response => {
        const value = await response.json();
        if (response.status === 403) throw new Error('Only project admins can see prices.');
        if (!response.ok) throw new Error(typeof value.error === 'string' ? value.error : 'Price delta unavailable');
        if (value.project_ref !== projectId || value.baseline_revision_hash !== revisionHash || value.alternative_option_ref !== optionRef || value.persist !== false) {
          throw new Error('Price delta project, revision or option mismatch');
        }
        if (!abort.signal.aborted) setResult(value as PriceDelta);
      }).catch(reason => { if (!abort.signal.aborted) setError(reason instanceof Error ? reason.message : 'Price delta unavailable'); });
    return () => abort.abort();
  }, [requested, projectId, revisionHash, decisionRef, optionRef]);

  if (!requested) {
    return <div className={styles.stack}>
      <p className={styles.note}>Admins only: cost and price of baseline and alternative from the tenant price canon. Shown here, never stored or exported.</p>
      <div><StudioButton onClick={() => setRequested(true)}>Show price delta</StudioButton></div>
    </div>;
  }
  if (!result) return <StudioEmptyState title={error ? 'Price delta unavailable' : 'Calculating price delta'} description={error || 'Running the price canon through the mirrored calculation core.'} />;
  if (result.status !== 'evaluated' || !result.baseline || !result.alternative || !result.delta) {
    return <StudioEmptyState title="No price delta" description={result.reason ?? (result.findings ?? []).join(' · ') ?? 'The price canon could not be evaluated.'} />;
  }
  const { baseline, alternative, delta } = result;
  const money = new Intl.NumberFormat('en-GB', { style: 'currency', currency: result.currency ?? 'EUR', maximumFractionDigits: 0 });
  const signed = (value: number) => `${value > 0 ? '+' : ''}${money.format(value)}`;
  const unpriced = [...baseline.unpriced, ...alternative.unpriced];
  return <div className={styles.stack}>
    <table className={styles.parts}>
      <caption>Cost and price · accepted baseline → alternative ({alternative.priced_packages} priced packages)</caption>
      <thead><tr><th scope="col">Figure</th><th scope="col">Baseline</th><th scope="col">Alternative</th><th scope="col">Delta</th></tr></thead>
      <tbody>{ROWS.map(([key, text]) => <tr key={key}>
        <td>{text}</td><td>{money.format(baseline.totals[key])}</td><td>{money.format(alternative.totals[key])}</td><td>{signed(delta[key])}</td>
      </tr>)}</tbody>
    </table>
    {!result.comparable && <p className={styles.note}>Not fully comparable: the two sides price different packages or some packages are unpriced.</p>}
    {unpriced.length > 0 && <StudioPanel title="Not priced">
      <ul className={styles.list}>{unpriced.map((row, index) => <li key={`${row.work_package_ref}-${index}`}><strong>{row.work_package_ref.replaceAll('_', ' ')}</strong><span>{row.reason}</span></li>)}</ul>
    </StudioPanel>}
  </div>;
}
