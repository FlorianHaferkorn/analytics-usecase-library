'use client';

import { useCallback } from 'react';
import { usePathname } from 'next/navigation';
import { getPageTitle } from '@/lib/navigation';
import { useProjectStore } from '@/lib/store/project-store';
import { DriftBadge } from '@/components/registry/drift-badge';
import { NotificationBell } from '@/components/notifications/notification-bell';
import { ProjectSwitcher } from '@/components/AppShell/ProjectSwitcher';

export function StudioHeader() {
  const pathname = usePathname();
  const title = getPageTitle(pathname);
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
        height: '56px',
        borderBottom: '1px solid var(--slate-800)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--sp-3)',
        backgroundColor: 'var(--slate-900)',
      }}
    >
      <h1 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--slate-100)' }}>
        {title}
      </h1>

      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
        <NotificationBell count={activeCount} onClick={() => { /* scroll to rules panel in registry */ }} />
        <DriftBadge report={driftReport} loading={driftLoading} onClick={runScan} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)' }}>
          <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--mint)' }} />
          <span style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>Stage 1 Ready</span>
        </div>
        <ProjectSwitcher />
      </div>
    </header>
  );
}
