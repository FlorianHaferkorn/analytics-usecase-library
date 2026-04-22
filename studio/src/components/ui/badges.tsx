'use client';

import type { ReactNode } from 'react';

// ── Pill ──────────────────────────────────────────────────────────────────────

type PillTone = 'neutral' | 'accent' | 'positive' | 'warn' | 'draft' | 'danger' | 'info';

const PILL_TONES: Record<PillTone, { bg: string; fg: string; bd: string }> = {
  neutral:  { bg: 'var(--bg-2)',        fg: 'var(--ink-2)',       bd: 'var(--line)' },
  accent:   { bg: 'var(--accent-soft)', fg: 'var(--accent)',      bd: 'transparent' },
  positive: { bg: 'oklch(0.94 0.05 150 / 0.5)', fg: 'oklch(0.42 0.13 150)', bd: 'transparent' },
  warn:     { bg: 'oklch(0.95 0.05 75 / 0.5)',  fg: 'oklch(0.48 0.15 60)',  bd: 'transparent' },
  draft:    { bg: 'var(--line-2)',       fg: 'var(--ink-3)',       bd: 'var(--line)' },
  danger:   { bg: 'oklch(0.95 0.05 15 / 0.5)',  fg: 'oklch(0.48 0.15 15)',  bd: 'transparent' },
  info:     { bg: 'oklch(0.94 0.05 240 / 0.5)', fg: 'oklch(0.45 0.15 240)', bd: 'transparent' },
};

export function Pill({ tone = 'neutral', children }: { tone?: PillTone; children: ReactNode }) {
  const t = PILL_TONES[tone];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '2px 8px', borderRadius: 999,
      fontSize: '0.6875rem', fontWeight: 500, letterSpacing: '-0.005em',
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
  certified: 'oklch(0.58 0.16 150)',
  active:    'oklch(0.58 0.16 150)',
  review:    'oklch(0.65 0.16 75)',
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
      minWidth: 18, height: 18, padding: '0 5px',
      fontFamily: 'var(--font-mono)', fontSize: '0.625rem', fontWeight: 500,
      color: 'var(--ink-3)', background: 'var(--bg-2)',
      border: '1px solid var(--line)', borderRadius: 5,
      lineHeight: 1,
    }}>
      {children}
    </kbd>
  );
}
