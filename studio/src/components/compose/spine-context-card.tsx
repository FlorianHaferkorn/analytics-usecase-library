'use client';

import type { DecisionSpine } from '@/lib/schemas/decision-spine';
import { card, cardHead } from '@/components/registry/kpi-detail-tabs';

interface Props {
  spines: DecisionSpine[];
  bracketId: string;
}

/**
 * SpineContextCard — shows the decision spine most relevant to the selected
 * bracket. Relevance is determined by matching owner_domains against the
 * bracket domain prefix (first segment of the bracket ID, e.g. "COM" from
 * "COM-001"). Falls back to the first spine if no domain match is found.
 */
export function SpineContextCard({ spines, bracketId }: Props) {
  if (spines.length === 0) return null;

  // Derive domain token from bracket ID prefix (e.g. "COM" from "COM-001")
  const domainToken = bracketId.split('-')[0]?.toUpperCase() ?? '';

  const relevant =
    spines.find((s) =>
      s.owner_domains.some((d) => d.toUpperCase().includes(domainToken)),
    ) ?? spines[0];

  if (!relevant) return null;

  return (
    <div style={card}>
      {/* Header */}
      <div style={cardHead}>
        <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
          Decision Context
        </span>
        <span
          style={{
            fontSize: '0.75rem',
            color: 'var(--ink-3)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          {relevant.name}
        </span>
      </div>

      {/* Body */}
      <div style={{ padding: 'var(--pad)', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {/* Strategic Intent */}
        <p
          style={{
            margin: 0,
            fontSize: 14,
            color: 'var(--ink-2)',
            lineHeight: 1.6,
          }}
        >
          {relevant.purpose.intent}
        </p>

        {/* Decision Type pill + Primary Question row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, flexWrap: 'wrap' }}>
          <span
            style={{
              display: 'inline-block',
              padding: '2px 8px',
              borderRadius: 4,
              background: 'var(--hover)',
              color: 'var(--ink-3)',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              whiteSpace: 'nowrap',
              flexShrink: 0,
            }}
          >
            {relevant.decision_context.decision_type}
          </span>

          <p
            style={{
              margin: 0,
              fontSize: '0.8125rem',
              color: 'var(--ink-2)',
              fontStyle: 'italic',
              lineHeight: 1.5,
            }}
          >
            {relevant.decision_context.primary_question}
          </p>
        </div>
      </div>
    </div>
  );
}
