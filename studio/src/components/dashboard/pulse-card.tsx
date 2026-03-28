'use client';

import { motion } from 'framer-motion';
import type { KpiSnapshot } from '@/lib/dashboard/sample-data';

const STATUS_COLORS: Record<string, string> = {
  'on-track': 'var(--mint)',
  'at-risk': 'var(--gold)',
  'off-track': 'var(--danger)',
};

interface Props {
  kpi: KpiSnapshot;
  theme?: { primary?: string; surface?: string; text?: string };
}

export function PulseCard({ kpi, theme }: Props) {
  const delta = kpi.value - kpi.previousValue;
  const deltaPercent = ((delta / kpi.previousValue) * 100).toFixed(1);
  const isPositive = delta >= 0;
  const statusColor = STATUS_COLORS[kpi.status] ?? 'var(--slate-500)';

  return (
    <div
      style={{
        padding: 'var(--sp-2)',
        backgroundColor: theme?.surface ?? 'var(--slate-800)',
        border: `1px solid var(--slate-700)`,
        borderRadius: 'var(--radius-lg)',
        borderLeft: `4px solid ${statusColor}`,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-1)' }}>
        <span style={{ fontSize: '0.6875rem', color: 'var(--slate-400)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
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
        <span style={{ fontSize: '1.75rem', fontWeight: 700, color: theme?.text ?? 'var(--slate-100)' }}>
          {kpi.value}
        </span>
        <span style={{ fontSize: '0.875rem', color: 'var(--slate-400)', marginLeft: '4px' }}>
          {kpi.unit}
        </span>
      </motion.div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'var(--sp-1)' }}>
        <span style={{ fontSize: '0.75rem', color: isPositive ? 'var(--mint)' : 'var(--danger)' }}>
          {isPositive ? '↑' : '↓'} {Math.abs(delta).toFixed(1)} ({isPositive ? '+' : ''}{deltaPercent}%)
        </span>
        <span style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>
          Target: {kpi.target}{kpi.unit}
        </span>
      </div>
    </div>
  );
}
