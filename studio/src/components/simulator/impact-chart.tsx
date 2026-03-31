'use client';

import type { DriverContribution } from '@/lib/simulation/scenario-engine';

interface Props {
  contributions: DriverContribution[];
  impactDirection: 'maximize' | 'minimize';
}

export function ImpactChart({ contributions, impactDirection }: Props) {
  const maxAbs = Math.max(...contributions.map((c) => Math.abs(c.contribution)), 0.01);

  return (
    <div
      style={{
        padding: 'var(--sp-2)',
        backgroundColor: 'var(--slate-800)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--slate-700)',
      }}
    >
      <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--slate-100)', marginBottom: 'var(--sp-1-5)' }}>
        Driver Impact
      </h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
        {contributions.map((c) => {
          const pct = (c.contribution / maxAbs) * 100;
          const isPositive = c.contribution >= 0;
          const isGood = impactDirection === 'maximize' ? isPositive : !isPositive;
          const barColor = isGood ? 'var(--mint)' : 'var(--danger)';

          return (
            <div key={c.kpiId} style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)' }}>
              <span
                style={{
                  fontSize: '0.6875rem',
                  color: 'var(--slate-300)',
                  minWidth: '140px',
                  textAlign: 'right',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                title={c.kpiId}
              >
                {c.kpiId.split('.').slice(-2).join('.')}
              </span>
              <div style={{ flex: 1, height: '16px', position: 'relative', backgroundColor: 'var(--slate-900)', borderRadius: 'var(--radius-sm)' }}>
                {isPositive ? (
                  <div
                    style={{
                      position: 'absolute',
                      left: '50%',
                      height: '100%',
                      width: `${Math.min(Math.abs(pct) / 2, 50)}%`,
                      backgroundColor: barColor,
                      borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                    }}
                  />
                ) : (
                  <div
                    style={{
                      position: 'absolute',
                      right: '50%',
                      height: '100%',
                      width: `${Math.min(Math.abs(pct) / 2, 50)}%`,
                      backgroundColor: barColor,
                      borderRadius: 'var(--radius-sm) 0 0 var(--radius-sm)',
                    }}
                  />
                )}
                {/* Center line */}
                <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: '1px', backgroundColor: 'var(--slate-600)' }} />
              </div>
              <span style={{ fontSize: '0.6875rem', color: barColor, fontWeight: 600, minWidth: '48px', textAlign: 'right' }}>
                {c.contribution >= 0 ? '+' : ''}{c.contribution.toFixed(2)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
