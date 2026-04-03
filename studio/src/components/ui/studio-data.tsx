'use client';

import type { CSSProperties, ReactNode } from 'react';

export function StudioDataToolbar({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: 'flex', gap: 'var(--sp-1)', marginBottom: 'var(--sp-2)', flexWrap: 'wrap', alignItems: 'center' }}>
      {children}
    </div>
  );
}

export function StudioInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} style={{ ...inputBaseStyle, ...props.style }} />;
}

export function StudioSelect(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} style={{ ...inputBaseStyle, minWidth: '140px', ...props.style }} />;
}

export function StudioFormGrid({ children, columns = '1fr 1fr' }: { children: ReactNode; columns?: string }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: columns, gap: 'var(--sp-1)', padding: 'var(--sp-1-5)', background: 'linear-gradient(180deg, var(--slate-850, #182030), var(--slate-800))', borderRadius: 'var(--radius-md)', border: '1px solid var(--slate-700)' }}>
      {children}
    </div>
  );
}

export function StudioFormField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ minWidth: 0 }}>
      <label style={{ display: 'block', marginBottom: '4px', fontSize: '0.625rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--slate-500)' }}>
        {label}
      </label>
      {children}
    </div>
  );
}

export function StudioTableShell({ children }: { children: ReactNode }) {
  return (
    <div style={{ overflow: 'hidden', padding: 0, borderRadius: 'var(--radius-lg)', border: '1px solid var(--slate-700)', background: 'linear-gradient(180deg, var(--slate-850, #182030), var(--slate-800))' }}>
      {children}
    </div>
  );
}

export function StudioTable({ children }: { children: ReactNode }) {
  return <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>{children}</table>;
}

export function StudioTableHeadCell({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <th style={{ padding: 'var(--sp-1) var(--sp-1-5)', textAlign: 'left', color: 'var(--slate-400)', fontWeight: 600, fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', ...style }}>
      {children}
    </th>
  );
}

export function StudioTableCell({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', borderTop: '1px solid var(--slate-700)', color: 'var(--slate-200)', ...style }}>
      {children}
    </td>
  );
}

export function StudioExpandedRow({ children, colSpan }: { children: ReactNode; colSpan: number }) {
  return (
    <tr>
      <td colSpan={colSpan} style={{ backgroundColor: 'var(--slate-850, #182030)', padding: 'var(--sp-2)' }}>
        {children}
      </td>
    </tr>
  );
}

export function StudioInlineStat({ children }: { children: ReactNode }) {
  return <p style={{ marginTop: 'var(--sp-1)', fontSize: '0.75rem', color: 'var(--slate-500)' }}>{children}</p>;
}

const inputBaseStyle: CSSProperties = {
  padding: 'var(--sp-1) var(--sp-1-5)',
  backgroundColor: 'var(--slate-900)',
  border: '1px solid var(--slate-700)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--slate-100)',
  fontSize: '0.8125rem',
  width: '100%',
};