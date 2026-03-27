'use client';

import { usePathname } from 'next/navigation';

const PAGE_TITLES: Record<string, string> = {
  '/discovery': 'Discovery Hub',
  '/steering': 'Steering Hub',
  '/registry': 'Registry',
  '/brand-lab': 'Brand & UX Lab',
  '/delivery': 'Delivery',
};

export function StudioHeader() {
  const pathname = usePathname();
  const title = Object.entries(PAGE_TITLES).find(([path]) =>
    pathname.startsWith(path)
  )?.[1] ?? 'Studio';

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
      <h1
        style={{
          fontSize: '1rem',
          fontWeight: 600,
          color: 'var(--slate-100)',
        }}
      >
        {title}
      </h1>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--sp-1)',
        }}
      >
        <span
          style={{
            display: 'inline-block',
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: 'var(--mint)',
          }}
        />
        <span style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>
          Stage 1 Ready
        </span>
      </div>
    </header>
  );
}
