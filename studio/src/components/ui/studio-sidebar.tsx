'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { NAV_ITEMS } from '@/lib/navigation';
import { PhIcon, type PhIconName } from './ph-icon';

export function StudioSidebar() {
  const pathname = usePathname();

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
      <div style={{ padding: 'var(--sp-1) var(--sp-2)', marginBottom: 'var(--sp-3)' }}>
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

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px', padding: '0 var(--sp-1)' }}>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--sp-1)',
                /* T1.4: active left-border accent + compensate padding so text stays aligned */
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
