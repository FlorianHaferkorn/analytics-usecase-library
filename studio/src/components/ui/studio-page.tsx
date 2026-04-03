'use client';

import type { CSSProperties, ReactNode } from 'react';

type Tone = 'default' | 'info' | 'success' | 'warning';

function getToneAccent(tone: Tone): string {
  switch (tone) {
    case 'info':
      return 'var(--info)';
    case 'success':
      return 'var(--mint)';
    case 'warning':
      return 'var(--gold)';
    default:
      return 'var(--slate-300)';
  }
}

export function StudioPage({ children, fill = false, style }: { children: ReactNode; fill?: boolean; style?: CSSProperties }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--sp-2)',
        minHeight: fill ? 'calc(100vh - 56px - var(--sp-6))' : undefined,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

export function StudioPageHeader({
  eyebrow,
  title,
  description,
  badge,
  actions,
  tone = 'default',
}: {
  eyebrow?: string;
  title: string;
  description: string;
  badge?: string;
  actions?: ReactNode;
  tone?: Tone;
}) {
  const accent = getToneAccent(tone);

  return (
    <div
      style={{
        padding: 'var(--sp-2) var(--sp-2-5)',
        borderRadius: 'var(--radius-xl)',
        border: `1px solid color-mix(in srgb, ${accent} 24%, var(--slate-700))`,
        background: `linear-gradient(135deg, color-mix(in srgb, var(--slate-850, #17202e) 86%, ${accent} 14%), var(--slate-800))`,
        boxShadow: `0 20px 48px color-mix(in srgb, ${accent} 10%, transparent)`,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: 'var(--sp-2)',
        flexWrap: 'wrap',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxWidth: '960px' }}>
        {eyebrow ? (
          <span style={{ fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: accent, fontWeight: 700 }}>
            {eyebrow}
          </span>
        ) : null}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <h1 style={{ fontSize: '1.375rem', lineHeight: 1.1, fontWeight: 700, color: 'var(--slate-50)', margin: 0 }}>
            {title}
          </h1>
          {badge ? (
            <span
              style={{
                padding: '4px 10px',
                borderRadius: '9999px',
                border: `1px solid color-mix(in srgb, ${accent} 30%, transparent)`,
                backgroundColor: `color-mix(in srgb, ${accent} 12%, transparent)`,
                color: 'var(--slate-100)',
                fontSize: '0.6875rem',
                fontWeight: 600,
              }}
            >
              {badge}
            </span>
          ) : null}
        </div>
        <p style={{ margin: 0, fontSize: '0.8125rem', lineHeight: 1.55, color: 'var(--slate-300)' }}>
          {description}
        </p>
      </div>
      {actions ? <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)', flexWrap: 'wrap' }}>{actions}</div> : null}
    </div>
  );
}

export function StudioMetricBar({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--sp-1)' }}>
      {children}
    </div>
  );
}

export function StudioMetric({
  label,
  value,
  meta,
  tone = 'default',
}: {
  label: string;
  value: string | number;
  meta?: string;
  tone?: Tone;
}) {
  const accent = getToneAccent(tone);

  return (
    <div
      style={{
        padding: 'var(--sp-1-5)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--slate-700)',
        background: `linear-gradient(180deg, color-mix(in srgb, var(--slate-800) 88%, ${accent} 12%), var(--slate-800))`,
        minHeight: '88px',
      }}
    >
      <p style={{ margin: 0, marginBottom: '4px', fontSize: '0.625rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</p>
      <p style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: accent }}>{value}</p>
      {meta ? <p style={{ margin: 0, marginTop: '4px', fontSize: '0.6875rem', color: 'var(--slate-400)' }}>{meta}</p> : null}
    </div>
  );
}

export function StudioPanel({
  title,
  description,
  action,
  children,
  tone = 'default',
  style,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  tone?: Tone;
  style?: CSSProperties;
}) {
  const accent = getToneAccent(tone);

  return (
    <section
      style={{
        padding: 'var(--sp-2)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--slate-700)',
        background: `linear-gradient(180deg, color-mix(in srgb, var(--slate-800) 90%, ${accent} 10%), var(--slate-800))`,
        ...style,
      }}
    >
      {(title || description || action) ? (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--sp-1)', marginBottom: 'var(--sp-1)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {title ? <h3 style={{ margin: 0, fontSize: '0.8125rem', fontWeight: 600, color: 'var(--slate-100)' }}>{title}</h3> : null}
            {description ? <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--slate-400)' }}>{description}</p> : null}
          </div>
          {action ? <div style={{ flexShrink: 0 }}>{action}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}

export function StudioEmptyState({ title, description }: { title: string; description: ReactNode }) {
  return (
    <div
      style={{
        padding: 'var(--sp-4)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--slate-700)',
        background: 'linear-gradient(180deg, var(--slate-800), var(--slate-850, #182030))',
        textAlign: 'center',
      }}
    >
      <p style={{ margin: 0, marginBottom: 'var(--sp-1)', fontSize: '0.875rem', color: 'var(--slate-200)', fontWeight: 600 }}>{title}</p>
      <div style={{ fontSize: '0.75rem', color: 'var(--slate-500)' }}>{description}</div>
    </div>
  );
}

export function StudioToolbar({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--sp-1)',
        flexWrap: 'wrap',
        padding: 'var(--sp-1-5)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--slate-700)',
        background: 'linear-gradient(180deg, var(--slate-850, #182030), var(--slate-800))',
        ...style,
      }}
    >
      {children}
    </div>
  );
}

export function StudioButton({
  children,
  onClick,
  tone = 'default',
  variant = 'secondary',
  disabled = false,
  style,
}: {
  children: ReactNode;
  onClick?: () => void;
  tone?: Tone;
  variant?: 'primary' | 'secondary' | 'ghost';
  disabled?: boolean;
  style?: CSSProperties;
}) {
  const accent = getToneAccent(tone);

  const appearance: Record<typeof variant, CSSProperties> = {
    primary: {
      backgroundColor: accent,
      border: `1px solid ${accent}`,
      color: 'var(--slate-950)',
      fontWeight: 700,
    },
    secondary: {
      backgroundColor: `color-mix(in srgb, ${accent} 12%, var(--slate-900))`,
      border: `1px solid color-mix(in srgb, ${accent} 32%, var(--slate-700))`,
      color: 'var(--slate-100)',
      fontWeight: 600,
    },
    ghost: {
      backgroundColor: 'transparent',
      border: '1px solid var(--slate-700)',
      color: 'var(--slate-300)',
      fontWeight: 500,
    },
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '8px 12px',
        borderRadius: 'var(--radius-md)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.55 : 1,
        fontSize: '0.75rem',
        transition: 'all var(--duration-fast) var(--ease-out)',
        ...appearance[variant],
        ...style,
      }}
    >
      {children}
    </button>
  );
}

export function StudioSegmentedControl<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
}) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', backgroundColor: 'var(--slate-900)', borderRadius: 'var(--radius-md)', border: '1px solid var(--slate-700)', overflow: 'hidden' }}>
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            style={{
              padding: '7px 12px',
              backgroundColor: active ? 'var(--slate-700)' : 'transparent',
              border: 'none',
              color: active ? 'var(--slate-50)' : 'var(--slate-500)',
              fontSize: '0.75rem',
              fontWeight: active ? 600 : 500,
              cursor: 'pointer',
            }}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

export function StudioField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ minWidth: 0 }}>
      <label style={{ display: 'block', fontSize: '0.625rem', color: 'var(--slate-500)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {label}
      </label>
      {children}
    </div>
  );
}