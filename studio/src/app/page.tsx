import Link from 'next/link';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { NAV_ITEMS } from '@/lib/navigation';

export default async function HomePage() {
  const [kpis, actions, brackets] = await Promise.all([
    loadKpiCatalog(),
    loadAllActionCodes(),
    loadAllBrackets(),
  ]);

  const stats = [
    { label: 'KPIs', value: kpis.length, color: 'var(--mint)' },
    { label: 'Action Codes', value: actions.length, color: 'var(--gold)' },
    { label: 'Use Cases', value: brackets.length, color: 'var(--info)' },
    {
      label: 'Domains',
      value: [...new Set(brackets.map((b) => b.domain))].length,
      color: 'var(--slate-300)',
    },
  ];

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--sp-4)',
        gap: 'var(--sp-4)',
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

      {/* Pulse Stats */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 'var(--sp-2)',
          maxWidth: '640px',
          width: '100%',
        }}
      >
        {stats.map((stat) => (
          <div
            key={stat.label}
            style={{
              padding: 'var(--sp-2)',
              backgroundColor: 'var(--slate-800)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--slate-700)',
              textAlign: 'center',
            }}
          >
            <p style={{ fontSize: '1.75rem', fontWeight: 700, color: stat.color }}>
              {stat.value}
            </p>
            <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', marginTop: '2px' }}>
              {stat.label}
            </p>
          </div>
        ))}
      </div>

      {/* Navigation Grid */}
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
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--slate-900)',
                border: `1px solid ${item.color}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.875rem',
                fontWeight: 700,
                color: item.color,
                marginBottom: 'var(--sp-1-5)',
              }}
            >
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
              {item.label}
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--slate-400)', lineHeight: 1.5 }}>
              {item.description}
            </p>
          </Link>
        ))}
      </nav>

      <footer style={{ color: 'var(--slate-600)', fontSize: '0.75rem' }}>
        ActionReady Analytics Platform v0.1.0 — Aurora Group SE Showcase
      </footer>
    </div>
  );
}
