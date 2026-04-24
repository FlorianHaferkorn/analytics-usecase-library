'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
  id: string;
  label: string;
  icon: string;
  href: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: 'Home', href: '/overview' },
  { id: 'canvas', label: 'Canvas', icon: 'Graph', href: '/canvas' },
  { id: 'library', label: 'Library', icon: 'Library', href: '/library' },
  { id: 'detail', label: 'Detail', icon: 'Book', href: '/detail' },
];

interface SidebarProps {
  onNew?: () => void;
  onCommand?: () => void;
}

export function Sidebar({ onNew, onCommand }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === '[') {
        e.preventDefault();
        setCollapsed(true);
      }
      if ((e.metaKey || e.ctrlKey) && e.key === ']') {
        e.preventDefault();
        setCollapsed(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const isActive = (href: string) => {
    const segment = pathname?.split('/')[1];
    const hrefSegment = href.split('/')[1];
    return segment === hrefSegment;
  };

  return (
    <aside
      className="flex flex-col h-screen border-r border-border relative transition-all"
      style={{
        width: collapsed ? '68px' : '248px',
        transitionDuration: 'var(--motion-normal)',
        transitionTimingFunction: 'var(--ease-standard)',
      }}
    >
      {/* Brand */}
      <div className="h-14 flex items-center gap-2.5 px-4 border-b border-border-subtle">
        <div className="w-6.5 h-6.5 rounded-md bg-foreground text-background flex items-center justify-center font-display font-semibold text-sm">
          S
        </div>
        {!collapsed && (
          <div className="flex flex-col leading-tight">
            <div className="font-semibold text-xs font-display">Studio</div>
            <div className="text-2xs text-foreground-subtle">Analytics Framework</div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="px-3 py-3.5 flex flex-col gap-1.5">
        <button
          onClick={onNew}
          className="h-8.5 px-2.5 flex items-center justify-center gap-2.5 rounded-lg bg-foreground text-background font-medium text-xs hover:opacity-90 transition-opacity"
          title={collapsed ? 'New Element (N)' : undefined}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          >
            <line x1="7" y1="1" x2="7" y2="13" />
            <line x1="1" y1="7" x2="13" y2="7" />
          </svg>
          {!collapsed && (
            <>
              New element
              <span className="ml-auto opacity-60 text-2xs font-mono">N</span>
            </>
          )}
        </button>

        <button
          onClick={onCommand}
          className="h-8 px-2.5 flex items-center justify-center gap-2.5 rounded-lg bg-transparent text-foreground-subtle border border-border text-xs hover:bg-hover transition-colors"
          title={collapsed ? 'Search (⌘K)' : undefined}
        >
          <svg
            width="13"
            height="13"
            viewBox="0 0 13 13"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          >
            <circle cx="5" cy="5" r="4" />
            <line x1="8.5" y1="8.5" x2="12" y2="12" />
          </svg>
          {!collapsed && (
            <>
              Search…
              <span className="ml-auto text-2xs font-mono">⌘K</span>
            </>
          )}
        </button>
      </div>

      {/* Nav */}
      <nav className="px-2 py-3 flex flex-col gap-0.25">
        {!collapsed && <div className="text-2xs font-medium text-foreground-subtle px-2.5 py-1.5">Workspace</div>}
        {NAV_ITEMS.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.id}
              href={item.href}
              className={`h-8 px-2.5 flex items-center justify-center gap-2.5 rounded-lg text-xs font-medium transition-colors relative ${
                active
                  ? 'bg-hover text-foreground'
                  : 'text-foreground-muted hover:bg-hover'
              }`}
            >
              {/* Icon placeholder */}
              <div className="w-3.75 h-3.75 flex-shrink-0" />
              {!collapsed && item.label}
              {!collapsed && active && (
                <div
                  className="absolute left-0 top-2 bottom-2 w-0.5 bg-accent rounded-sm"
                  style={{ left: '-8px' }}
                />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute bottom-4 left-1/2 -translate-x-1/2 p-1 rounded text-foreground-subtle hover:bg-hover transition-colors"
        title={collapsed ? 'Expand' : 'Collapse'}
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          {collapsed ? (
            <polyline points="10 4 14 8 10 12" />
          ) : (
            <polyline points="6 4 2 8 6 12" />
          )}
        </svg>
      </button>
    </aside>
  );
}
