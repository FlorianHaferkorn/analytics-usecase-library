'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FORGE_NAV, REGISTRY_NAV, getNavMode, type NavItem } from '@/lib/navigation';
import { PhIcon, type PhIconName } from './ph-icon';
import { type DomainStat } from '@/app/(studio)/layout';

const navLabelStyle = {
  padding: '8px 10px 4px',
  fontSize: '0.5625rem', fontWeight: 500,
  color: 'var(--ink-4)', textTransform: 'uppercase' as const,
  letterSpacing: '0.08em',
};

interface SidebarProps {
  domains?: DomainStat[];
}

export function StudioSidebar({ domains = [] }: SidebarProps) {
  const pathname = usePathname();
  const mode = getNavMode(pathname);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('sidebar-collapsed');
    if (stored === 'true') setCollapsed(true);
  }, []);

  const toggle = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem('sidebar-collapsed', String(next));
  };

  const w = collapsed ? 68 : 248;
  const navItems = mode === 'forge' ? FORGE_NAV : REGISTRY_NAV;

  return (
    <aside style={{
      width: w, flexShrink: 0, height: '100%',
      background: 'var(--panel)',
      borderRight: '1px solid var(--line)',
      display: 'flex', flexDirection: 'column',
      transition: 'width 240ms cubic-bezier(.2,.8,.2,1)',
      overflow: 'hidden',
    }}>
      {/* Brand */}
      <div style={{
        height: 56, padding: '0 16px', flexShrink: 0,
        display: 'flex', alignItems: 'center', gap: 10,
        borderBottom: '1px solid var(--line-2)',
      }}>
        <div style={{
          width: 26, height: 26, borderRadius: 7, flexShrink: 0,
          background: 'var(--ink)', color: 'var(--panel)',
          display: 'grid', placeItems: 'center',
          fontWeight: 600, fontSize: 14, letterSpacing: '-0.04em',
          fontFamily: 'var(--font-display)',
        }}>
          A
        </div>
        {!collapsed && (
          <div style={{ lineHeight: 1.2, minWidth: 0 }}>
            <div style={{ fontWeight: 600, fontSize: '0.875rem', letterSpacing: '-0.01em', color: 'var(--ink)', whiteSpace: 'nowrap' }}>
              Action<span style={{ color: 'var(--accent)' }}>Ready</span>
            </div>
            <div style={{ fontSize: '0.625rem', color: 'var(--ink-4)', whiteSpace: 'nowrap' }}>Studio v0.1.0</div>
          </div>
        )}
      </div>

      {/* New + Search */}
      <div style={{ padding: '14px 8px 6px', display: 'flex', flexDirection: 'column', gap: 6, flexShrink: 0 }}>
        <button
          onClick={() => window.dispatchEvent(new CustomEvent('studio:open-wizard'))}
          style={{
            height: 34, padding: collapsed ? 0 : '0 10px',
            display: 'flex', alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: 10, borderRadius: 8,
            background: 'var(--ink)', color: 'var(--panel)',
            fontWeight: 500, fontSize: '0.8125rem',
            border: 'none', cursor: 'pointer', flexShrink: 0,
          }}
        >
          <PhIcon name="plus" size={14} />
          {!collapsed && <><span>New element</span><span style={{ marginLeft: 'auto', opacity: 0.5, fontSize: '0.625rem', fontFamily: 'var(--font-mono)' }}>N</span></>}
        </button>
        <button
          onClick={() => window.dispatchEvent(new CustomEvent('studio:open-command-palette'))}
          style={{
            height: 32, padding: collapsed ? 0 : '0 10px',
            display: 'flex', alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: 10, borderRadius: 8,
            background: 'transparent', color: 'var(--ink-3)',
            border: '1px solid var(--line)', fontSize: '0.8125rem',
            cursor: 'pointer', flexShrink: 0,
          }}
        >
          <PhIcon name="magnifying-glass" size={13} />
          {!collapsed && <><span style={{ flex: 1, textAlign: 'left' }}>Search…</span><span style={{ fontSize: '0.625rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-4)' }}>⌘K</span></>}
        </button>
      </div>

      {/* Mode switcher — only when expanded */}
      {!collapsed && (
        <div style={{ padding: '4px 8px' }}>
          <div style={{ display: 'flex', gap: 4 }}>
            {(['forge', 'registry'] as const).map((m) => (
              <Link
                key={m}
                href={m === 'forge' ? '/dashboard' : '/catalog'}
                style={{
                  flex: 1, textAlign: 'center', padding: '5px 0',
                  borderRadius: 6, fontSize: '0.625rem', fontWeight: mode === m ? 600 : 400,
                  textTransform: 'uppercase', letterSpacing: '0.06em',
                  textDecoration: 'none',
                  color: mode === m ? 'var(--ink)' : 'var(--ink-4)',
                  background: mode === m ? 'var(--bg-2)' : 'transparent',
                  border: `1px solid ${mode === m ? 'var(--line)' : 'transparent'}`,
                }}
              >
                {m === 'forge' ? 'Forge' : 'Registry'}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Nav */}
      {!collapsed && (
        <div style={navLabelStyle}>Workspace</div>
      )}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 1, padding: '0 8px', flexShrink: 0 }}>
        {navItems.map((item: NavItem) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              style={{
                display: 'flex', alignItems: 'center',
                justifyContent: collapsed ? 'center' : 'flex-start',
                gap: 10,
                height: 34, padding: collapsed ? 0 : '0 10px',
                paddingLeft: !collapsed && isActive ? 7 : !collapsed ? 10 : 0,
                borderRadius: 7,
                borderLeft: !collapsed && isActive ? '3px solid var(--accent)' : '3px solid transparent',
                textDecoration: 'none',
                fontSize: '0.8125rem',
                fontWeight: isActive ? 500 : 400,
                color: isActive ? 'var(--ink)' : 'var(--ink-3)',
                background: isActive ? 'var(--hover)' : 'transparent',
                transition: 'all var(--duration-fast)',
              }}
              onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'var(--hover)'; }}
              onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
            >
              <PhIcon name={item.sidebarIcon as PhIconName} size={16} />
              {!collapsed && item.label}
            </Link>
          );
        })}
      </nav>

      {/* Domains section — only when expanded and data available */}
      {!collapsed && domains.length > 0 && (
        <div style={{ padding: '12px 8px 4px' }}>
          <div style={navLabelStyle}>Domains</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {domains.map((d) => (
              <div key={d.name} style={{
                height: 28, padding: '0 10px',
                display: 'flex', alignItems: 'center', gap: 10,
                borderRadius: 7,
                color: 'var(--ink-3)', fontSize: '0.8125rem',
              }}>
                <span style={{
                  width: 6, height: 6, borderRadius: 2, flexShrink: 0,
                  background: `oklch(0.65 0.12 ${d.hue})`,
                }} />
                <span style={{ flex: 1, textTransform: 'capitalize', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {d.name}
                </span>
                <span style={{ fontSize: '0.625rem', color: 'var(--ink-4)', fontFamily: 'var(--font-mono)' }}>
                  {d.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ flex: 1 }} />

      {/* Footer */}
      <div style={{
        padding: '10px 12px', borderTop: '1px solid var(--line-2)', flexShrink: 0,
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <div style={{
          width: 28, height: 28, borderRadius: 999, flexShrink: 0,
          background: 'linear-gradient(135deg, var(--accent), oklch(0.5 0.12 320))',
          color: '#fff', display: 'grid', placeItems: 'center',
          fontSize: '0.5625rem', fontWeight: 700,
        }}>
          AU
        </div>
        {!collapsed && (
          <>
            <div style={{ lineHeight: 1.2, flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                Aurora Group SE
              </div>
              <div style={{ fontSize: '0.625rem', color: 'var(--ink-4)' }}>Analytics Platform</div>
            </div>
            <button
              onClick={toggle}
              style={{
                width: 24, height: 24, borderRadius: 6, flexShrink: 0,
                display: 'grid', placeItems: 'center',
                color: 'var(--ink-4)', background: 'transparent', border: 'none', cursor: 'pointer',
              }}
              title="Collapse sidebar"
            >
              <PhIcon name="caret-left" size={13} />
            </button>
          </>
        )}
        {collapsed && (
          <button
            onClick={toggle}
            style={{
              width: 28, height: 28, borderRadius: 6,
              display: 'grid', placeItems: 'center',
              color: 'var(--ink-4)', background: 'transparent', border: 'none', cursor: 'pointer',
              margin: '0 auto',
            }}
            title="Expand sidebar"
          >
            <PhIcon name="caret-right" size={13} />
          </button>
        )}
      </div>
    </aside>
  );
}
