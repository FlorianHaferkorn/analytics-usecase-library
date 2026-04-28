'use client';

import { useCallback } from 'react';
import { usePathname } from 'next/navigation';
import { NAV_ITEMS } from '@/lib/navigation';
import { useProjectStore } from '@/lib/store/project-store';
import { DriftBadge } from '@/components/registry/drift-badge';
import { NotificationBell } from '@/components/notifications/notification-bell';
import { ProjectSwitcher } from '@/components/AppShell/ProjectSwitcher';
import { PhIcon } from './ph-icon';
import { KbdShortcut } from './kbd-shortcut';

/** Build breadcrumb segments from the current pathname. */
function useBreadcrumbs(pathname: string): string[] {
  const match = NAV_ITEMS.find((item) => pathname.startsWith(item.href));
  if (!match) return ['Studio'];
  const mode = ['catalog', 'lineage', 'drift', 'health', 'approvals'].some((p) =>
    pathname.startsWith('/' + p)
  )
    ? 'Registry'
    : 'Forge';
  return [mode, match.label];
}

export function StudioHeader() {
  const pathname = usePathname();
  const crumbs = useBreadcrumbs(pathname);
  const driftReport = useProjectStore((s) => s.driftReport);
  const driftLoading = useProjectStore((s) => s.driftLoading);
  const notifications = useProjectStore((s) => s.notifications);
  const activeCount = notifications.filter((n) => !n.dismissed).length;
  const setDriftReport = useProjectStore((s) => s.setDriftReport);
  const setDriftLoading = useProjectStore((s) => s.setDriftLoading);

  const runScan = useCallback(async () => {
    setDriftLoading(true);
    try {
      const res = await fetch('/api/validate/drift');
      if (res.ok) setDriftReport(await res.json());
    } finally {
      setDriftLoading(false);
    }
  }, [setDriftReport, setDriftLoading]);

  return (
    <header
      style={{
        height: 56,
        flexShrink: 0,
        borderBottom: '1px solid var(--line)',
        padding: '0 20px',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        background: 'var(--bg)',
      }}
    >
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
        {crumbs.map((crumb, i) => (
          <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {i > 0 && (
              <PhIcon name="caret-right" size={12} style={{ color: 'var(--ink-4)', flexShrink: 0 }} />
            )}
            <span style={{
              color: i === crumbs.length - 1 ? 'var(--ink)' : 'var(--ink-3)',
              fontWeight: i === crumbs.length - 1 ? 500 : 400,
            }}>
              {crumb}
            </span>
          </span>
        ))}
      </div>

      <div style={{ flex: 1 }} />

      {/* Search */}
      <button
        onClick={() => window.dispatchEvent(new CustomEvent('studio:open-command-palette'))}
        style={{
          height: 30, padding: '0 10px',
          display: 'flex', alignItems: 'center', gap: 8, borderRadius: 7,
          border: '1px solid var(--line)', color: 'var(--ink-3)', fontSize: 12.5,
          background: 'transparent', cursor: 'pointer',
        }}
      >
        <PhIcon name="magnifying-glass" size={13} />
        <span>Search…</span>
        <KbdShortcut k="K" />
      </button>

      {/* Drift + Notifications */}
      <DriftBadge report={driftReport} loading={driftLoading} onClick={runScan} />
      <NotificationBell count={activeCount} onClick={() => {}} />

      {/* Settings (opens Tweaks panel) */}
      <button
        onClick={() => window.dispatchEvent(new CustomEvent('studio:open-tweaks'))}
        aria-label="Settings"
        title="Settings"
        style={{
          width: 30, height: 30, borderRadius: 7,
          display: 'grid', placeItems: 'center',
          color: 'var(--ink-3)', background: 'transparent',
          border: 'none', cursor: 'pointer',
        }}
      >
        <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor"
             strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <circle cx="8" cy="8" r="2" />
          <path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3 3l1.5 1.5M11.5 11.5 13 13M3 13l1.5-1.5M11.5 4.5 13 3" />
        </svg>
      </button>

      {/* Avatar stack — collaborators on the active framework */}
      <div style={{ display: 'flex', alignItems: 'center', marginLeft: 4 }}>
        {[
          { i: 'RO', c: 'oklch(0.6 0.13 30)' },
          { i: 'LC', c: 'oklch(0.6 0.13 180)' },
          { i: 'MP', c: 'oklch(0.6 0.13 280)' },
        ].map((a, idx) => (
          <div
            key={a.i}
            title={a.i}
            style={{
              width: 26, height: 26, borderRadius: 999,
              background: a.c, color: '#fff',
              display: 'grid', placeItems: 'center',
              fontSize: 10, fontWeight: 600,
              border: '2px solid var(--bg)',
              marginLeft: idx === 0 ? 0 : -8,
              fontFamily: 'var(--font-display)',
            }}
          >
            {a.i}
          </div>
        ))}
      </div>

      {/* Project switcher */}
      <ProjectSwitcher />

      <div style={{ width: 1, height: 20, background: 'var(--line)' }} />

      {/* Ask Studio CTA */}
      <button
        onClick={() => window.dispatchEvent(new CustomEvent('studio:open-ai-assist'))}
        style={{
          height: 30, padding: '0 12px', borderRadius: 7,
          background: 'var(--ink)', color: 'var(--bg)',
          fontSize: 12.5, fontWeight: 500, cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 6, border: 'none',
        }}
      >
        <PhIcon name="sparkle" size={13} />
        Ask Studio
      </button>
    </header>
  );
}
