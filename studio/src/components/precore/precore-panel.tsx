'use client';

/**
 * PreCorePanel — "Vor dem Core" reality check (I-6.2).
 *
 * Presentational: renders the gov/eng/arch engine findings returned by the
 * Superversion bridge (ADR-0007). When the bridge is unavailable it shows an
 * honest banner instead of a fabricated empty pass (ADR-0007 rule 5).
 */

import type { PreCoreResult, PreCoreFinding } from '@/lib/bridge/superversion-bridge';

const SEVERITY_LABEL: Record<PreCoreFinding['severity'], string> = {
  error: 'Fehler',
  warn: 'Warnung',
  info: 'Hinweis',
};

export function PreCorePanel({ result }: { result: PreCoreResult }) {
  if (!result.available) {
    return (
      <div role="alert" data-testid="precore-unavailable" className="precore-unavailable">
        <strong>Vor-dem-Core-Prüfung nicht verfügbar.</strong>{' '}
        Die Superversion-Bridge ist offline — Ergebnis <em>nicht gate-validiert</em>.
        {result.error ? <span className="precore-error"> ({result.error})</span> : null}
      </div>
    );
  }

  return (
    <section data-testid="precore-panel" className="precore-panel">
      <header>
        <h2>Vor dem Core — gov/eng/arch-Realität</h2>
        <p className="precore-subtitle">
          Beta-Engines (I-5.3) gegen <code>{result.bracket}</code>. Diese Prüfung läuft
          gegen den governten Python-Core, nicht gegen die UI-Vorschau.
        </p>
      </header>

      {result.engines.map((engine) => (
        <article key={engine.id} data-testid={`engine-${engine.id}`} className="precore-engine">
          <h3>
            {engine.label} <span className="precore-status">[{engine.status}]</span>
          </h3>
          {engine.findings.length === 0 ? (
            <p className="precore-clean" data-testid={`engine-${engine.id}-clean`}>
              Keine Befunde.
            </p>
          ) : (
            <ul>
              {engine.findings.map((f, i) => (
                <li key={`${f.code}-${i}`} data-severity={f.severity}>
                  <span className="precore-sev">{SEVERITY_LABEL[f.severity]}</span>{' '}
                  <code>{f.code}</code> — {f.detail}
                </li>
              ))}
            </ul>
          )}
        </article>
      ))}
    </section>
  );
}
