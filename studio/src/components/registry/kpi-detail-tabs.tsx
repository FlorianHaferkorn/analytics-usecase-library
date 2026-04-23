'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { CatalogKpi } from '@/lib/core/catalog-loader';

// ─── Types ────────────────────────────────────────────────────────────────────

interface LinkedBracket {
  id: string;
  title: string;
  domain: string;
}

export interface KpiDetailTabsProps {
  kpi: CatalogKpi;
  linkedBrackets: LinkedBracket[];
  activeTab: TabId;
}

export type TabId = 'overview' | 'definition' | 'lineage' | 'comments' | 'history';

// ─── Sparkline ────────────────────────────────────────────────────────────────

export function Sparkline({
  data,
  color = 'var(--accent)',
  height = 40,
}: {
  data: number[];
  color?: string;
  height?: number;
}) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const pts: [number, number][] = data.map((v, i) => [
    (i / (data.length - 1)) * 100,
    height - ((v - min) / range) * (height - 4) - 2,
  ]);
  const d = 'M' + pts.map((p) => `${p[0]}%,${p[1]}`).join(' L');
  return (
    <svg
      width="100%"
      height={height}
      style={{ display: 'block' }}
      preserveAspectRatio="none"
    >
      <path d={d + ` L100%,${height} L0,${height} Z`} fill={color} opacity="0.08" />
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

// ─── Card style constants ─────────────────────────────────────────────────────

export const card: React.CSSProperties = {
  background: 'var(--panel)',
  border: '1px solid var(--line)',
  borderRadius: 'var(--radius)',
  overflow: 'hidden',
  marginBottom: 'var(--gap)',
};

export const cardHead: React.CSSProperties = {
  padding: '16px var(--pad)',
  borderBottom: '1px solid var(--line-2)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
};

const cardBody: React.CSSProperties = {
  padding: 'var(--pad)',
};

// ─── Pill helper ──────────────────────────────────────────────────────────────

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '3px 8px',
        borderRadius: 6,
        background: 'var(--hover)',
        color: 'var(--ink-3)',
        fontSize: '0.75rem',
        fontFamily: 'var(--font-mono)',
        marginRight: 6,
        marginBottom: 6,
      }}
    >
      {children}
    </span>
  );
}

// ─── Tab: Overview ────────────────────────────────────────────────────────────

function OverviewTab({ kpi }: { kpi: CatalogKpi }) {
  const DEMO_SPARK = [80, 85, 82, 88, 90, 95, 92, 98, 100, 105, 108, 112];
  const measures = kpi.technical?.depends_on_measures ?? [];
  const refs = kpi.use_case_ref ?? [];

  return (
    <div>
      {/* Latest Value card */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Latest value
          </span>
        </div>
        <div style={cardBody}>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 24, marginBottom: 12 }}>
            <span
              style={{
                fontSize: 48,
                fontWeight: 300,
                color: 'var(--ink)',
                lineHeight: 1,
                fontFamily: 'var(--font-display)',
              }}
            >
              —
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--ink-4)', marginBottom: 8 }}>
              No live data connected
            </span>
          </div>
          <Sparkline data={DEMO_SPARK} />
        </div>
      </div>

      {/* Dimensions card */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Dimensions
          </span>
        </div>
        <div style={cardBody}>
          {measures.length > 0 ? (
            <div>{measures.map((m) => <Tag key={m}>{m}</Tag>)}</div>
          ) : (
            <span style={{ fontSize: '0.8125rem', color: 'var(--ink-4)' }}>
              No dimensions defined
            </span>
          )}
        </div>
      </div>

      {/* Use Case References card */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Use Case References
          </span>
        </div>
        <div style={cardBody}>
          {refs.length > 0 ? (
            <div>
              {refs.map((ref) => (
                <Link
                  key={ref}
                  href={`/catalog?kpi=${ref}`}
                  style={{
                    display: 'inline-block',
                    padding: '3px 8px',
                    borderRadius: 6,
                    background: 'var(--accent-soft)',
                    color: 'var(--accent)',
                    fontSize: '0.75rem',
                    fontFamily: 'var(--font-mono)',
                    textDecoration: 'none',
                    marginRight: 6,
                    marginBottom: 6,
                  }}
                >
                  {ref}
                </Link>
              ))}
            </div>
          ) : (
            <span style={{ fontSize: '0.8125rem', color: 'var(--ink-4)' }}>
              No use case references
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Tab: Definition ──────────────────────────────────────────────────────────

function DefinitionTab({ kpi }: { kpi: CatalogKpi }) {
  const [copied, setCopied] = useState(false);
  const expr = kpi.technical?.dax_expression ?? '';

  function handleCopy() {
    void navigator.clipboard.writeText(expr);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div>
      <div style={card}>
        <div style={cardHead}>
          <div>
            <div style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
              DAX / SQL definition
            </div>
            <div
              style={{
                fontSize: '0.75rem',
                color: 'var(--ink-4)',
                fontFamily: 'var(--font-mono)',
                marginTop: 2,
              }}
            >
              ref: {kpi.technical?.dax_name ?? '—'}
            </div>
          </div>
          <button
            onClick={handleCopy}
            style={{
              padding: '5px 10px',
              border: '1px solid var(--line)',
              borderRadius: 6,
              background: 'transparent',
              color: copied ? 'var(--accent)' : 'var(--ink-3)',
              fontSize: '0.75rem',
              cursor: 'pointer',
            }}
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
        <pre
          style={{
            margin: 0,
            padding: 'var(--pad)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8125rem',
            color: 'var(--ink-2)',
            lineHeight: 1.6,
            overflowX: 'auto',
            background: 'var(--bg)',
            borderBottom: '1px solid var(--line-2)',
          }}
        >
          {expr || '-- No expression defined'}
        </pre>
        <div style={{ ...cardBody, borderTop: '1px solid var(--line-2)' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--ink-3)', marginBottom: 6 }}>
            Description
          </div>
          <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--ink-2)', lineHeight: 1.6 }}>
            {kpi.technical?.description || kpi.business?.definition || '—'}
          </p>
        </div>
      </div>
    </div>
  );
}

// ─── Tab: Lineage ──────────────────────────────────────────────────────────────

function LineageTab({ kpi, linkedBrackets }: { kpi: CatalogKpi; linkedBrackets: LinkedBracket[] }) {
  const lineage = kpi.technical?.lineage ?? [];

  return (
    <div>
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Data Lineage
          </span>
        </div>
        <div style={cardBody}>
          <div style={{ marginBottom: 20 }}>
            <div
              style={{
                fontSize: '0.6875rem',
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                color: 'var(--ink-4)',
                marginBottom: 10,
              }}
            >
              Depends on:
            </div>
            {lineage.length > 0 ? (
              <div>{lineage.map((l) => <Tag key={l}>{l}</Tag>)}</div>
            ) : (
              <span style={{ fontSize: '0.8125rem', color: 'var(--ink-4)' }}>No lineage defined</span>
            )}
          </div>

          <div style={{ marginBottom: 20 }}>
            <div
              style={{
                fontSize: '0.6875rem',
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                color: 'var(--ink-4)',
                marginBottom: 10,
              }}
            >
              Referenced by brackets:
            </div>
            {linkedBrackets.length > 0 ? (
              <div>
                {linkedBrackets.map((b) => (
                  <div
                    key={b.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '8px 0',
                      borderBottom: '1px solid var(--line-2)',
                    }}
                  >
                    <span
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.75rem',
                        color: 'var(--ink-4)',
                      }}
                    >
                      {b.id}
                    </span>
                    <span style={{ fontSize: '0.8125rem', color: 'var(--ink)', flex: 1 }}>
                      {b.title}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--ink-4)' }}>{b.domain}</span>
                  </div>
                ))}
              </div>
            ) : (
              <span style={{ fontSize: '0.8125rem', color: 'var(--ink-4)' }}>
                Not referenced by any brackets
              </span>
            )}
          </div>

          <button
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '7px 14px',
              border: '1px solid var(--line)',
              borderRadius: 6,
              background: 'transparent',
              color: 'var(--ink-3)',
              fontSize: '0.8125rem',
              cursor: 'pointer',
            }}
          >
            View in Canvas →
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Tab: Comments ────────────────────────────────────────────────────────────

function CommentsTab() {
  const [comment, setComment] = useState('');

  const STATIC_COMMENTS = [
    {
      author: 'A. Haferkorn',
      text: 'This KPI is certified and matches the board definition.',
      time: '2h ago',
    },
    {
      author: 'F. Müller',
      text: 'Can we add a breakdown by region? Useful for the review.',
      time: '1d ago',
    },
  ];

  return (
    <div>
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Comments
          </span>
        </div>
        <div style={{ padding: '0 var(--pad)' }}>
          {STATIC_COMMENTS.map((c, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                gap: 12,
                padding: '14px 0',
                borderBottom: '1px solid var(--line-2)',
              }}
            >
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 999,
                  background: 'var(--accent-soft)',
                  color: 'var(--accent)',
                  fontSize: '0.6875rem',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {c.author.slice(0, 2)}
              </div>
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    display: 'flex',
                    gap: 8,
                    alignItems: 'center',
                    marginBottom: 4,
                  }}
                >
                  <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
                    {c.author}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--ink-4)' }}>{c.time}</span>
                </div>
                <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--ink-2)', lineHeight: 1.5 }}>
                  {c.text}
                </p>
              </div>
            </div>
          ))}
        </div>
        <div style={{ padding: 'var(--pad)' }}>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Add a comment…"
            rows={3}
            style={{
              width: '100%',
              padding: '10px 12px',
              border: '1px solid var(--line)',
              borderRadius: 'var(--radius)',
              background: 'var(--bg)',
              color: 'var(--ink)',
              fontSize: '0.8125rem',
              lineHeight: 1.5,
              resize: 'vertical',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </div>
    </div>
  );
}

// ─── Tab: History ─────────────────────────────────────────────────────────────

function HistoryTab() {
  const HISTORY = [
    { author: 'A. Haferkorn', action: 'certified definition', time: '2h ago' },
    { author: 'F. Müller', action: 'edited description', time: '1d ago' },
    { author: 'A. Haferkorn', action: 'updated SQL expression', time: '3d ago' },
    { author: 'F. Müller', action: 'created KPI', time: '2w ago' },
  ];

  return (
    <div>
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            History
          </span>
        </div>
        <table
          style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}
        >
          <tbody>
            {HISTORY.map((h, i) => (
              <tr key={i}>
                <td
                  style={{
                    padding: '12px var(--pad)',
                    borderBottom: '1px solid var(--line-2)',
                    color: 'var(--ink)',
                    fontWeight: 500,
                    width: 140,
                  }}
                >
                  {h.author}
                </td>
                <td
                  style={{
                    padding: '12px var(--pad)',
                    borderBottom: '1px solid var(--line-2)',
                    color: 'var(--ink-2)',
                  }}
                >
                  {h.action}
                </td>
                <td
                  style={{
                    padding: '12px var(--pad)',
                    borderBottom: '1px solid var(--line-2)',
                    color: 'var(--ink-4)',
                    fontSize: '0.75rem',
                    textAlign: 'right',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {h.time}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Tab content dispatcher ───────────────────────────────────────────────────

export function KpiDetailTabContent({ kpi, linkedBrackets, activeTab }: KpiDetailTabsProps) {
  if (activeTab === 'overview') return <OverviewTab kpi={kpi} />;
  if (activeTab === 'definition') return <DefinitionTab kpi={kpi} />;
  if (activeTab === 'lineage') return <LineageTab kpi={kpi} linkedBrackets={linkedBrackets} />;
  if (activeTab === 'comments') return <CommentsTab />;
  if (activeTab === 'history') return <HistoryTab />;
  return null;
}
