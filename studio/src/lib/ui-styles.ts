/** Shared inline style objects for consistent UI. */

import type { CSSProperties } from 'react';

export const cardStyle: CSSProperties = {
  padding: 'var(--sp-2)',
  backgroundColor: 'var(--slate-800)',
  borderRadius: 'var(--radius-lg)',
  border: '1px solid var(--slate-700)',
};

export const tableContainerStyle: CSSProperties = {
  ...cardStyle,
  overflow: 'hidden',
  padding: 0,
};

export const tableStyle: CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: '0.8125rem',
};

export const thStyle: CSSProperties = {
  padding: 'var(--sp-1) var(--sp-1-5)',
  textAlign: 'left',
  color: 'var(--slate-400)',
  fontWeight: 600,
  fontSize: '0.6875rem',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
};

export const tdStyle: CSSProperties = {
  padding: 'var(--sp-1) var(--sp-1-5)',
  borderTop: '1px solid var(--slate-700)',
  color: 'var(--slate-200)',
};

export const expandedRowStyle: CSSProperties = {
  backgroundColor: 'var(--slate-850, #182030)',
  padding: 'var(--sp-2)',
};

export const filterInputStyle: CSSProperties = {
  padding: 'var(--sp-1) var(--sp-1-5)',
  backgroundColor: 'var(--slate-900)',
  border: '1px solid var(--slate-700)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--slate-100)',
  fontSize: '0.8125rem',
};

export const filterSelectStyle: CSSProperties = {
  ...filterInputStyle,
  minWidth: '140px',
};

/** Status color for action codes. */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'active': return 'var(--mint)';
    case 'draft': return 'var(--gold)';
    case 'deprecated': return 'var(--danger)';
    default: return 'var(--slate-500)';
  }
}
