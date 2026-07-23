'use client';

import { motion } from 'framer-motion';
import type { KpiSnapshot } from '@/lib/dashboard/sample-data';

const STATUS_COLORS: Record<string, string> = {
  'on-track': 'var(--accent)',
  'at-risk': 'var(--warning)',
  'off-track': 'var(--danger)',
};

interface Props {
  kpi: KpiSnapshot;
  theme?: { primary?: string; surface?: string; text?: string; background?: string; borderRadius?: number };
}

export function PulseCard({ kpi, theme }: Props) {
  const delta = kpi.value - kpi.previousValue;
  const deltaPercent = ((delta / kpi.previousValue) * 100).toFixed(1);
  const isPositive = delta >= 0;
  const statusColor = STATUS_COLORS[kpi.status] ?? 'var(--ink-4)';
  const radius = theme?.borderRadius != null ? `${theme.borderRadius / 2}px` : 'var(--radius-lg)';
  const borderColor = theme?.background
    ? `color-mix(in srgb, ${theme.background} 60%, ${theme.text ?? 'var(--ink-3)'})`
    : 'var(--line)';

  return (
    <div
      style={{
        padding: 'var(--pad)',
        backgroundColor: theme?.surface ?? 'var(--panel)',
        borderTop: `1px solid ${borderColor}`,
        borderRight: `1px solid ${borderColor}`,
        borderBottom: `1px solid ${borderColor}`,
        borderLeft: `4px solid ${statusColor}`,
        borderRadius: radius,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ fontSize: '0.6875rem', color: theme?.text ? `color-mix(in srgb, ${theme.text} 60%, transparent)` : 'var(--ink-3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {kpi.label}
        </span>
        <span
          style={{
            width: 8, height: 8, borderRadius: '50%',
            backgroundColor: statusColor,
            display: 'inline-block',
          }}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <span style={{ fontSize: '1.75rem', fontWeight: 700, color: theme?.text ?? 'var(--ink)' }}>
          {kpi.value}
        </span>
        <span style={{ fontSize: '0.875rem', color: theme?.text ? `color-mix(in srgb, ${theme.text} 50%, transparent)` : 'var(--ink-3)', marginLeft: '4px' }}>
          {kpi.unit}
        </span>
      </motion.div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
        <span style={{ fontSize: '0.75rem', color: isPositive ? 'var(--accent)' : 'var(--danger)' }}>
          {isPositive ? '↑' : '↓'} {Math.abs(delta).toFixed(1)} ({isPositive ? '+' : ''}{deltaPercent}%)
        </span>
        <span style={{ fontSize: '0.6875rem', color: theme?.text ? `color-mix(in srgb, ${theme.text} 40%, transparent)` : 'var(--ink-4)' }}>
          Target: {kpi.target}{kpi.unit}
        </span>
      </div>
    </div>
  );
}
