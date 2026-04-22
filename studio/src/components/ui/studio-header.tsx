'use client';

import { useCallback } from 'react';
import { usePathname } from 'next/navigation';
import { getPageTitle } from '@/lib/navigation';
import { useProjectStore } from '@/lib/store/project-store';
import { DriftBadge } from '@/components/registry/drift-badge';
import { NotificationBell } from '@/components/notifications/notification-bell';
import { ProjectSelector } from './project-selector';

/** Build breadcrumb segments from a path like /steering/discover */
function breadcrumbs(pathname: string, title: string): string[] {
  const segment = pathname.split('/').filter(Boolean)[0];
  const section = segment
    ? segment.charAt(0).toUpperCase() + segment.slice(1)
    : 'Studio';
  if (section.toLowerCase() === title.toLowerCase()) return ['Framework', title];
  return ['Framework', section, title];
}

export function StudioHeader() {
  const pathname = usePathname();
  const title = getPageTitle(pathname);
  const crumbs = breadcrumbs(pathname, title);

  const driftReport  = useProjectStore((s) => s.driftReport);
  const driftLoading = useProjectStore((s) => s.driftLoading);
  const notifications = useProjectStore((s) => s.notifications);
  const activeCount  = notifications.filter((n) => !n.dismissed).length;
  const setDriftReport  = useProjectStore((s) => s.setDriftReport);
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
    <header style={{
      height: 'var(--h-row)',
      borderBottom: '1px solid var(--line)',
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '0 var(--pad)',
      background: 'var(--panel)',
    }}>
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: '0.8125rem', flex: 1, minWidth: 0 }}>
        {crumbs.map((c, i) => (
          <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            {i > 0 && <span style={{ color: 'var(--ink-4)', fontSize: '0.625rem' }}>›</span>}
            <span style={{ color: i === crumbs.length - 1 ? 'var(--ink)' : 'var(--ink-4)', fontWeight: i === crumbs.length - 1 ? 500 : 400 }}>
              {c}
            </span>
          </span>
        ))}
      </div>

      {/* Search trigger */}
      <button
        style={{
          height: 30, padding: '0 10px', display: 'flex', alignItems: 'center', gap: 8,
          borderRadius: 7, border: '1px solid var(--line)',
          color: 'var(--ink-3)', fontSize: '0.8125rem', background: 'var(--bg-2)',
        }}
        onClick={() => {
          window.dispatchEvent(new CustomEvent('studio:open-command-palette'));
        }}
      >
        <span>Search…</span>
        <kbd style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          minWidth: 18, height: 18, padding: '0 5px',
          fontFamily: 'var(--font-mono)', fontSize: '0.625rem', fontWeight: 500,
          color: 'var(--ink-4)', background: 'var(--panel)',
          border: '1px solid var(--line)', borderRadius: 5,
        }}>
          ⌘K
        </kbd>
      </button>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <NotificationBell count={activeCount} onClick={() => {}} />
        <DriftBadge report={driftReport} loading={driftLoading} onClick={runScan} />
      </div>

      <div style={{ width: 1, height: 20, background: 'var(--line)' }} />

      <ProjectSelector />

      {/* CTA */}
      <button style={{
        height: 30, padding: '0 12px', borderRadius: 7,
        background: 'var(--accent)', color: 'var(--accent-ink)',
        fontSize: '0.8125rem', fontWeight: 500,
        display: 'inline-flex', alignItems: 'center', gap: 6,
        border: 'none', cursor: 'pointer',
      }}>
        ✦ Ask Studio
      </button>
    </header>
  );
}
