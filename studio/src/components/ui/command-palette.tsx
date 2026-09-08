'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { KBD } from './badges';

export interface PaletteItem {
  kind: 'kpi' | 'usecase' | 'bracket' | 'action' | 'dimension' | 'page' | 'action-item';
  id: string;
  label: string;
  /** Display subtitle (domain tag, entity type label). Not a navigation path. */
  sub?: string;
  /** Detail or page route; preferred for navigation when set. */
  href?: string;
  status?: string;
  onSelect?: () => void;
}

export type SerializablePaletteItem = Omit<PaletteItem, 'onSelect'>;

interface Props {
  items?: PaletteItem[];
  onNavigate?: (path: string) => void;
}

const KIND_ICON: Record<string, string> = {
  kpi: 'K',
  usecase: 'U',
  bracket: 'B',
  action: 'A',
  dimension: 'D',
  page: '→',
  'action-item': '⚡',
};

/** Canonical routes (see studio/next.config.ts redirects for legacy paths). */
const NAV_ACTIONS: PaletteItem[] = [
  { kind: 'page', id: 'overview', label: 'Open Overview', href: '/overview' },
  { kind: 'page', id: 'canvas', label: 'Open Canvas', href: '/canvas' },
  { kind: 'page', id: 'library', label: 'Open Library', href: '/library' },
  { kind: 'page', id: 'delivery', label: 'Open Delivery', href: '/delivery' },
  { kind: 'page', id: 'registry', label: 'Open Registry Health', href: '/health' },
  { kind: 'page', id: 'templates', label: 'Open Report Templates', href: '/templates' },
];

export function CommandPalette({ items = [], onNavigate }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const close = useCallback(() => { setOpen(false); setQuery(''); }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === 'Escape') close();
    };
    const onCustom = () => setOpen(true);
    window.addEventListener('keydown', onKey);
    window.addEventListener('studio:open-command-palette', onCustom);
    return () => {
      window.removeEventListener('keydown', onKey);
      window.removeEventListener('studio:open-command-palette', onCustom);
    };
  }, [close]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 10);
  }, [open]);

  if (!open) return null;

  const q = query.toLowerCase();
  const filtered = (q ? items : items.slice(0, 6))
    .filter((it) => !q || it.label.toLowerCase().includes(q) || (it.sub ?? '').toLowerCase().includes(q));

  const actions = q ? [] : NAV_ACTIONS;

  return (
    <div
      onClick={close}
      style={{
        position: 'fixed', inset: 0, zIndex: 'var(--z-modal)' as never,
        background: 'rgba(11,11,12,0.3)', backdropFilter: 'blur(4px)',
        display: 'grid', placeItems: 'start center', paddingTop: '14vh',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 600, maxWidth: '90vw',
          background: 'var(--panel)', borderRadius: 12,
          border: '1px solid var(--line)', boxShadow: 'var(--shadow-lg)',
          overflow: 'hidden',
        }}
      >
        {/* Search input */}
        <div style={{ padding: '13px 18px', display: 'flex', alignItems: 'center', gap: 12, borderBottom: '1px solid var(--line-2)' }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="var(--ink-3)" strokeWidth="1.5" strokeLinecap="round">
            <circle cx="7" cy="7" r="4" /><path d="m10 10 3.5 3.5" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search KPIs, use cases, actions, or type a page name…"
            style={{ flex: 1, background: 'transparent', border: 0, outline: 0, fontSize: '0.9375rem', color: 'var(--ink)' }}
          />
          <KBD>esc</KBD>
        </div>

        {/* Results */}
        <div style={{ maxHeight: 400, overflow: 'auto', padding: 8 }}>
          {actions.length > 0 && (
            <>
              <SectionHead>Pages</SectionHead>
              {actions.map((it) => (
                <PaletteRow
                  key={it.id}
                  item={it}
                  onSelect={() => {
                    onNavigate?.(it.href ?? (it.sub?.startsWith('/') ? it.sub : '/'));
                    close();
                  }}
                />
              ))}
            </>
          )}

          {filtered.length > 0 && (
            <>
              {!q && <SectionHead>Framework</SectionHead>}
              {filtered.map((it) => (
                <PaletteRow key={it.kind + it.id} item={it} onSelect={() => { it.onSelect?.(); close(); }} />
              ))}
            </>
          )}

          {q && filtered.length === 0 && actions.length === 0 && (
            <div style={{ padding: 24, textAlign: 'center', color: 'var(--ink-3)', fontSize: '0.875rem' }}>
              No results for &ldquo;{query}&rdquo;
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SectionHead({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ padding: '8px 10px 4px', fontSize: 'var(--text-xs)', fontWeight: 500, color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
      {children}
    </div>
  );
}

function PaletteRow({ item, onSelect }: { item: PaletteItem; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      style={{
        width: '100%', padding: '8px 10px',
        display: 'flex', alignItems: 'center', gap: 10,
        borderRadius: 7, fontSize: '0.8125rem', color: 'var(--ink)',
        textAlign: 'left', border: 'none', background: 'transparent', cursor: 'pointer',
        transition: 'background var(--duration-fast)',
      }}
      onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = 'var(--hover)')}
      onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = 'transparent')}
    >
      <span style={{
        width: 20, height: 20, borderRadius: 5, flexShrink: 0,
        background: 'var(--bg-2)', border: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--ink-3)',
      }}>
        {KIND_ICON[item.kind] ?? '·'}
      </span>
      <span style={{ flex: 1 }}>{item.label}</span>
      {item.sub && (
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--ink-4)' }}>
          {item.sub}
        </span>
      )}
      {item.status && (
        <span style={{ width: 6, height: 6, borderRadius: 99, background: item.status === 'certified' ? 'oklch(0.58 0.16 150)' : 'var(--ink-4)', flexShrink: 0 }} />
      )}
    </button>
  );
}
