'use client';

import { useState, useMemo, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import type { CatalogKpi } from '@/lib/core/catalog-loader';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import type { ActionCodeDefinitionV20AIMirror } from '@/lib/schemas';
import { PhIcon } from '@/components/ui/ph-icon';

// ─── Types ────────────────────────────────────────────────────────────────────

type TabId = 'kpis' | 'brackets' | 'actions';

interface Props {
  kpis: CatalogKpi[];
  brackets: UseCaseBracketV20Lean[];
  actions: ActionCodeDefinitionV20AIMirror[];
  highlightKpiId: string | null;
  initialTab: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function deriveStatus(kpi: CatalogKpi): 'certified' | 'review' | 'draft' {
  const score = kpi.metadata_quality?.completeness_score ?? 0;
  if (score >= 0.8) return 'certified';
  if (score >= 0.5) return 'review';
  return 'draft';
}

const DOMAIN_HUES: Record<string, number> = {
  revenue: 250,
  growth: 150,
  product: 310,
  retention: 30,
  operations: 130,
};

function domainHue(name: string): number {
  return DOMAIN_HUES[name] ?? 200;
}

// ─── Inline Components ────────────────────────────────────────────────────────

function StatusDot({ status }: { status: 'certified' | 'review' | 'draft' }) {
  const colors: Record<string, string> = {
    certified: 'oklch(0.6 0.15 150)',
    review: 'oklch(0.7 0.15 75)',
    draft: 'var(--ink-4)',
  };
  return (
    <span
      style={{
        display: 'inline-block',
        width: 6,
        height: 6,
        borderRadius: 99,
        background: colors[status],
        flexShrink: 0,
      }}
    />
  );
}

function Pill({
  tone,
  children,
}: {
  tone: 'positive' | 'warn' | 'draft' | 'neutral';
  children: React.ReactNode;
}) {
  const styles: Record<string, { bg: string; fg: string }> = {
    positive: { bg: 'var(--positive-bg)', fg: 'var(--positive-fg)' },
    warn: { bg: 'oklch(0.22 0.05 75 / 0.4)', fg: 'oklch(0.75 0.15 75)' },
    draft: { bg: 'var(--line-2)', fg: 'var(--ink-4)' },
    neutral: { bg: 'var(--hover)', fg: 'var(--ink-3)' },
  };
  const s = styles[tone];
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 7px',
        borderRadius: 999,
        fontSize: 10.5,
        fontWeight: 500,
        background: s.bg,
        color: s.fg,
      }}
    >
      {children}
    </span>
  );
}

function DomainDot({ domain }: { domain: string }) {
  const hue = domainHue(domain);
  return (
    <span
      style={{
        display: 'inline-block',
        width: 7,
        height: 7,
        borderRadius: 99,
        background: `oklch(0.6 0.15 ${hue})`,
        flexShrink: 0,
      }}
    />
  );
}

function CountBadge({ count }: { count: number }) {
  return (
    <span
      style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '0.625rem',
        color: 'var(--ink-4)',
        background: 'var(--line-2)',
        padding: '1px 5px',
        borderRadius: 4,
        lineHeight: 1.4,
      }}
    >
      {count}
    </span>
  );
}

// ─── Style constants ──────────────────────────────────────────────────────────

const tableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: '0.8125rem',
};

const thStyle: React.CSSProperties = {
  textAlign: 'left',
  fontWeight: 500,
  fontSize: '0.625rem',
  color: 'var(--ink-4)',
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  padding: '12px var(--pad)',
  borderBottom: '1px solid var(--line)',
};

const tdStyle: React.CSSProperties = {
  padding: '13px var(--pad)',
  borderBottom: '1px solid var(--line-2)',
};

// ─── KPI Table ────────────────────────────────────────────────────────────────

function KpiTable({
  kpis,
  filter,
  domainFilter,
  highlightKpiId,
}: {
  kpis: CatalogKpi[];
  filter: string;
  domainFilter: string;
  highlightKpiId: string | null;
}) {
  const router = useRouter();
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const highlightRef = useRef<HTMLTableRowElement | null>(null);

  const filtered = useMemo(
    () =>
      kpis.filter((kpi) => {
        const matchesText =
          !filter ||
          kpi.kpi_id.toLowerCase().includes(filter.toLowerCase()) ||
          kpi.kpi_key.toLowerCase().includes(filter.toLowerCase()) ||
          (kpi.business?.purpose ?? '').toLowerCase().includes(filter.toLowerCase());
        const matchesDomain =
          domainFilter === 'all' || (kpi.domain_tag ?? []).includes(domainFilter);
        return matchesText && matchesDomain;
      }),
    [kpis, filter, domainFilter]
  );

  useEffect(() => {
    if (highlightKpiId && highlightRef.current) {
      setTimeout(() => {
        highlightRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 80);
    }
  }, [highlightKpiId]);

  return (
    <div
      style={{
        background: 'var(--panel)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--radius)',
        overflow: 'hidden',
      }}
    >
      <table style={tableStyle}>
        <thead>
          <tr>
            {['Name', 'Ref', 'Type', 'Domain', 'Owner', 'Grain', 'Updated'].map((h) => (
              <th key={h} style={thStyle}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filtered.map((kpi) => {
            const status = deriveStatus(kpi);
            const isHighlighted = highlightKpiId === kpi.kpi_id;
            const isHovered = hoveredId === kpi.kpi_id;
            const domain = (kpi.domain_tag ?? [])[0] ?? '';

            const rowStyle: React.CSSProperties = {
              ...tdStyle,
              cursor: 'pointer',
              background: isHighlighted
                ? 'var(--accent-soft)'
                : isHovered
                ? 'var(--hover)'
                : 'transparent',
              boxShadow: isHighlighted ? '0 0 0 1px var(--accent) inset' : undefined,
              transition: 'background 120ms',
            };

            const statusTone =
              status === 'certified' ? 'positive' : status === 'review' ? 'warn' : 'draft';

            return (
              <tr
                key={kpi.kpi_id}
                ref={isHighlighted ? highlightRef : undefined}
                onClick={() => router.push(`/catalog/${kpi.kpi_id}`)}
                onMouseEnter={() => setHoveredId(kpi.kpi_id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                {/* Name */}
                <td style={{ ...rowStyle }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <StatusDot status={status} />
                    <span style={{ fontWeight: 500, color: 'var(--ink)' }}>{kpi.kpi_key}</span>
                    <Pill tone={statusTone}>{status}</Pill>
                  </div>
                </td>
                {/* Ref */}
                <td style={{ ...rowStyle, fontFamily: 'var(--font-mono)', color: 'var(--ink-4)', fontSize: '0.75rem' }}>
                  {kpi.kpi_id}
                </td>
                {/* Type */}
                <td style={{ ...rowStyle, color: 'var(--ink-3)' }}>{kpi.calc_type}</td>
                {/* Domain */}
                <td style={{ ...rowStyle }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    {domain && <DomainDot domain={domain} />}
                    <span style={{ color: 'var(--ink-3)' }}>{domain || '—'}</span>
                  </div>
                </td>
                {/* Owner */}
                <td style={{ ...rowStyle, color: 'var(--ink-3)' }}>
                  {kpi.governance?.business_owner ?? '—'}
                </td>
                {/* Grain */}
                <td style={{ ...rowStyle, color: 'var(--ink-3)' }}>
                  {kpi.business?.grain_scope ?? '—'}
                </td>
                {/* Updated */}
                <td style={{ ...rowStyle, color: 'var(--ink-4)', fontSize: '0.75rem' }}>
                  {kpi.metadata_quality?.last_review ?? '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {filtered.length === 0 && (
        <p
          style={{
            margin: 0,
            padding: 'var(--pad)',
            textAlign: 'center',
            color: 'var(--ink-4)',
            fontSize: '0.8125rem',
            lineHeight: 1.55,
          }}
        >
          No KPIs match the filter.
        </p>
      )}
      <div
        style={{
          padding: '8px var(--pad)',
          fontSize: '0.6875rem',
          color: 'var(--ink-4)',
          borderTop: '1px solid var(--line-2)',
        }}
      >
        Showing {filtered.length} of {kpis.length} KPIs
      </div>
    </div>
  );
}

// ─── Brackets Table ───────────────────────────────────────────────────────────

function BracketsTable({ brackets, filter }: { brackets: UseCaseBracketV20Lean[]; filter: string }) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const filtered = useMemo(
    () =>
      brackets.filter(
        (b) =>
          !filter ||
          b.id.toLowerCase().includes(filter.toLowerCase()) ||
          b.title.toLowerCase().includes(filter.toLowerCase()) ||
          b.domain.toLowerCase().includes(filter.toLowerCase())
      ),
    [brackets, filter]
  );

  return (
    <div
      style={{
        background: 'var(--panel)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--radius)',
        overflow: 'hidden',
      }}
    >
      <table style={tableStyle}>
        <thead>
          <tr>
            {['Name', 'ID', 'Domain', 'Strategic KPI', 'Actions'].map((h) => (
              <th key={h} style={thStyle}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filtered.map((bracket) => {
            const isHovered = hoveredId === bracket.id;
            const rowBg: React.CSSProperties = {
              background: isHovered ? 'var(--hover)' : 'transparent',
              transition: 'background 120ms',
            };
            return (
              <tr
                key={bracket.id}
                onMouseEnter={() => setHoveredId(bracket.id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                <td style={{ ...tdStyle, ...rowBg, fontWeight: 500, color: 'var(--ink)' }}>
                  {bracket.title}
                </td>
                <td
                  style={{
                    ...tdStyle,
                    ...rowBg,
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--ink-4)',
                    fontSize: '0.75rem',
                  }}
                >
                  {bracket.id}
                </td>
                <td style={{ ...tdStyle, ...rowBg }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <DomainDot domain={bracket.domain.toLowerCase()} />
                    <span style={{ color: 'var(--ink-3)' }}>{bracket.domain}</span>
                  </div>
                </td>
                <td
                  style={{
                    ...tdStyle,
                    ...rowBg,
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--ink-3)',
                    fontSize: '0.75rem',
                  }}
                >
                  {bracket.orchestration?.strategic_kpi_id ?? '—'}
                </td>
                <td style={{ ...tdStyle, ...rowBg }}>
                  <CountBadge
                    count={(bracket.orchestration?.action_code_ids ?? []).length}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {filtered.length === 0 && (
        <p
          style={{
            margin: 0,
            padding: 'var(--pad)',
            textAlign: 'center',
            color: 'var(--ink-4)',
            fontSize: '0.8125rem',
            lineHeight: 1.55,
          }}
        >
          No brackets match the filter.
        </p>
      )}
      <div
        style={{
          padding: '8px var(--pad)',
          fontSize: '0.6875rem',
          color: 'var(--ink-4)',
          borderTop: '1px solid var(--line-2)',
        }}
      >
        Showing {filtered.length} of {brackets.length} brackets
      </div>
    </div>
  );
}

// ─── Actions Table ────────────────────────────────────────────────────────────

function ActionsTable({
  actions,
  filter,
}: {
  actions: ActionCodeDefinitionV20AIMirror[];
  filter: string;
}) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const filtered = useMemo(
    () =>
      actions.filter(
        (a) =>
          !filter ||
          a.id.toLowerCase().includes(filter.toLowerCase()) ||
          a.name.toLowerCase().includes(filter.toLowerCase()) ||
          a.owner_domain.toLowerCase().includes(filter.toLowerCase())
      ),
    [actions, filter]
  );

  function actionStatusTone(
    status: string
  ): 'positive' | 'warn' | 'draft' | 'neutral' {
    if (status === 'active') return 'positive';
    if (status === 'deprecated') return 'warn';
    return 'draft';
  }

  return (
    <div
      style={{
        background: 'var(--panel)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--radius)',
        overflow: 'hidden',
      }}
    >
      <table style={tableStyle}>
        <thead>
          <tr>
            {['Name', 'ID', 'Domain', 'Status', 'KPI Refs'].map((h) => (
              <th key={h} style={thStyle}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filtered.map((action) => {
            const isHovered = hoveredId === action.id;
            const rowBg: React.CSSProperties = {
              background: isHovered ? 'var(--hover)' : 'transparent',
              transition: 'background 120ms',
            };
            const kpiCount =
              (action.kpis?.trigger_kpis?.length ?? 0) +
              (action.kpis?.guardrail_kpis?.length ?? 0) +
              (action.kpis?.outcome_kpis?.length ?? 0);

            return (
              <tr
                key={action.id}
                onMouseEnter={() => setHoveredId(action.id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                <td style={{ ...tdStyle, ...rowBg, fontWeight: 500, color: 'var(--ink)' }}>
                  {action.name}
                </td>
                <td
                  style={{
                    ...tdStyle,
                    ...rowBg,
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--ink-4)',
                    fontSize: '0.75rem',
                  }}
                >
                  {action.id}
                </td>
                <td style={{ ...tdStyle, ...rowBg }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <DomainDot domain={action.owner_domain.toLowerCase()} />
                    <span style={{ color: 'var(--ink-3)' }}>{action.owner_domain}</span>
                  </div>
                </td>
                <td style={{ ...tdStyle, ...rowBg }}>
                  <Pill tone={actionStatusTone(action.status)}>{action.status}</Pill>
                </td>
                <td style={{ ...tdStyle, ...rowBg }}>
                  <CountBadge count={kpiCount} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {filtered.length === 0 && (
        <p
          style={{
            margin: 0,
            padding: 'var(--pad)',
            textAlign: 'center',
            color: 'var(--ink-4)',
            fontSize: '0.8125rem',
            lineHeight: 1.55,
          }}
        >
          No actions match the filter.
        </p>
      )}
      <div
        style={{
          padding: '8px var(--pad)',
          fontSize: '0.6875rem',
          color: 'var(--ink-4)',
          borderTop: '1px solid var(--line-2)',
        }}
      >
        Showing {filtered.length} of {actions.length} actions
      </div>
    </div>
  );
}

// ─── Main CatalogLibrary Component ────────────────────────────────────────────

export function CatalogLibrary({
  kpis,
  brackets,
  actions,
  highlightKpiId,
  initialTab,
}: Props) {
  const validTab = (t: string): TabId =>
    t === 'brackets' ? 'brackets' : t === 'actions' ? 'actions' : 'kpis';

  const [activeTab, setActiveTab] = useState<TabId>(validTab(initialTab));
  const [search, setSearch] = useState('');
  const [domainFilter, setDomainFilter] = useState('all');
  const searchRef = useRef<HTMLInputElement>(null);

  const domains = useMemo(
    () => [...new Set(kpis.flatMap((k) => k.domain_tag ?? []))].sort(),
    [kpis]
  );

  // "/" keyboard shortcut to focus search
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (
        e.key === '/' &&
        document.activeElement !== searchRef.current &&
        !(document.activeElement instanceof HTMLInputElement) &&
        !(document.activeElement instanceof HTMLTextAreaElement)
      ) {
        e.preventDefault();
        searchRef.current?.focus();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const tabs: { id: TabId; label: string; count: number }[] = [
    { id: 'kpis', label: 'KPIs', count: kpis.length },
    { id: 'brackets', label: 'Brackets', count: brackets.length },
    { id: 'actions', label: 'Actions', count: actions.length },
  ];

  return (
    <div
      style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: 'var(--pad)',
        display: 'flex',
        flexDirection: 'column',
        gap: 24,
      }}
    >
      {/* Page header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 16,
        }}
      >
        <div>
          <h1
            style={{
              margin: 0,
              fontSize: 28,
              fontWeight: 500,
              letterSpacing: '-0.02em',
              color: 'var(--ink)',
              lineHeight: 1.2,
            }}
          >
            Library
          </h1>
          <p
            style={{
              margin: '6px 0 0',
              fontSize: '0.875rem',
              color: 'var(--ink-3)',
              lineHeight: 1.5,
            }}
          >
            The single source of truth for every KPI, bracket, and action code.
          </p>
        </div>
        <button
          onClick={() =>
            window.dispatchEvent(new CustomEvent('studio:open-wizard'))
          }
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 16px',
            borderRadius: 'var(--radius)',
            border: 'none',
            background: 'var(--accent)',
            color: '#fff',
            fontSize: '0.8125rem',
            fontWeight: 500,
            cursor: 'pointer',
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          + New element
        </button>
      </div>

      {/* Tab bar */}
      <div
        style={{
          display: 'flex',
          gap: 0,
          borderBottom: '1px solid var(--line)',
          marginBottom: -1,
        }}
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setSearch('');
                setDomainFilter('all');
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '10px 16px',
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: isActive ? 500 : 400,
                color: isActive ? 'var(--ink)' : 'var(--ink-3)',
                borderBottom: isActive
                  ? '1.5px solid var(--accent)'
                  : '1.5px solid transparent',
                marginBottom: -1,
                transition: 'color 120ms',
              }}
            >
              {tab.label}
              <CountBadge count={tab.count} />
            </button>
          );
        })}
      </div>

      {/* Search + filter row */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <div
          style={{
            flex: 1,
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <span
            style={{
              position: 'absolute',
              left: 10,
              color: 'var(--ink-4)',
              display: 'flex',
              pointerEvents: 'none',
            }}
          >
            <PhIcon name="magnifying-glass" size={14} />
          </span>
          <input
            ref={searchRef}
            type="text"
            placeholder={`Search ${activeTab}…`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 36px 8px 32px',
              border: '1px solid var(--line)',
              borderRadius: 'var(--radius)',
              background: 'var(--panel)',
              color: 'var(--ink)',
              fontSize: '0.8125rem',
              outline: 'none',
            }}
          />
          <kbd
            style={{
              position: 'absolute',
              right: 10,
              fontSize: '0.625rem',
              color: 'var(--ink-4)',
              background: 'var(--line-2)',
              border: '1px solid var(--line)',
              borderRadius: 4,
              padding: '1px 5px',
              lineHeight: 1.6,
              pointerEvents: 'none',
            }}
          >
            /
          </kbd>
        </div>

        {activeTab === 'kpis' && (
          <select
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
            style={{
              padding: '8px 12px',
              border: '1px solid var(--line)',
              borderRadius: 'var(--radius)',
              background: 'var(--panel)',
              color: 'var(--ink)',
              fontSize: '0.8125rem',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <option value="all">All Domains</option>
            {domains.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        )}

        <button
          style={{
            padding: '8px 14px',
            border: '1px solid var(--line)',
            borderRadius: 'var(--radius)',
            background: 'transparent',
            color: 'var(--ink-3)',
            fontSize: '0.8125rem',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          Filter
        </button>
      </div>

      {/* Tab content */}
      {activeTab === 'kpis' && (
        <KpiTable
          kpis={kpis}
          filter={search}
          domainFilter={domainFilter}
          highlightKpiId={highlightKpiId}
        />
      )}
      {activeTab === 'brackets' && (
        <BracketsTable brackets={brackets} filter={search} />
      )}
      {activeTab === 'actions' && (
        <ActionsTable actions={actions} filter={search} />
      )}
    </div>
  );
}
