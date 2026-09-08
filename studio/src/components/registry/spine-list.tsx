'use client';

import { useState } from 'react';
import type { DecisionSpine } from '@/lib/schemas/decision-spine';
import { EscalationViewer } from './escalation-viewer';
import { StudioButton, StudioEmptyState } from '@/components/ui/studio-page';

interface Props {
  spines: DecisionSpine[];
}

function ConfidenceBadge({ level }: { level: string }) {
  const color =
    level === 'High' ? 'var(--accent)' : level === 'Medium' ? 'var(--warning)' : '#EF4444';
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
        fontSize: 'var(--text-xs)',
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
    return <StudioEmptyState title="No decision spines found" description="Registry has no governed decision spines available for the current slice." />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {spines.map((spine) => {
        const isExpanded = expandedId === spine.id;
        return (
          <div
            key={spine.id}
            style={{
              backgroundColor: 'var(--panel)',
              border: `1px solid ${isExpanded ? 'var(--info)' : 'var(--line)'}`,
              borderRadius: 'var(--radius-lg)',
              overflow: 'hidden',
              transition: 'border-color var(--duration-fast) var(--ease-out)',
            }}
          >
            {/* Header row */}
            <StudioButton
              onClick={() => setExpandedId(isExpanded ? null : spine.id)}
              variant="ghost"
              style={{
                width: '100%',
                display: 'grid',
                gridTemplateColumns: '1fr auto auto auto',
                gap: '16px',
                alignItems: 'center',
                padding: '12px 16px',
                backgroundColor: 'transparent',
                textAlign: 'left',
                justifyContent: 'stretch',
              }}
            >
              <div>
                <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '2px' }}>
                  {spine.name}
                </p>
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)', fontFamily: 'monospace' }}>
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
                      fontSize: 'var(--text-xs)',
                      backgroundColor: 'var(--bg-2)',
                      color: 'var(--ink-2)',
                    }}
                  >
                    {d}
                  </span>
                ))}
              </div>
              <ConfidenceBadge level={spine.decision_confidence.level} />
              <span style={{ color: 'var(--ink-4)', fontSize: '0.875rem', transition: 'transform var(--duration-fast)', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>
                &#x25BC;
              </span>
            </StudioButton>

            {/* Expanded detail */}
            {isExpanded && (
              <div style={{ padding: '0 16px 16px 16px' }}>
                <EscalationViewer spine={spine} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
