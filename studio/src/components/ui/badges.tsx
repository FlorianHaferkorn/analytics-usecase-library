'use client';

import type { ReactNode } from 'react';

// ── Pill ──────────────────────────────────────────────────────────────────────

type PillTone = 'neutral' | 'accent' | 'positive' | 'warn' | 'draft' | 'danger' | 'info';

const PILL_TONES: Record<PillTone, { bg: string; fg: string; bd: string }> = {
  neutral:  { bg: 'var(--bg-2)',        fg: 'var(--ink-2)',       bd: 'var(--line)' },
  accent:   { bg: 'var(--accent-soft)', fg: 'var(--accent)',      bd: 'transparent' },
  positive: { bg: 'var(--positive-bg)', fg: 'var(--positive-fg)', bd: 'transparent' },
  warn:     { bg: 'var(--warn-soft)', fg: 'var(--warning)', bd: 'transparent' },
  draft:    { bg: 'var(--line-2)',       fg: 'var(--ink-3)',       bd: 'var(--line)' },
  danger:   { bg: 'var(--negative-bg)', fg: 'var(--negative-fg)', bd: 'transparent' },
  info:     { bg: 'var(--accent-soft)', fg: 'var(--info)', bd: 'transparent' },
};

export function Pill({ tone = 'neutral', children }: { tone?: PillTone; children: ReactNode }) {
  const t = PILL_TONES[tone];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '2px 8px', borderRadius: 999,
      fontSize: 'var(--text-xs)', fontWeight: 500, letterSpacing: '-0.005em',
      background: t.bg, color: t.fg, border: `1px solid ${t.bd}`,
      whiteSpace: 'nowrap',
    }}>
      {children}
    </span>
  );
}

// ── StatusDot ─────────────────────────────────────────────────────────────────

type StatusTone = 'certified' | 'review' | 'draft' | 'active' | 'inactive';

const DOT_COLORS: Record<StatusTone, string> = {
  certified: 'var(--success)',
  active:    'var(--success)',
  review:    'var(--warning)',
  draft:     'var(--ink-4)',
  inactive:  'var(--ink-4)',
};

export function StatusDot({ status }: { status: StatusTone | string }) {
  return (
    <span style={{
      display: 'inline-block', width: 6, height: 6, borderRadius: 99, flexShrink: 0,
      background: DOT_COLORS[status as StatusTone] ?? 'var(--ink-4)',
    }} />
  );
}

// ── KBD ───────────────────────────────────────────────────────────────────────

export function KBD({ children }: { children: ReactNode }) {
  return (
    <kbd style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      minWidth: 20, minHeight: 20, padding: '0 var(--space-1)',
      fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', fontWeight: 500,
      color: 'var(--ink-3)', background: 'var(--bg-2)',
      border: '1px solid var(--line)', borderRadius: 5,
      lineHeight: 1,
    }}>
      {children}
    </kbd>
  );
}
