'use client';

/**
 * DeliveryFlowPanel — the customer-without-builder journey (I-6.4).
 *
 * Renders the five-step flow (Authoring → Freigabe-Schleuse → Generate →
 * Validate → Deliverable) as a checklist and offers the deploy-handoff only when
 * the flow clears (approved AND gate-green). When blocked, it names the step that
 * blocks — no builder required to read the state.
 */

import type { DeliveryFlowState, FlowStepStatus } from '@/lib/studio/delivery-flow';

const STATUS_GLYPH: Record<FlowStepStatus, string> = {
  done: '✓',
  current: '▸',
  blocked: '✕',
  pending: '○',
};

export function DeliveryFlowPanel({
  flow,
  onHandoff,
}: {
  flow: DeliveryFlowState;
  onHandoff?: () => void;
}) {
  return (
    <section data-testid="delivery-flow-panel" className="delivery-flow-panel">
      <header>
        <h2>Auslieferung — Kunden-Durchlauf</h2>
        <p className="flow-subtitle">
          Bracket <code>{flow.bracketId}</code> · Deliverable nur bei Freigabe <em>und</em> grünem Gate.
        </p>
      </header>

      <ol className="flow-steps">
        {flow.steps.map((step) => (
          <li
            key={step.key}
            data-testid={`flow-step-${step.key}`}
            data-status={step.status}
            className={`flow-step is-${step.status}`}
          >
            <span className="flow-glyph" aria-hidden="true">
              {STATUS_GLYPH[step.status]}
            </span>
            <span className="flow-label">{step.label}</span>
            <span className="flow-detail">{step.detail}</span>
          </li>
        ))}
      </ol>

      {flow.canHandoff ? (
        <button
          type="button"
          data-testid="flow-handoff"
          className="flow-handoff is-ready"
          disabled={!onHandoff}
          onClick={() => onHandoff?.()}
        >
          Deploy-Handoff starten
        </button>
      ) : (
        <p data-testid="flow-blocked" className="flow-handoff is-blocked" role="status">
          Auslieferung blockiert: {flow.blockedReason}
        </p>
      )}
    </section>
  );
}
