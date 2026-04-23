'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { CatalogKpi } from '@/lib/core/catalog-loader';
import type { FactsheetSummary } from '@/lib/core/factsheet-loader';
import { AiField } from '@/components/ai/ai-field';
import {
  KpiDetailTabContent,
  type TabId,
  card,
  cardHead,
} from '@/components/registry/kpi-detail-tabs';

// ─── Types ────────────────────────────────────────────────────────────────────

interface LinkedBracket {
  id: string;
  title: string;
  domain: string;
}

interface Props {
  kpi: CatalogKpi;
  linkedBrackets: LinkedBracket[];
  factsheet: FactsheetSummary | null;
  factsheetRole: string | null;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function deriveStatus(kpi: CatalogKpi): 'certified' | 'review' | 'draft' {
  const score = kpi.metadata_quality?.completeness_score ?? 0;
  if (score >= 0.8) return 'certified';
  if (score >= 0.5) return 'review';
  return 'draft';
}

const STATUS_COLORS: Record<string, { bg: string; fg: string }> = {
  certified: { bg: 'oklch(0.18 0.05 150 / 0.5)', fg: 'oklch(0.6 0.15 150)' },
  review: { bg: 'oklch(0.22 0.05 75 / 0.4)', fg: 'oklch(0.75 0.15 75)' },
  draft: { bg: 'var(--line-2)', fg: 'var(--ink-4)' },
};

function StatusPill({ status }: { status: 'certified' | 'review' | 'draft' }) {
  const s = STATUS_COLORS[status];
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: 999,
        fontSize: 10.5,
        fontWeight: 500,
        background: s.bg,
        color: s.fg,
      }}
    >
      {status}
    </span>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: 999,
        fontSize: 10.5,
        fontWeight: 500,
        background: 'var(--hover)',
        color: 'var(--ink-3)',
      }}
    >
      {children}
    </span>
  );
}

// ─── Right Rail: Properties row ───────────────────────────────────────────────

function PropRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '100px 1fr',
        gap: 8,
        padding: '6px 0',
        borderBottom: '1px solid var(--line-2)',
        alignItems: 'start',
      }}
    >
      <span
        style={{ fontSize: 11.5, color: 'var(--ink-4)', lineHeight: 1.5, paddingTop: 1 }}
      >
        {label}
      </span>
      <span style={{ fontSize: 11.5, color: 'var(--ink-2)', lineHeight: 1.5 }}>
        {value || '—'}
      </span>
    </div>
  );
}

// ─── Right Rail: Domain dot ───────────────────────────────────────────────────

const DOMAIN_HUES: Record<string, number> = {
  revenue: 250,
  growth: 150,
  product: 310,
  retention: 30,
  operations: 130,
};

function DomainDot({ domain }: { domain: string }) {
  const hue = DOMAIN_HUES[domain.toLowerCase()] ?? 200;
  return (
    <span
      style={{
        display: 'inline-block',
        width: 7,
        height: 7,
        borderRadius: 99,
        background: `oklch(0.6 0.15 ${hue})`,
        flexShrink: 0,
        marginRight: 5,
        verticalAlign: 'middle',
      }}
    />
  );
}

// ─── Main KpiDetail component ─────────────────────────────────────────────────

export function KpiDetail({ kpi, linkedBrackets, factsheet, factsheetRole }: Props) {
  const status = deriveStatus(kpi);
  const domain = (kpi.domain_tag ?? [])[0] ?? '';

  // Inline edit state
  const [name, setName] = useState(kpi.kpi_key);
  const [description, setDescription] = useState(
    kpi.business?.purpose ?? kpi.business?.definition ?? ''
  );
  const [editingName, setEditingName] = useState(false);
  const [editingDesc, setEditingDesc] = useState(false);

  // Tab state
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  const TABS: { id: TabId; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'definition', label: 'Definition' },
    { id: 'lineage', label: 'Lineage' },
    { id: 'comments', label: 'Comments (2)' },
    { id: 'history', label: 'History' },
  ];

  const completenessScore = kpi.metadata_quality?.completeness_score ?? 0;

  return (
    <div style={{ display: 'flex', height: '100%', gap: 0, minHeight: 0 }}>
      {/* ── Main scrollable area ─────────────────────────────────────── */}
      <div style={{ flex: 1, overflow: 'auto', minWidth: 0 }}>
        <div style={{ padding: 'var(--pad)', maxWidth: 860, margin: '0 auto' }}>

          {/* Back link */}
          <Link
            href="/catalog"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              fontSize: '0.75rem',
              color: 'var(--ink-3)',
              textDecoration: 'none',
              marginBottom: 16,
            }}
          >
            ‹ Back to Library
          </Link>

          {/* Status / type / domain row */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 8,
              flexWrap: 'wrap',
            }}
          >
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.625rem',
                color: 'var(--ink-3)',
              }}
            >
              {kpi.kpi_id}
            </span>
            <StatusPill status={status} />
            {kpi.calc_type && <Pill>{kpi.calc_type}</Pill>}
            {domain && <Pill>{domain}</Pill>}
          </div>

          {/* Inline-editable name */}
          {editingName ? (
            <div onBlur={() => setEditingName(false)} style={{ marginBottom: 12 }}>
              <AiField
                entityType="kpi"
                entityId={kpi.kpi_id}
                entityName={name}
                fieldName="kpi_key"
                fieldLabel="KPI Name"
                value={name}
                onChange={(v) => setName(v)}
                placeholder="KPI name…"
                domainContext={(kpi.domain_tag ?? [])[0]}
                style={{ fontSize: 24, fontWeight: 500 }}
              />
            </div>
          ) : (
            <h1
              onClick={() => setEditingName(true)}
              title="Click to edit"
              style={{
                margin: '0 0 12px',
                fontSize: 36,
                fontWeight: 500,
                letterSpacing: '-0.025em',
                lineHeight: 1.15,
                color: 'var(--ink)',
                cursor: 'text',
              }}
            >
              {name}
            </h1>
          )}

          {/* Inline-editable description */}
          {editingDesc ? (
            <div onBlur={() => setEditingDesc(false)}>
              <AiField
                entityType="kpi"
                entityId={kpi.kpi_id}
                entityName={name}
                fieldName="description"
                fieldLabel="Description"
                value={description}
                onChange={(v) => setDescription(v)}
                multiline
                rows={3}
                placeholder="Click to add a description…"
                domainContext={(kpi.domain_tag ?? [])[0]}
                style={{ fontSize: 14.5, lineHeight: 1.6 }}
              />
            </div>
          ) : (
            <p
              onClick={() => setEditingDesc(true)}
              title="Click to edit"
              style={{
                margin: 0,
                fontSize: 14.5,
                lineHeight: 1.6,
                color: 'var(--ink-2)',
                cursor: 'text',
                minHeight: 22,
              }}
            >
              {description || (
                <span style={{ color: 'var(--ink-4)', fontStyle: 'italic' }}>
                  Click to add a description…
                </span>
              )}
            </p>
          )}

          {/* Tab bar */}
          <div
            style={{
              display: 'flex',
              gap: 2,
              borderBottom: '1px solid var(--line)',
              marginTop: 22,
              marginBottom: 20,
            }}
          >
            {TABS.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    padding: '9px 14px',
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
                    whiteSpace: 'nowrap',
                  }}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Tab content (rendered from kpi-detail-tabs.tsx) */}
          <KpiDetailTabContent
            kpi={kpi}
            linkedBrackets={linkedBrackets}
            activeTab={activeTab}
            factsheet={factsheet}
            factsheetRole={factsheetRole}
          />
        </div>
      </div>

      {/* ── Right rail ───────────────────────────────────────────────── */}
      <aside
        style={{
          width: 300,
          flexShrink: 0,
          borderLeft: '1px solid var(--line)',
          padding: 'var(--pad)',
          overflow: 'auto',
          background: 'var(--bg)',
        }}
      >
        {/* Properties section */}
        <div style={card}>
          <div style={cardHead}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
              Properties
            </span>
          </div>
          <div style={{ padding: '6px var(--pad) 10px' }}>
            <PropRow label="Owner" value={kpi.governance?.business_owner} />
            <PropRow label="Data Owner" value={kpi.governance?.data_owner} />
            <PropRow label="Steward" value={kpi.governance?.steward} />
            <PropRow
              label="Domain"
              value={
                domain ? (
                  <>
                    <DomainDot domain={domain} />
                    {domain}
                  </>
                ) : (
                  '—'
                )
              }
            />
            <PropRow label="Type" value={kpi.calc_type} />
            <PropRow label="Grain" value={kpi.business?.grain_scope} />
            <PropRow label="Unit" value={kpi.business?.unit_format} />
            <PropRow label="Review Cycle" value={kpi.governance?.review_cycle} />
            <PropRow label="Version" value={kpi.governance?.version} />
            <PropRow
              label="Completeness"
              value={`${Math.round(completenessScore * 100)}%`}
            />
          </div>
        </div>

        {/* Studio AI Suggestions */}
        <div
          style={{
            padding: 14,
            borderRadius: 10,
            background: 'linear-gradient(180deg, var(--accent-soft), transparent)',
            border: '1px solid var(--line)',
            marginTop: 24,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              marginBottom: 8,
              fontSize: '0.75rem',
            }}
          >
            <span>✦</span>
            <span style={{ fontWeight: 500 }}>Studio AI</span>
          </div>
          <div
            style={{
              fontSize: '0.8125rem',
              color: 'var(--ink-2)',
              lineHeight: 1.5,
              marginBottom: 10,
            }}
          >
            Your definition references{' '}
            <span
              style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}
            >
              {kpi.technical?.dax_name ?? kpi.kpi_id}
            </span>
            . Want me to suggest additional dimensions or validate the formula?
          </div>
          <button
            onClick={() =>
              window.dispatchEvent(new CustomEvent('studio:open-chat'))
            }
            style={{
              display: 'block',
              width: '100%',
              padding: '8px 0',
              border: 'none',
              borderRadius: 'var(--radius)',
              background: 'var(--ink)',
              color: 'var(--bg)',
              fontSize: '0.8125rem',
              fontWeight: 500,
              cursor: 'pointer',
              textAlign: 'center',
            }}
          >
            Ask Studio AI
          </button>
        </div>
      </aside>
    </div>
  );
}
