'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FORGE_NAV, REGISTRY_NAV, getNavMode, type NavItem } from '@/lib/navigation';
import { PhIcon, type PhIconName } from './ph-icon';

function NavGroup({ items, pathname }: { items: readonly NavItem[]; pathname: string }) {
  return (
    <>
      {items.map((item) => {
        const isActive = pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              height: 34, padding: '0 10px',
              paddingLeft: isActive ? 7 : 10,
              borderRadius: 7,
              borderLeft: `3px solid ${isActive ? 'var(--accent)' : 'transparent'}`,
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
            {item.label}
          </Link>
        );
      })}
    </>
  );
}

export function StudioSidebar() {
  const pathname = usePathname();
  const mode = getNavMode(pathname);

  return (
    <aside style={{
      gridRow: '1 / -1', width: 248,
      background: 'var(--panel)',
      borderRight: '1px solid var(--line)',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Brand */}
      <div style={{ height: 56, padding: '0 16px', display: 'flex', alignItems: 'center', gap: 10, borderBottom: '1px solid var(--line-2)' }}>
        <div style={{
          width: 26, height: 26, borderRadius: 7,
          background: 'var(--ink)', color: 'var(--panel)',
          display: 'grid', placeItems: 'center',
          fontWeight: 600, fontSize: 14, letterSpacing: '-0.04em',
          fontFamily: 'var(--font-display)',
        }}>
          A
        </div>
        <div style={{ lineHeight: 1.2 }}>
          <div style={{ fontWeight: 600, fontSize: '0.875rem', letterSpacing: '-0.01em', color: 'var(--ink)' }}>
            Action<span style={{ color: 'var(--accent)' }}>Ready</span>
          </div>
          <div style={{ fontSize: '0.625rem', color: 'var(--ink-4)' }}>Studio v0.1.0</div>
        </div>
      </div>

      {/* Mode switcher */}
      <div style={{ padding: '12px 8px 8px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ display: 'flex', gap: 4 }}>
          {(['forge', 'registry'] as const).map((m) => (
            <Link
              key={m}
              href={m === 'forge' ? '/steering' : '/registry'}
              style={{
                flex: 1, textAlign: 'center', padding: '5px 0',
                borderRadius: 6, fontSize: '0.625rem', fontWeight: mode === m ? 600 : 400,
                textTransform: 'uppercase', letterSpacing: '0.06em',
                textDecoration: 'none',
                color: mode === m ? 'var(--ink)' : 'var(--ink-4)',
                background: mode === m ? 'var(--bg-2)' : 'transparent',
                border: `1px solid ${mode === m ? 'var(--line)' : 'transparent'}`,
                transition: 'all var(--duration-fast)',
              }}
            >
              {m === 'forge' ? 'Forge' : 'Registry'}
            </Link>
          ))}
        </div>
      </div>

      {/* Nav header */}
      <div style={{ padding: '4px 8px 2px' }}>
        <div style={{ padding: '6px 10px', fontSize: '0.5625rem', fontWeight: 500, color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Workspace
        </div>
      </div>

      {/* Nav */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 1, padding: '0 8px' }}>
        <NavGroup items={mode === 'forge' ? FORGE_NAV : REGISTRY_NAV} pathname={pathname} />
      </nav>

      <div style={{ flex: 1 }} />

      {/* Footer */}
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--line-2)', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 28, height: 28, borderRadius: 999,
          background: 'var(--accent)', color: 'var(--accent-ink)',
          display: 'grid', placeItems: 'center',
          fontSize: '0.5625rem', fontWeight: 700, flexShrink: 0,
        }}>
          AU
        </div>
        <div style={{ lineHeight: 1.2, flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            Aurora Group SE
          </div>
          <div style={{ fontSize: '0.625rem', color: 'var(--ink-4)' }}>Analytics Platform</div>
        </div>
      </div>
    </aside>
  );
}
