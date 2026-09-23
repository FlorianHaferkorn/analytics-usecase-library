'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { STUDIO_NAV_GROUPS } from '@/lib/navigation';
import { useDomainFilter } from '@/lib/hooks/use-domain-filter';
import { PhIcon, type PhIconName } from './ph-icon';
import { KbdShortcut } from './kbd-shortcut';
import { useProjectStore } from '@/lib/store/project-store';
import styles from './studio-sidebar.module.css';

export interface DomainStat {
  name: string;
  count: number;
  hue: number;
}

interface SidebarProps {
  domains?: DomainStat[];
}

export function StudioSidebar({ domains = [] }: SidebarProps) {
  const pathname = usePathname();
  const dataScope = useProjectStore(state => state.dataScope);
  const projectName = useProjectStore(state => state.projectName);
  const { domainFilter, toggleDomainFilter, isPending } = useDomainFilter();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 960px)');
    const apply = () => {
      const stored = localStorage.getItem('sidebar-collapsed');
      setCollapsed(stored === 'true' || mq.matches);
    };
    const frame = window.requestAnimationFrame(apply);
    mq.addEventListener('change', apply);
    return () => {
      window.cancelAnimationFrame(frame);
      mq.removeEventListener('change', apply);
    };
  }, []);

  const toggle = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem('sidebar-collapsed', String(next));
  };

  const isCollapsed = collapsed;

  return (
    <aside className={`studio-sidebar ${styles.sidebar}`} data-collapsed={isCollapsed}>
      {/* Brand */}
      <div className={styles.brand}>
        <div className={styles.brandMark}>
          A
        </div>
        {!collapsed && (
          <div className={styles.brandCopy}>
            <div className={styles.brandName}>ALUCA</div>
            <div className={styles.brandMeta}>Studio</div>
          </div>
        )}
      </div>

      <div className={styles.scroller}>

      <div className={styles.quickActions}>
        {dataScope === 'project' ? <Link href="/discover" className={styles.newButton} aria-label="Add project evidence">
          <PhIcon name="plus" size={14} />
          {!collapsed && <span>Add evidence</span>}
        </Link> : <button
          onClick={() => window.dispatchEvent(new CustomEvent('studio:open-wizard'))}
          type="button"
          aria-label="New library definition"
          className={styles.newButton}
        >
          <PhIcon name="plus" size={14} />
          {!collapsed && <><span>New definition</span><span style={{ marginLeft: 'auto' }}><KbdShortcut k="N" meta={false} style={{ background: 'transparent', borderColor: 'transparent', color: 'currentColor', opacity: 0.6 }} /></span></>}
        </button>}
      </div>

      {/* One workflow-oriented navigation. Routes keep their technical ownership. */}
      <nav className={styles.nav} aria-label="Studio workflow">
        {STUDIO_NAV_GROUPS.filter(group => dataScope === 'project' ? group.label !== 'Administration' : ['Reference & standards', 'Administration'].includes(group.label)).map((group) => (
          <div className={styles.navGroup} key={group.label}>
            {!collapsed && (
              <div className={styles.navLabel} title={group.description}>
                {group.label}
              </div>
            )}
            {group.items.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-label={item.label}
                  aria-current={isActive ? 'page' : undefined}
                  title={collapsed ? item.label : item.description}
                  className={styles.navLink}
                  data-active={isActive}
                >
                  {item.step ? <span className={styles.phaseNumber} aria-hidden="true">{item.step}</span> : <PhIcon name={item.sidebarIcon as PhIconName} size={16} />}
                  {!collapsed && <span className={styles.navLinkLabel}>{item.label}</span>}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Domains section — clickable filter (?domain=<name>) when expanded */}
      {!collapsed && domains.length > 0 && (
        <div className={styles.domainSection}>
          <div className={styles.navLabel}>Domain filter</div>
          <p className={styles.domainHint}>
            Narrows Forge views instantly — no page reload.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {domains.map((d) => {
              const isActive = domainFilter === d.name;
              return (
                <button
                  key={d.name}
                  type="button"
                  disabled={isPending}
                  onClick={() => toggleDomainFilter(d.name)}
                  style={{
                    height: 28, padding: '0 10px',
                    display: 'flex', alignItems: 'center', gap: 10,
                    borderRadius: 7,
                    color: isActive ? 'var(--ink)' : 'var(--ink-2)',
                    fontSize: 12.5,
                    background: isActive ? 'var(--hover)' : 'transparent',
                    border: 'none', cursor: isPending ? 'wait' : 'pointer', textAlign: 'left',
                    opacity: isPending && !isActive ? 0.7 : 1,
                    transition: 'background var(--duration-fast)',
                  }}
                  onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'var(--hover)'; }}
                  onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
                >
                  <span style={{
                    width: 6, height: 6, borderRadius: 2, flexShrink: 0,
                    background: `oklch(0.7 0.1 ${d.hue})`,
                  }} />
                  <span style={{ flex: 1, textTransform: 'capitalize', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {d.name}
                  </span>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-4)', fontFamily: 'var(--font-mono)' }}>
                    {d.count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div style={{ flex: 1 }} />
      </div>

      <div className={styles.footer}>
        <div className={styles.footerIcon} aria-hidden="true">
          <PhIcon name="clipboard-text" size={14} />
        </div>
        {!collapsed && (
          <>
            <div className={styles.footerCopy}>
              <div className={styles.footerTitle}>{dataScope === 'project' ? projectName : 'Reference library'}</div>
              <div className={styles.footerMeta}>{dataScope === 'project' ? 'Pinned project context' : 'Reusable content only'}</div>
            </div>
            <button
              onClick={toggle}
              className={styles.collapseButton}
              title="Collapse sidebar"
            >
              <PhIcon name="caret-left" size={13} />
            </button>
          </>
        )}
        {collapsed && (
          <button
            onClick={toggle}
            className={styles.collapseButton}
            title="Expand sidebar"
          >
            <PhIcon name="caret-right" size={13} />
          </button>
        )}
      </div>
    </aside>
  );
}
