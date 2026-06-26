/**
 * AiHealthPanel — read-only AI budget/usage + ROI dashboard (I-6.6 UI).
 *
 * Presentational: renders the `buildAiHealth` report (I-6.6 V4). Surfaces the honest
 * caveats verbatim — incomplete/unverified cost and UNCOMPUTED ROI are shown as such,
 * never hidden behind a fabricated green number.
 */

import type { AiHealth } from '@/lib/ai/health';

function fmtUsd(n: number): string {
  return `$${n.toFixed(n < 1 ? 4 : 2)}`;
}

export function AiHealthPanel({ health }: { health: AiHealth }) {
  const { usage, roi, warnings } = health;
  return (
    <section data-testid="ai-health-panel" className="ai-health-panel">
      <header>
        <h2>AI-Health &amp; Budget</h2>
        <p className="ai-health-sub">
          Projekt <code>{health.projectId}</code> · lokal-first Telemetrie (kein PII)
        </p>
      </header>

      <div data-testid="usage-stats" className="ai-health-stats">
        <dl>
          <div><dt>Schritte</dt><dd>{usage.steps}</dd></div>
          <div><dt>Input-Tokens</dt><dd>{usage.inputTokens.toLocaleString()}</dd></div>
          <div><dt>Output-Tokens</dt><dd>{usage.outputTokens.toLocaleString()}</dd></div>
          <div><dt>Kosten</dt><dd data-testid="cost">{fmtUsd(usage.costUsd)}</dd></div>
          <div><dt>Fehler</dt><dd>{usage.errors}</dd></div>
        </dl>
      </div>

      <div data-testid="roi-verdict" data-status={roi.status} className="ai-health-roi">
        <h3>ROI</h3>
        {roi.status === 'computed' ? (
          <p>
            <strong>{(roi.roi * 100).toFixed(0)}%</strong>{' '}
            (Wert {fmtUsd(roi.valueUsd)} − Kosten {fmtUsd(roi.costUsd)})
            {roi.notes.length > 0 && (
              <span className="ai-health-notes"> · {roi.notes.join(' · ')}</span>
            )}
          </p>
        ) : (
          <p data-testid="roi-uncomputed">
            <strong>UNCOMPUTED</strong> — {roi.reason}
          </p>
        )}
      </div>

      {warnings.length > 0 && (
        <ul data-testid="ai-health-warnings" className="ai-health-warnings" role="status">
          {warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
