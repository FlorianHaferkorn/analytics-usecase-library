'use client';

import type { ThemeConfig } from '@/lib/store/project-store';

interface Props {
  theme: ThemeConfig;
}

/** Mini dashboard mockup rendered with the exported theme's custom properties. */
export function CssPreview({ theme }: Props) {
  const radius = `${theme.borderRadius}px`;

  return (
    <div
      style={{
        padding: '16px',
        backgroundColor: theme.background,
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--line)',
        fontFamily: `${theme.fontFamily}, sans-serif`,
      }}
    >
      <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)', marginBottom: '12px' }}>
        Live Preview (exported CSS)
      </p>

      {/* Header bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px',
          backgroundColor: theme.surface,
          borderRadius: radius,
          marginBottom: '8px',
        }}
      >
        <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: theme.primary }} />
        <span style={{ fontSize: '0.75rem', color: theme.text, fontWeight: 600 }}>Dashboard</span>
        <span style={{ marginLeft: 'auto', fontSize: '0.625rem', color: theme.accent }}>v1.0</span>
      </div>

      {/* Metric cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
        {[
          { label: 'Revenue', value: '$12.4M', color: theme.primary },
          { label: 'Margin', value: '34.2%', color: theme.secondary },
          { label: 'Growth', value: '+8.1%', color: theme.accent },
        ].map((card) => (
          <div
            key={card.label}
            style={{
              padding: '8px',
              backgroundColor: theme.surface,
              borderRadius: radius,
              borderLeft: `3px solid ${card.color}`,
            }}
          >
            <p style={{ fontSize: '0.5625rem', color: theme.text, opacity: 0.6 }}>{card.label}</p>
            <p style={{ fontSize: '0.875rem', fontWeight: 700, color: card.color }}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* RAG status row */}
      <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
        {[
          { status: 'On Track', color: '#10B981' },
          { status: 'At Risk', color: '#FFB800' },
          { status: 'Critical', color: '#EF4444' },
        ].map((item) => (
          <div
            key={item.status}
            style={{
              flex: 1,
              padding: '4px 8px',
              backgroundColor: theme.surface,
              borderRadius: radius,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: item.color }} />
            <span style={{ fontSize: '0.5625rem', color: theme.text }}>{item.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
