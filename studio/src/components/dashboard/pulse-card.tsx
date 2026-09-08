'use client';

import { motion } from 'framer-motion';
import type { KpiSnapshot } from '@/lib/dashboard/sample-data';

const STATUS_COLORS: Record<string, string> = {
  'on-track': 'var(--positive)',
  'at-risk': 'var(--warn)',
  'off-track': 'var(--negative)',
};

const STATUS_LABELS: Record<string, string> = {
  'on-track': 'On track',
  'at-risk': 'At risk',
  'off-track': 'Off track',
};

interface Props {
  kpi: KpiSnapshot;
  theme?: {
    primary?: string;
    surface?: string;
    text?: string;
    background?: string;
    borderRadius?: number;
    positive?: string;
    negative?: string;
    warning?: string;
  };
}

export function PulseCard({ kpi, theme }: Props) {
  const delta = kpi.value - kpi.previousValue;
  const deltaPercent = ((delta / kpi.previousValue) * 100).toFixed(1);
  const isPositive = delta >= 0;
  const statusColor = kpi.status === 'on-track'
    ? (theme?.positive ?? STATUS_COLORS[kpi.status])
    : kpi.status === 'at-risk'
      ? (theme?.warning ?? STATUS_COLORS[kpi.status])
      : kpi.status === 'off-track'
        ? (theme?.negative ?? STATUS_COLORS[kpi.status])
        : 'var(--ink-4)';
  const statusLabel = STATUS_LABELS[kpi.status] ?? kpi.status;
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
        borderRadius: radius,
        borderLeft: `4px solid ${statusColor}`,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ fontSize: '0.75rem', color: theme?.text ? `color-mix(in srgb, ${theme.text} 68%, transparent)` : 'var(--ink-3)', letterSpacing: '0.01em' }}>
          {kpi.label}
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: statusColor, fontSize: 'var(--text-xs)', whiteSpace: 'nowrap' }}>
          <span aria-hidden="true" style={{ width: 7, height: 7, borderRadius: '50%', backgroundColor: statusColor, display: 'inline-block' }} />
          {statusLabel}
        </span>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <span data-numeric style={{ fontSize: '2rem', fontWeight: 650, letterSpacing: '-0.025em', color: theme?.text ?? 'var(--ink)' }}>
          {kpi.value}
        </span>
        <span style={{ fontSize: '0.875rem', color: theme?.text ? `color-mix(in srgb, ${theme.text} 50%, transparent)` : 'var(--ink-3)', marginLeft: '4px' }}>
          {kpi.unit}
        </span>
      </motion.div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
        <span data-numeric style={{ fontSize: '0.75rem', color: statusColor }}>
          {isPositive ? '↑' : '↓'} {Math.abs(delta).toFixed(1)} ({isPositive ? '+' : ''}{deltaPercent}%)
        </span>
        <span data-numeric style={{ fontSize: 'var(--text-xs)', color: theme?.text ? `color-mix(in srgb, ${theme.text} 62%, transparent)` : 'var(--ink-4)' }}>
          Target: {kpi.target}{kpi.unit}
        </span>
      </div>
    </div>
  );
}
