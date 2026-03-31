'use client';

import { useState } from 'react';
import type { DecisionSpine } from '@/lib/schemas/decision-spine';
import { EscalationViewer } from './escalation-viewer';

interface Props {
  spines: DecisionSpine[];
}

function ConfidenceBadge({ level }: { level: string }) {
  const color =
    level === 'High' ? 'var(--mint)' : level === 'Medium' ? 'var(--gold)' : '#EF4444';
  const bg =
    level === 'High'
      ? 'rgba(0,212,170,0.15)'
      : level === 'Medium'
        ? 'rgba(255,184,0,0.15)'
        : 'rgba(239,68,68,0.15)';

  return (
    <span
      style={{
        padding: '2px 8px',
        borderRadius: 'var(--radius-sm)',
        fontSize: '0.6875rem',
        fontWeight: 600,
        backgroundColor: bg,
        color,
      }}
    >
      {level}
    </span>
  );
}

export function SpineList({ spines }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (spines.length === 0) {
    return (
      <p style={{ fontSize: '0.8125rem', color: 'var(--slate-500)' }}>
        No decision spines found.
      </p>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
      {spines.map((spine) => {
        const isExpanded = expandedId === spine.id;
        return (
          <div
            key={spine.id}
            style={{
              backgroundColor: 'var(--slate-800)',
              border: `1px solid ${isExpanded ? 'var(--info)' : 'var(--slate-700)'}`,
              borderRadius: 'var(--radius-lg)',
              overflow: 'hidden',
              transition: 'border-color var(--duration-fast) var(--ease-out)',
            }}
          >
            {/* Header row */}
            <button
              onClick={() => setExpandedId(isExpanded ? null : spine.id)}
              style={{
                width: '100%',
                display: 'grid',
                gridTemplateColumns: '1fr auto auto auto',
                gap: 'var(--sp-2)',
                alignItems: 'center',
                padding: 'var(--sp-1-5) var(--sp-2)',
                backgroundColor: 'transparent',
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <div>
                <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--slate-100)', marginBottom: '2px' }}>
                  {spine.name}
                </p>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-400)', fontFamily: 'monospace' }}>
                  {spine.id}
                </p>
              </div>
              <div style={{ display: 'flex', gap: '4px' }}>
                {spine.owner_domains.map((d) => (
                  <span
                    key={d}
                    style={{
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.6875rem',
                      backgroundColor: 'var(--slate-700)',
                      color: 'var(--slate-300)',
                    }}
                  >
                    {d}
                  </span>
                ))}
              </div>
              <ConfidenceBadge level={spine.decision_confidence.level} />
              <span style={{ color: 'var(--slate-500)', fontSize: '0.875rem', transition: 'transform var(--duration-fast)', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>
                &#x25BC;
              </span>
            </button>

            {/* Expanded detail */}
            {isExpanded && (
              <div style={{ padding: '0 var(--sp-2) var(--sp-2) var(--sp-2)' }}>
                <EscalationViewer spine={spine} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
