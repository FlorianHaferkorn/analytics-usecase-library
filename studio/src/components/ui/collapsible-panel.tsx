'use client';

import { useState, type ReactNode } from 'react';
import { StudioPanel } from './studio-page';
import type { CSSProperties } from 'react';

type Tone = 'default' | 'info' | 'success' | 'warning';

interface Props {
  title: string;
  description?: string;
  tone?: Tone;
  style?: CSSProperties;
  defaultOpen?: boolean;
  children: ReactNode;
}

export function CollapsiblePanel({ title, description, tone, style, defaultOpen = true, children }: Props) {
  const [open, setOpen] = useState(defaultOpen);

  const toggle = (
    <button
      onClick={() => setOpen((o) => !o)}
      style={{
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        padding: '2px 8px',
        fontSize: '0.6875rem',
        color: 'var(--slate-400)',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        borderRadius: 'var(--radius-sm)',
        transition: 'color 0.15s ease',
      }}
      onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.color = 'var(--slate-200)')}
      onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.color = 'var(--slate-400)')}
    >
      <span style={{ fontSize: '0.5rem', display: 'inline-block', transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease' }}>▲</span>
      {open ? 'Collapse' : 'Expand'}
    </button>
  );

  return (
    <StudioPanel
      title={title}
      description={open ? description : undefined}
      tone={tone}
      style={style}
      action={toggle}
    >
      {open ? children : null}
    </StudioPanel>
  );
}
