'use client';

import type { CSSProperties, ReactNode } from 'react';

export function StudioDataToolbar({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
      {children}
    </div>
  );
}

const inputBase: CSSProperties = {
  padding: '8px 12px', background: 'var(--panel)',
  border: '1px solid var(--line)', borderRadius: 8,
  color: 'var(--ink)', fontSize: '0.8125rem', lineHeight: 1.5, width: '100%', outline: 'none',
};

export function StudioInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`studio-input ${props.className ?? ''}`} style={{ ...inputBase, ...props.style }} />;
}

export function StudioTextarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`studio-input ${props.className ?? ''}`} style={{ ...inputBase, resize: 'vertical', minHeight: 72, ...props.style }} />;
}

export function StudioSelect(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`studio-input ${props.className ?? ''}`} style={{ ...inputBase, minWidth: 140, cursor: 'pointer', ...props.style }} />;
}

export function StudioFormGrid({ children, columns = '1fr 1fr' }: { children: ReactNode; columns?: string }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: columns, gap: '12px', padding: '16px', background: 'var(--bg-2)', borderRadius: 8, border: '1px solid var(--line)' }}>
      {children}
    </div>
  );
}

export function StudioFormField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ minWidth: 0 }}>
      <label style={{ display: 'block', marginBottom: 6, fontSize: '0.625rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-3)' }}>
        {label}
      </label>
      {children}
    </div>
  );
}

export function StudioTableShell({ children }: { children: ReactNode }) {
  return (
    <div style={{ overflow: 'hidden', borderRadius: 'var(--radius)', border: '1px solid var(--line)', background: 'var(--panel)', boxShadow: 'var(--shadow-sm)' }}>
      {children}
    </div>
  );
}

export function StudioTable({ children }: { children: ReactNode }) {
  return <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>{children}</table>;
}

export function StudioTableHeadCell({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <th style={{
      padding: '11px 16px', textAlign: 'left',
      color: 'var(--ink-4)', fontWeight: 500,
      fontSize: '0.625rem', textTransform: 'uppercase', letterSpacing: '0.06em',
      borderBottom: '1px solid var(--line)', background: 'var(--bg-2)',
      ...style,
    }}>
      {children}
    </th>
  );
}

export function StudioTableCell({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <td style={{ padding: '13px 16px', borderTop: '1px solid var(--line-2)', color: 'var(--ink-2)', lineHeight: 1.55, verticalAlign: 'top', ...style }}>
      {children}
    </td>
  );
}

export function StudioExpandedRow({ children, colSpan }: { children: ReactNode; colSpan: number }) {
  return (
    <tr>
      <td colSpan={colSpan} style={{ background: 'var(--bg-2)', padding: '20px' }}>{children}</td>
    </tr>
  );
}

export function StudioInlineStat({ children }: { children: ReactNode }) {
  return <p style={{ marginTop: '12px', fontSize: '0.75rem', lineHeight: 1.5, color: 'var(--ink-4)' }}>{children}</p>;
}

export function StudioSelectionList({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div style={{ overflow: 'hidden', borderRadius: 'var(--radius)', border: '1px solid var(--line)', background: 'var(--panel)', ...style }}>
      {children}
    </div>
  );
}

export function StudioSelectionItem({
  selected, onClick, primary, secondary, meta, leading,
}: {
  selected: boolean; onClick: () => void;
  primary: ReactNode; secondary?: ReactNode; meta?: ReactNode; leading?: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="studio-selection-item"
      style={{
        width: '100%', display: 'grid',
        gridTemplateColumns: 'auto auto minmax(0,1fr) auto',
        alignItems: 'center', gap: '8px',
        padding: '12px 16px',
        border: 'none', borderBottom: '1px solid var(--line-2)',
        backgroundColor: selected ? 'var(--accent-soft)' : 'transparent',
        color: 'var(--ink)', textAlign: 'left', cursor: 'pointer',
        transition: 'background-color var(--duration-fast)',
      }}
    >
      <input type="checkbox" checked={selected} readOnly style={{ pointerEvents: 'none' }} />
      {leading ? <span style={{ minWidth: 0 }}>{leading}</span> : <span />}
      <span style={{ minWidth: 0 }}>
        <span style={{ display: 'block', fontSize: '0.8125rem', color: 'var(--ink)' }}>{primary}</span>
        {secondary && <span style={{ display: 'block', fontSize: '0.6875rem', color: 'var(--ink-4)', marginTop: 3, lineHeight: 1.5 }}>{secondary}</span>}
      </span>
      {meta && <span style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', textAlign: 'right' }}>{meta}</span>}
    </button>
  );
}

export function StudioCheckbox({
  checked, onChange, label, disabled,
}: {
  checked: boolean; onChange: (checked: boolean) => void; label?: string; disabled?: boolean;
}) {
  return (
    <label style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.5 : 1 }}>
      <input type="checkbox" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
      {label && <span style={{ fontSize: '0.8125rem', color: 'var(--ink-2)', lineHeight: 1.4 }}>{label}</span>}
    </label>
  );
}
