'use client';

import type { CSSProperties, ReactNode } from 'react';

type Tone = 'default' | 'info' | 'success' | 'warning';

function toneColor(tone: Tone): string {
  if (tone === 'info')    return 'var(--info)';
  if (tone === 'success') return 'var(--accent)';
  if (tone === 'warning') return 'var(--gold)';
  return 'var(--ink-4)';
}

// ── Page shell ──────────────────────────────────────────────────────────────

export function StudioPage({ children, fill = false, style }: { children: ReactNode; fill?: boolean; style?: CSSProperties }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', gap: 'var(--gap)',
      height: fill ? 'calc(100vh - var(--h-row) - var(--pad) * 2)' : undefined,
      ...style,
    }}>
      {children}
    </div>
  );
}

// ── Page header ──────────────────────────────────────────────────────────────

export function StudioPageHeader({
  eyebrow, title, description, badge, actions, tone = 'default',
}: {
  eyebrow?: string; title: string; description: string;
  badge?: string; actions?: ReactNode; tone?: Tone;
}) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
      gap: 'var(--sp-2)', flexWrap: 'wrap',
      paddingBottom: 'var(--gap)', borderBottom: '1px solid var(--line)',
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxWidth: 800 }}>
        {eyebrow && (
          <span style={{ fontSize: '0.625rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-3)', fontWeight: 600 }}>
            {eyebrow}
          </span>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <h1 style={{ margin: 0, fontSize: '1.625rem', fontWeight: 500, letterSpacing: '-0.025em', color: 'var(--ink)' }}>
            {title}
          </h1>
          {badge && (
            <span style={{
              padding: '3px 10px', borderRadius: 999,
              border: `1px solid color-mix(in srgb, ${toneColor(tone)} 30%, transparent)`,
              backgroundColor: `color-mix(in srgb, ${toneColor(tone)} 10%, transparent)`,
              color: toneColor(tone), fontSize: '0.625rem', fontWeight: 600, letterSpacing: '0.04em',
            }}>
              {badge}
            </span>
          )}
        </div>
        <p style={{ margin: 0, fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--ink-3)' }}>{description}</p>
      </div>
      {actions && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)', flexShrink: 0 }}>{actions}</div>
      )}
    </div>
  );
}

// ── Metric bar ───────────────────────────────────────────────────────────────

export function StudioMetricBar({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 'var(--sp-1)' }}>
      {children}
    </div>
  );
}

export function StudioMetric({
  label, value, meta, tone = 'default', trend,
}: {
  label: string; value: string | number; meta?: string; tone?: Tone; trend?: string;
}) {
  const positive = trend?.startsWith('+');
  const negative = trend?.startsWith('−') || trend?.startsWith('-');
  void tone;

  return (
    <div style={{
      padding: 'var(--sp-2)', background: 'var(--panel)',
      border: '1px solid var(--line)', borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow-sm)', display: 'flex', flexDirection: 'column', gap: 6,
    }}>
      <div style={{ fontSize: '0.6875rem', color: 'var(--ink-3)', letterSpacing: '-0.005em' }}>{label}</div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: '1.75rem', fontWeight: 500, letterSpacing: '-0.025em', color: 'var(--ink)', fontFamily: 'var(--font-display)' }}>
          {value}
        </span>
        {trend && (
          <span style={{ fontSize: '0.6875rem', color: positive ? 'var(--positive-fg)' : negative ? 'var(--negative-fg)' : 'var(--ink-4)' }}>
            {trend}
          </span>
        )}
      </div>
      {meta && <div style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', lineHeight: 1.5 }}>{meta}</div>}
    </div>
  );
}

// ── Panel ─────────────────────────────────────────────────────────────────────

export function StudioPanel({
  title, description, action, children, tone = 'default', style,
}: {
  title?: string; description?: string; action?: ReactNode;
  children: ReactNode; tone?: Tone; style?: CSSProperties;
}) {
  const hasHeader = !!(title || description || action);
  void tone;

  return (
    <section style={{
      background: 'var(--panel)', border: '1px solid var(--line)',
      borderRadius: 'var(--radius)', boxShadow: 'var(--shadow-sm)',
      overflow: 'hidden', display: 'flex', flexDirection: 'column',
      ...style,
    }}>
      {hasHeader && (
        <div style={{
          padding: '18px var(--pad)', borderBottom: '1px solid var(--line-2)',
          display: 'flex', alignItems: 'flex-start',
          justifyContent: 'space-between', gap: 'var(--sp-2)', flexShrink: 0,
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxWidth: '72ch' }}>
            {title && <h3 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 500, letterSpacing: '-0.01em', color: 'var(--ink)' }}>{title}</h3>}
            {description && <p style={{ margin: 0, fontSize: '0.8125rem', lineHeight: 1.6, color: 'var(--ink-3)' }}>{description}</p>}
          </div>
          {action && <div style={{ flexShrink: 0 }}>{action}</div>}
        </div>
      )}
      <div style={{ padding: 'var(--pad)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-1-5)', flex: 1, minHeight: 0 }}>
        {children}
      </div>
    </section>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

export function StudioEmptyState({ title, description }: { title: string; description: ReactNode }) {
  return (
    <div style={{
      padding: 'var(--sp-6)', background: 'var(--bg-2)',
      border: '1px solid var(--line)', borderRadius: 'var(--radius)', textAlign: 'center',
    }}>
      <p style={{ margin: 0, marginBottom: 6, fontSize: '0.9375rem', fontWeight: 500, color: 'var(--ink)' }}>{title}</p>
      <div style={{ fontSize: '0.8125rem', lineHeight: 1.65, color: 'var(--ink-3)', maxWidth: '56ch', margin: '0 auto' }}>{description}</div>
    </div>
  );
}

// ── Toolbar ───────────────────────────────────────────────────────────────────

export function StudioToolbar({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 'var(--sp-1)', flexWrap: 'wrap',
      padding: '10px 16px', background: 'var(--panel)',
      border: '1px solid var(--line)', borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow-sm)',
      ...style,
    }}>
      {children}
    </div>
  );
}

// ── Button ────────────────────────────────────────────────────────────────────

export function StudioButton({
  children, onClick, variant = 'secondary', disabled = false, style,
}: {
  children: ReactNode;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  tone?: Tone;
  variant?: 'primary' | 'secondary' | 'ghost' | 'accent';
  disabled?: boolean;
  style?: CSSProperties;
}) {
  const appearances: Record<string, CSSProperties> = {
    primary:   { background: 'var(--ink)',    color: 'var(--bg)',         border: '1px solid var(--ink)',    fontWeight: 500 },
    accent:    { background: 'var(--accent)', color: 'var(--accent-ink)', border: '1px solid var(--accent)', fontWeight: 500 },
    secondary: { background: 'var(--panel)',  color: 'var(--ink-2)',      border: '1px solid var(--line)',   fontWeight: 500 },
    ghost:     { background: 'transparent',   color: 'var(--ink-3)',      border: '1px solid transparent' },
  };

  return (
    <button
      className="studio-button"
      onClick={onClick}
      disabled={disabled}
      style={{
        height: 32, padding: '0 12px', borderRadius: 7,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1, fontSize: '0.8125rem',
        display: 'inline-flex', alignItems: 'center', gap: 6,
        transition: 'opacity var(--duration-fast)',
        ...appearances[variant],
        ...style,
      }}
    >
      {children}
    </button>
  );
}

// ── Segmented control ─────────────────────────────────────────────────────────

export function StudioSegmentedControl<T extends string>({
  value, options, onChange,
}: {
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
  tone?: Tone;
}) {
  return (
    <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--line)' }}>
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            className="studio-button"
            onClick={() => onChange(opt.value)}
            style={{
              padding: '9px 14px', background: 'transparent',
              color: active ? 'var(--ink)' : 'var(--ink-3)',
              fontSize: '0.8125rem', fontWeight: active ? 500 : 400,
              border: 'none',
              borderBottom: `1.5px solid ${active ? 'var(--accent)' : 'transparent'}`,
              cursor: 'pointer', marginBottom: -1,
              transition: 'color var(--duration-fast), border-color var(--duration-fast)',
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

// ── Form field ────────────────────────────────────────────────────────────────

export function StudioField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ minWidth: 0 }}>
      <label style={{ display: 'block', marginBottom: 5, fontSize: '0.625rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-3)' }}>
        {label}
      </label>
      {children}
    </div>
  );
}
