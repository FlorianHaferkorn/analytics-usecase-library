'use client';

import type { ApprovalStatus } from '@/lib/governance/approval-types';

interface Props {
  status: ApprovalStatus;
}

const STATUS_STYLES: Record<ApprovalStatus, { bg: string; color: string; label: string }> = {
  draft: { bg: 'var(--panel)', color: 'var(--ink-2)', label: 'Draft' },
  review: { bg: 'rgba(255,184,0,0.2)', color: 'var(--warning)', label: 'In Review' },
  approved: { bg: 'rgba(0,212,170,0.2)', color: 'var(--accent)', label: 'Approved' },
  rejected: { bg: 'rgba(239,68,68,0.2)', color: 'var(--danger)', label: 'Rejected' },
  deprecated: { bg: 'rgba(100,116,139,0.2)', color: 'var(--ink-3)', label: 'Deprecated' },
};

export function ApprovalBadge({ status }: Props) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.draft;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: 'var(--radius-sm)',
        backgroundColor: style.bg,
        color: style.color,
        fontSize: 'var(--text-xs)',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.03em',
      }}
    >
      {style.label}
    </span>
  );
}
