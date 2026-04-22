'use client';

import type { DecisionSpine } from '@/lib/schemas/decision-spine';
import { StudioPanel } from '@/components/ui/studio-page';

interface Props {
  spine: DecisionSpine;
}

const LEVEL_CONFIG: Record<string, { color: string; label: string; shortLabel: string }> = {
  EarlyWarning: { color: 'var(--mint)', label: 'Early Warning', shortLabel: 'L1' },
  RequiredIntervention: { color: 'var(--gold)', label: 'Required Intervention', shortLabel: 'L2' },
  PrescriptiveExecution: { color: '#EF4444', label: 'Prescriptive Execution', shortLabel: 'L3' },
};

export function EscalationViewer({ spine }: Props) {
  const path = spine.escalation_logic.escalation_path;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Escalation Path */}
      <div>
        <p style={{ fontSize: '0.6875rem', color: 'var(--ink-3)', marginBottom: '8px' }}>
          {spine.escalation_logic.principle}
        </p>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'stretch' }}>
          {path.map((step, i) => {
            const config = LEVEL_CONFIG[step.level] ?? { color: 'var(--ink-3)', label: step.level, shortLabel: `L${i + 1}` };
            return (
              <div key={step.level} style={{ flex: 1, display: 'flex', alignItems: 'stretch', gap: '8px' }}>
                <StudioPanel
                  style={{
                    flex: 1,
                    border: `1px solid ${config.color}`,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '24px',
                        height: '24px',
                        borderRadius: '50%',
                        backgroundColor: config.color,
                        color: 'var(--bg)',
                        fontSize: '0.6875rem',
                        fontWeight: 700,
                      }}
                    >
                      {config.shortLabel}
                    </span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: config.color }}>
                      {config.label}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.6875rem', color: 'var(--ink-2)', lineHeight: 1.5 }}>
                    {step.action}
                  </p>
                </StudioPanel>
                {i < path.length - 1 && (
                  <div style={{ display: 'flex', alignItems: 'center', color: 'var(--ink-4)', fontSize: '1.25rem' }}>
                    &#x2192;
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Decision Context */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <StudioPanel style={{ padding: '12px' }}>
          <p style={{ fontSize: '0.6875rem', color: 'var(--ink-3)', marginBottom: '4px', fontWeight: 600 }}>
            Primary Question
          </p>
          <p style={{ fontSize: '0.75rem', color: 'var(--ink-2)', lineHeight: 1.5 }}>
            {spine.decision_context.primary_question}
          </p>
        </StudioPanel>
        <StudioPanel style={{ padding: '12px' }}>
          <p style={{ fontSize: '0.6875rem', color: 'var(--ink-3)', marginBottom: '4px', fontWeight: 600 }}>
            Decision Confidence
          </p>
          <span
            style={{
              display: 'inline-block',
              padding: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.6875rem',
              fontWeight: 600,
              backgroundColor: spine.decision_confidence.level === 'High' ? 'rgba(0,212,170,0.15)' : spine.decision_confidence.level === 'Medium' ? 'rgba(255,184,0,0.15)' : 'rgba(239,68,68,0.15)',
              color: spine.decision_confidence.level === 'High' ? 'var(--mint)' : spine.decision_confidence.level === 'Medium' ? 'var(--gold)' : '#EF4444',
            }}
          >
            {spine.decision_confidence.level}
          </span>
        </StudioPanel>
      </div>

      {/* Tradeoffs */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <StudioPanel style={{ padding: '12px' }}>
          <p style={{ fontSize: '0.6875rem', color: 'var(--mint)', marginBottom: '4px', fontWeight: 600 }}>
            Improves
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {spine.decision_tradeoffs.improves.map((item) => (
              <span key={item} style={{ padding: '2px 8px', backgroundColor: 'rgba(0,212,170,0.1)', borderRadius: 'var(--radius-sm)', fontSize: '0.6875rem', color: 'var(--mint)' }}>
                {item}
              </span>
            ))}
          </div>
        </StudioPanel>
        <StudioPanel style={{ padding: '12px' }}>
          <p style={{ fontSize: '0.6875rem', color: '#EF4444', marginBottom: '4px', fontWeight: 600 }}>
            Risks
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {spine.decision_tradeoffs.risks.map((item) => (
              <span key={item} style={{ padding: '2px 8px', backgroundColor: 'rgba(239,68,68,0.1)', borderRadius: 'var(--radius-sm)', fontSize: '0.6875rem', color: '#EF4444' }}>
                {item}
              </span>
            ))}
          </div>
        </StudioPanel>
      </div>
    </div>
  );
}
