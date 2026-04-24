'use client';

import { useState } from 'react';
import type { DecisionSpine } from '@/lib/schemas/decision-spine';
import { card, cardHead } from '@/components/registry/kpi-detail-tabs';
import { AiField } from '@/components/ai/ai-field';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Props {
  spine: DecisionSpine;
  compact?: boolean;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function ImpactPill({ dimension }: { dimension: string }) {
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: 999,
        fontSize: 10.5,
        fontWeight: 500,
        background: 'oklch(0.22 0.06 200 / 0.4)',
        color: 'oklch(0.7 0.15 200)',
        letterSpacing: '0.01em',
      }}
    >
      {dimension}
    </span>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontSize: 10.5,
        fontWeight: 600,
        color: 'var(--ink-3)',
        textTransform: 'uppercase',
        letterSpacing: '0.07em',
        marginBottom: 8,
      }}
    >
      {children}
    </div>
  );
}

function ContextGrid({ spine }: { spine: DecisionSpine }) {
  const items = [
    { label: 'Decision Type', value: spine.decision_context.decision_type },
    { label: 'Primary Question', value: spine.decision_context.primary_question },
    { label: 'Owner Roles', value: spine.decision_context.decision_owner_roles.join(', ') },
  ];
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 8,
      }}
    >
      {items.map((item) => (
        <div
          key={item.label}
          style={{
            padding: '8px 10px',
            background: 'var(--bg-2)',
            borderRadius: 6,
            gridColumn: item.label === 'Primary Question' ? 'span 2' : undefined,
          }}
        >
          <div style={{ fontSize: 10, color: 'var(--ink-4)', marginBottom: 3, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            {item.label}
          </div>
          <div style={{ fontSize: 12, color: 'var(--ink-2)', lineHeight: 1.4 }}>
            {item.value}
          </div>
        </div>
      ))}
    </div>
  );
}

function TradeoffColumns({ spine }: { spine: DecisionSpine }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
      <div>
        <div style={{ fontSize: 10.5, fontWeight: 600, color: 'oklch(0.6 0.15 150)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Improves
        </div>
        <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
          {spine.decision_tradeoffs.improves.map((item, i) => (
            <li
              key={i}
              style={{
                fontSize: 12,
                color: 'var(--ink-2)',
                lineHeight: 1.5,
                paddingLeft: 14,
                position: 'relative',
                marginBottom: 2,
              }}
            >
              <span
                style={{
                  position: 'absolute',
                  left: 0,
                  top: '0.45em',
                  width: 5,
                  height: 5,
                  borderRadius: '50%',
                  background: 'oklch(0.6 0.15 150)',
                  display: 'inline-block',
                }}
              />
              {item}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <div style={{ fontSize: 10.5, fontWeight: 600, color: 'oklch(0.75 0.15 75)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Risks
        </div>
        <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
          {spine.decision_tradeoffs.risks.map((item, i) => (
            <li
              key={i}
              style={{
                fontSize: 12,
                color: 'var(--ink-2)',
                lineHeight: 1.5,
                paddingLeft: 14,
                position: 'relative',
                marginBottom: 2,
              }}
            >
              <span
                style={{
                  position: 'absolute',
                  left: 0,
                  top: '0.45em',
                  width: 5,
                  height: 5,
                  borderRadius: '50%',
                  background: 'oklch(0.75 0.15 75)',
                  display: 'inline-block',
                }}
              />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

const ESCALATION_COLORS: Record<string, string> = {
  EarlyWarning: 'oklch(0.75 0.15 75)',
  RequiredIntervention: 'oklch(0.75 0.15 28)',
  PrescriptiveExecution: 'oklch(0.6 0.15 150)',
};

function EscalationPath({ spine }: { spine: DecisionSpine }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {spine.escalation_logic.escalation_path.map((step, i) => {
        const color = ESCALATION_COLORS[step.level] ?? 'var(--ink-3)';
        return (
          <div
            key={i}
            style={{
              display: 'flex',
              gap: 10,
              alignItems: 'flex-start',
              padding: '8px 10px',
              background: 'var(--bg-2)',
              borderRadius: 6,
              borderLeft: `2px solid ${color}`,
            }}
          >
            <span
              style={{
                flexShrink: 0,
                fontSize: 9.5,
                fontWeight: 600,
                color,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                paddingTop: 1,
                minWidth: 120,
              }}
            >
              {step.level}
            </span>
            <span style={{ fontSize: 12, color: 'var(--ink-2)', lineHeight: 1.4 }}>
              {step.action}
            </span>
          </div>
        );
      })}
    </div>
  );
}

const CONFIDENCE_COLORS: Record<string, string> = {
  High: 'oklch(0.6 0.15 150)',
  Medium: 'oklch(0.75 0.15 75)',
  Low: 'oklch(0.75 0.15 28)',
};

function ConfidenceSection({ spine }: { spine: DecisionSpine }) {
  const color = CONFIDENCE_COLORS[spine.decision_confidence.level] ?? 'var(--ink-3)';
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span
          style={{
            padding: '2px 8px',
            borderRadius: 999,
            fontSize: 11,
            fontWeight: 600,
            background: `${color.replace('oklch', 'oklch').replace(')', ' / 0.15)')}`,
            color,
          }}
        >
          {spine.decision_confidence.level}
        </span>
      </div>
      <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
        {spine.decision_confidence.rationale.map((r, i) => (
          <li key={i} style={{ fontSize: 12, color: 'var(--ink-2)', lineHeight: 1.5, marginBottom: 3, paddingLeft: 12, position: 'relative' }}>
            <span style={{ position: 'absolute', left: 0, color: 'var(--ink-4)' }}>›</span>
            {r}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ─── SpineIntentField ──────────────────────────────────────────────────────────

function SpineIntentField({ spine }: { spine: DecisionSpine }) {
  const [intentValue, setIntentValue] = useState(spine.purpose.intent);
  return (
    <AiField
      entityType="bracket"
      entityId={spine.id}
      entityName={spine.name}
      fieldName="intent"
      fieldLabel="Intent"
      value={intentValue}
      onChange={setIntentValue}
      multiline
      rows={3}
    />
  );
}

// ─── Compact view ─────────────────────────────────────────────────────────────

function CompactCard({ spine }: { spine: DecisionSpine }) {
  return (
    <div
      style={{
        padding: 16,
        background: 'var(--panel)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--radius)',
        marginBottom: 8,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--ink)' }}>{spine.name}</span>
        <ImpactPill dimension={spine.impact_dimension} />
      </div>
      <p
        style={{
          margin: '0 0 6px',
          fontSize: 12,
          color: 'var(--ink-2)',
          lineHeight: 1.5,
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}
      >
        {spine.purpose.intent}
      </p>
      <span style={{ fontSize: 10.5, color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {spine.decision_context.decision_type}
      </span>
    </div>
  );
}

// ─── Full card ────────────────────────────────────────────────────────────────

function FullCard({ spine }: { spine: DecisionSpine }) {
  return (
    <div style={{ ...card, marginBottom: 0 }}>
      {/* Header */}
      <div style={cardHead}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--ink)' }}>{spine.name}</span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              color: 'var(--ink-4)',
              background: 'var(--bg-2)',
              padding: '1px 6px',
              borderRadius: 4,
            }}
          >
            {spine.id}
          </span>
        </div>
        <ImpactPill dimension={spine.impact_dimension} />
      </div>

      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Intent */}
        <div>
          <SectionLabel>Intent</SectionLabel>
          <SpineIntentField spine={spine} />
        </div>

        {/* Decision Context */}
        <div>
          <SectionLabel>Decision Context</SectionLabel>
          <ContextGrid spine={spine} />
        </div>

        {/* Tradeoffs */}
        <div>
          <SectionLabel>Tradeoffs</SectionLabel>
          <TradeoffColumns spine={spine} />
        </div>

        {/* Escalation Path */}
        <div>
          <SectionLabel>Escalation Path</SectionLabel>
          <EscalationPath spine={spine} />
        </div>

        {/* Confidence */}
        <div>
          <SectionLabel>Decision Confidence</SectionLabel>
          <ConfidenceSection spine={spine} />
        </div>
      </div>
    </div>
  );
}

// ─── Export ───────────────────────────────────────────────────────────────────

export function SpineNodeCard({ spine, compact = false }: Props) {
  if (compact) return <CompactCard spine={spine} />;
  return <FullCard spine={spine} />;
}
