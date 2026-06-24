'use client';

/**
 * GateReportPanel — "Nach dem Core" (I-6.3).
 *
 * Renders the target choice, the emitted artifact manifest, and the Gate-Report
 * (Golden-Thread gate I-3.4 + E2E smoke I-3.5) returned by the Superversion
 * bridge (ADR-0007). The deploy-handoff is offered only when the gate is green;
 * a red gate blocks it, and a bridge outage shows an honest "not gate-validated"
 * banner rather than a fabricated pass (ADR-0007 rule 5).
 */

import type { GenerateResult, GateStage } from '@/lib/bridge/superversion-bridge';

const STAGE_LABEL: Record<GateStage['status'], string> = {
  PASS: 'OK',
  FAIL: 'Fehler',
  SKIP: 'übersprungen',
};

export function GateReportPanel({
  result,
  onSelectTarget,
}: {
  result: GenerateResult;
  onSelectTarget?: (target: string) => void;
}) {
  if (!result.available) {
    return (
      <div role="alert" data-testid="generate-unavailable" className="generate-unavailable">
        <strong>Generierung nicht verfügbar.</strong>{' '}
        Die Superversion-Bridge ist offline — Ergebnis <em>nicht gate-validiert</em>.
        {result.error ? <span className="generate-error"> ({result.error})</span> : null}
      </div>
    );
  }

  return (
    <section data-testid="gate-report-panel" className="gate-report-panel">
      <header>
        <h2>Nach dem Core — Target &amp; Gate-Report</h2>
        <p className="postcore-subtitle">
          Deliverable für <code>{result.bracket}</code>, erzeugt vom governten Python-Core.
        </p>
      </header>

      <fieldset data-testid="target-picker" className="target-picker">
        <legend>Target</legend>
        {result.targetsAvailable.map((t) => (
          <button
            key={t}
            type="button"
            data-testid={`target-${t}`}
            aria-pressed={t === result.target}
            disabled={!onSelectTarget}
            onClick={() => onSelectTarget?.(t)}
          >
            {t}
            {t === result.target ? ' ✓' : ''}
          </button>
        ))}
      </fieldset>

      <div
        data-testid="gate-verdict"
        data-ok={result.gate?.ok ? 'true' : 'false'}
        className="gate-verdict"
      >
        <h3>
          Gate-Report:{' '}
          {result.gate?.ok ? 'grün — gate-validiert' : 'rot — Auslieferung blockiert'}
        </h3>
        <ul>
          {(result.gate?.stages ?? []).map((s) => (
            <li key={s.name} data-testid={`stage-${s.name}`} data-status={s.status}>
              <span className="stage-status">{STAGE_LABEL[s.status]}</span> <strong>{s.name}</strong>
              {s.detail ? ` — ${s.detail}` : ''}
            </li>
          ))}
        </ul>
      </div>

      <div data-testid="artifact-manifest" className="artifact-manifest">
        <h3>
          Artefakte ({result.targetLabel ?? result.target}
          {result.targetStatus ? ` · ${result.targetStatus}` : ''})
        </h3>
        <ul>
          {result.artifacts.map((a) => (
            <li key={a.path}>
              <code>{a.path}</code> <span className="artifact-bytes">({a.bytes} B)</span>
            </li>
          ))}
        </ul>
      </div>

      {result.gate?.ok ? (
        <p data-testid="deploy-handoff-ready" className="deploy-handoff is-ready">
          Bereit zum Deploy-Handoff.
        </p>
      ) : (
        <p data-testid="deploy-handoff-blocked" className="deploy-handoff is-blocked">
          Deploy-Handoff blockiert — Gate ist rot.
        </p>
      )}
    </section>
  );
}
