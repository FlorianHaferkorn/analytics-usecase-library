import Link from 'next/link';

const NAV_ITEMS = [
  {
    href: '/discovery',
    title: 'Discovery Hub',
    description: 'Extract strategy anchors from business reports and research',
    icon: '🔍',
  },
  {
    href: '/steering',
    title: 'Steering Hub',
    description: 'Visualize and edit the Golden Thread: Strategy → KPI → Action',
    icon: '🌳',
  },
  {
    href: '/registry',
    title: 'Registry',
    description: 'Manage the SSOT KPI catalog and action code library',
    icon: '📋',
  },
  {
    href: '/brand-lab',
    title: 'Brand & UX Lab',
    description: 'Define themes, layouts, and preview 3-30-300 report pages',
    icon: '🎨',
  },
  {
    href: '/delivery',
    title: 'Delivery',
    description: 'Export to Fabric/Power BI, SQL, or Evidence.dev',
    icon: '🚀',
  },
] as const;

export default function HomePage() {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--sp-4)',
        gap: 'var(--sp-6)',
      }}
    >
      <header style={{ textAlign: 'center' }}>
        <h1
          style={{
            fontSize: '2.5rem',
            fontWeight: 700,
            letterSpacing: '-0.025em',
            color: 'var(--slate-50)',
          }}
        >
          Action
          <span style={{ color: 'var(--mint)' }}>Ready</span>{' '}
          <span style={{ color: 'var(--gold)' }}>Studio</span>
        </h1>
        <p
          style={{
            marginTop: 'var(--sp-1)',
            color: 'var(--slate-400)',
            fontSize: '1.125rem',
          }}
        >
          NotebookLM for Business Steering
        </p>
      </header>

      <nav
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 'var(--sp-2)',
          maxWidth: '960px',
          width: '100%',
        }}
      >
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            style={{
              display: 'block',
              padding: 'var(--sp-3)',
              backgroundColor: 'var(--slate-800)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--slate-700)',
              textDecoration: 'none',
              transition: 'border-color var(--duration-fast) var(--ease-out)',
            }}
          >
            <div style={{ fontSize: '1.5rem', marginBottom: 'var(--sp-1)' }}>
              {item.icon}
            </div>
            <h2
              style={{
                fontSize: '1.125rem',
                fontWeight: 600,
                color: 'var(--slate-50)',
                marginBottom: 'var(--sp-0-5)',
              }}
            >
              {item.title}
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--slate-400)', lineHeight: 1.5 }}>
              {item.description}
            </p>
          </Link>
        ))}
      </nav>

      <footer style={{ color: 'var(--slate-600)', fontSize: '0.75rem' }}>
        ActionReady Analytics Platform v0.1.0 — Aurora Group Showcase
      </footer>
    </div>
  );
}
