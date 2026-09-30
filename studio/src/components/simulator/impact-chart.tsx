'use client';

import type { DriverContribution } from '@/lib/simulation/scenario-engine';
import { formatKpiValue } from '@/lib/format/kpi-value';

interface Props {
  contributions: DriverContribution[];
  impactDirection: 'maximize' | 'minimize';
  targetUnit?: string;
  /** Catalog names (`kpi_key`) by KPI ID; the ID itself carries no meaning (D-594). */
  kpiNames?: Record<string, string>;
}

export function ImpactChart({ contributions, impactDirection, targetUnit = '', kpiNames = {} }: Props) {
  const maxAbs = Math.max(...contributions.map((c) => Math.abs(c.contribution)), 0.01);

  return (
    <div
      style={{
        padding: '16px',
        backgroundColor: 'var(--panel)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--line)',
      }}
    >
      <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--ink)', marginBottom: 'var(--pad)' }}>
        Driver Impact
      </h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {contributions.map((c) => {
          const pct = (c.contribution / maxAbs) * 100;
          const isPositive = c.contribution >= 0;
          const isGood = impactDirection === 'maximize' ? isPositive : !isPositive;
          const barColor = c.contribution === 0 ? 'var(--ink-3)' : isGood ? 'var(--accent)' : 'var(--danger)';

          return (
            <div key={c.kpiId} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontSize: 'var(--text-xs)',
                  color: 'var(--ink-2)',
                  minWidth: '140px',
                  textAlign: 'right',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                title={c.kpiId}
              >
                {kpiNames[c.kpiId] ?? c.kpiId}
              </span>
              <div style={{ flex: 1, height: '16px', position: 'relative', backgroundColor: 'var(--bg)', borderRadius: 'var(--radius-sm)' }}>
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
                <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: '1px', backgroundColor: 'var(--line)' }} />
              </div>
              <span style={{ fontSize: 'var(--text-xs)', color: barColor, fontWeight: 600, minWidth: '48px', textAlign: 'right' }}>
                {c.contribution === 0 ? 'No change' : `${c.contribution > 0 ? '+' : ''}${formatKpiValue(c.contribution, targetUnit === '%' ? 'pp' : targetUnit)}`}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
