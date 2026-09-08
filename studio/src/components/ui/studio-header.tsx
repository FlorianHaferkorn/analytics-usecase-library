'use client';

import { useCallback } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { NAV_ITEMS, getNavGroup } from '@/lib/navigation';
import { useProjectStore } from '@/lib/store/project-store';
import { DriftBadge } from '@/components/registry/drift-badge';
import { ProjectSwitcher } from '@/components/AppShell/ProjectSwitcher';
import { PhIcon } from './ph-icon';
import { KbdShortcut } from './kbd-shortcut';
import styles from './studio-header.module.css';

/** Build breadcrumb segments from the current pathname. */
function useBreadcrumbs(pathname: string): string[] {
  const match = NAV_ITEMS.find((item) => pathname.startsWith(item.href));
  if (!match) return ['Studio'];
  const group = getNavGroup(pathname);
  return [group?.label ?? 'Studio', match.label];
}

export function StudioHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const scope = useProjectStore(s => s.dataScope);
  const crumbs = useBreadcrumbs(pathname);
  const driftReport = useProjectStore((s) => s.driftReport);
  const driftLoading = useProjectStore((s) => s.driftLoading);
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
    <header className={styles.header}>
      {/* Breadcrumb */}
      <div className={styles.breadcrumbs}>
        {crumbs.map((crumb, i) => (
          <span key={i} className={styles.crumb}>
            {i > 0 && (
              <PhIcon name="caret-right" size={12} style={{ color: 'var(--ink-4)', flexShrink: 0 }} />
            )}
            <span className={`${styles.crumbText}${i === crumbs.length - 1 ? ` ${styles.crumbCurrent}` : ''}`}>
              {crumb}
            </span>
          </span>
        ))}
      </div>

      <div className={styles.spacer} />

      {/* Search */}
      <button
        onClick={() => window.dispatchEvent(new CustomEvent('studio:open-command-palette'))}
        type="button"
        aria-label="Search Studio"
        className={styles.searchButton}
      >
        <PhIcon name="magnifying-glass" size={13} />
        <span>Search…</span>
        <span><KbdShortcut k="K" /></span>
      </button>

      {/* Drift assurance */}
      {scope === 'library' && <DriftBadge report={driftReport} loading={driftLoading} onClick={runScan} />}

      {/* Settings (opens Tweaks panel) */}
      <button
        onClick={() => window.dispatchEvent(new CustomEvent('studio:open-tweaks'))}
        aria-label="Settings"
        title="Settings"
        className={styles.iconButton}
      >
        <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor"
             strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <circle cx="8" cy="8" r="2" />
          <path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3 3l1.5 1.5M11.5 11.5 13 13M3 13l1.5-1.5M11.5 4.5 13 3" />
        </svg>
      </button>

      {/* Project switcher */}
      <ProjectSwitcher />

      <div className={styles.divider} />

      {/* Ask Studio CTA — per Studio.html: accent bg + accent-ink */}
      <button
        onClick={() => router.push('/discover')}
        type="button"
        aria-label="Ask Studio"
        className={styles.askButton}
      >
        <PhIcon name="sparkle" size={13} />
        <span>Ask Studio</span>
      </button>
    </header>
  );
}
