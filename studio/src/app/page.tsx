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
    { label: 'KPIs', value: kpis.length, color: 'var(--accent)' },
    { label: 'Action Codes', value: actions.length, color: 'var(--warning)' },
    { label: 'Use Cases', value: brackets.length, color: 'var(--info)' },
    {
      label: 'Domains',
      value: [...new Set(brackets.map((b) => b.domain))].length,
      color: 'var(--ink-2)',
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
        padding: '32px',
        gap: '32px',
      }}
    >
      <header style={{ textAlign: 'center' }}>
        <h1
          style={{
            fontSize: '2.5rem',
            fontWeight: 700,
            letterSpacing: '-0.025em',
            color: 'var(--ink)',
          }}
        >
          Action
          <span style={{ color: 'var(--accent)' }}>Ready</span>{' '}
          <span style={{ color: 'var(--warning)' }}>Studio</span>
        </h1>
        <p
          style={{
            marginTop: '8px',
            color: 'var(--ink-3)',
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
          gap: '16px',
          maxWidth: '640px',
          width: '100%',
        }}
      >
        {stats.map((stat) => (
          <div
            key={stat.label}
            style={{
              padding: '16px',
              backgroundColor: 'var(--panel)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--line)',
              textAlign: 'center',
            }}
          >
            <p style={{ fontSize: '1.75rem', fontWeight: 700, color: stat.color }}>
              {stat.value}
            </p>
            <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', marginTop: '2px' }}>
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
          gap: '16px',
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
              padding: 'var(--pad)',
              backgroundColor: 'var(--panel)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--line)',
              textDecoration: 'none',
              transition: 'border-color var(--duration-fast) var(--ease-out)',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--bg)',
                border: `1px solid ${item.color}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.875rem',
                fontWeight: 700,
                color: item.color,
                marginBottom: '12px',
              }}
            >
              {item.icon}
            </div>
            <h2
              style={{
                fontSize: '1.125rem',
                fontWeight: 600,
                color: 'var(--ink)',
                marginBottom: '4px',
              }}
            >
              {item.label}
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--ink-3)', lineHeight: 1.5 }}>
              {item.description}
            </p>
          </Link>
        ))}
      </nav>

      <footer style={{ color: 'var(--ink-4)', fontSize: '0.75rem' }}>
        ActionReady Analytics Platform v0.1.0 — Aurora Group SE Showcase
      </footer>
    </div>
  );
}
