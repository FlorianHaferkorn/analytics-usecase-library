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
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--sp-1)',
              paddingLeft: isActive ? `calc(var(--sp-1) - 3px)` : 'var(--sp-1)',
              paddingRight: 'var(--sp-1)',
              paddingTop: 'var(--sp-1)',
              paddingBottom: 'var(--sp-1)',
              borderRadius: 'var(--radius-md)',
              borderLeft: isActive ? `3px solid ${item.color}` : '3px solid transparent',
              textDecoration: 'none',
              fontSize: '0.875rem',
              fontWeight: isActive ? 600 : 400,
              color: isActive ? 'var(--slate-50)' : 'var(--slate-400)',
              backgroundColor: isActive ? 'var(--slate-800)' : 'transparent',
              transition: 'all var(--duration-fast) var(--ease-out)',
            }}
          >
            <PhIcon name={item.sidebarIcon as PhIconName} size={18} />
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
    <aside
      style={{
        gridRow: '1 / -1',
        backgroundColor: 'var(--slate-950)',
        borderRight: '1px solid var(--slate-800)',
        display: 'flex',
        flexDirection: 'column',
        padding: 'var(--sp-2) 0',
      }}
    >
      <div style={{ padding: 'var(--sp-1) var(--sp-2)', marginBottom: 'var(--sp-2)' }}>
        <Link href="/" style={{ textDecoration: 'none' }}>
          <span
            style={{
              fontSize: '1.125rem',
              fontWeight: 700,
              color: 'var(--slate-50)',
              letterSpacing: '-0.025em',
            }}
          >
            Action<span style={{ color: 'var(--mint)' }}>Ready</span>
          </span>
        </Link>
        <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', marginTop: '2px' }}>
          Studio v0.1.0
        </p>
      </div>

      {/* Mode switcher */}
      <div style={{ display: 'flex', gap: '4px', padding: '0 var(--sp-1)', marginBottom: 'var(--sp-2)' }}>
        {(['forge', 'registry'] as const).map((m) => (
          <Link
            key={m}
            href={m === 'forge' ? '/discover' : '/catalog'}
            style={{
              flex: 1,
              textAlign: 'center',
              padding: '4px 0',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.6875rem',
              fontWeight: mode === m ? 700 : 400,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              textDecoration: 'none',
              color: mode === m ? 'var(--slate-50)' : 'var(--slate-500)',
              backgroundColor: mode === m
                ? (m === 'forge' ? 'color-mix(in srgb, var(--mint) 20%, transparent)' : 'color-mix(in srgb, var(--info) 20%, transparent)')
                : 'transparent',
              border: `1px solid ${mode === m ? (m === 'forge' ? 'var(--mint)' : 'var(--info)') : 'transparent'}`,
            }}
          >
            {m === 'forge' ? 'Forge' : 'Registry'}
          </Link>
        ))}
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px', padding: '0 var(--sp-1)' }}>
        <NavGroup items={mode === 'forge' ? FORGE_NAV : REGISTRY_NAV} pathname={pathname} />
      </nav>

      <div style={{ flex: 1 }} />

      <div
        style={{
          padding: 'var(--sp-2)',
          borderTop: '1px solid var(--slate-800)',
          fontSize: '0.75rem',
          color: 'var(--slate-600)',
        }}
      >
        Aurora Group SE
      </div>
    </aside>
  );
}
