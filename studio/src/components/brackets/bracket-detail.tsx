'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import type { FactsheetSummary } from '@/lib/core/factsheet-loader';
import type { ResolvedRole } from '@/lib/core/org-role-loader';
import type { DecisionSpine } from '@/lib/schemas/decision-spine';
import { RoleChip } from '@/components/ui/role-chip';
import { card, cardHead } from '@/components/registry/kpi-detail-tabs';
import { BracketOverviewTab } from '@/components/brackets/tabs/bracket-overview-tab';
import { BracketKpisTab } from '@/components/brackets/tabs/bracket-kpis-tab';
import { ReportLayoutTab } from '@/components/brackets/tabs/report-layout-tab';
import { ActionsTab } from '@/components/brackets/tabs/actions-tab';
import { GovernanceTab } from '@/components/brackets/tabs/governance-tab';
import { SpinePanel } from '@/components/spine/spine-panel';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Props {
  bracket: UseCaseBracketV20Lean;
  factsheet: FactsheetSummary | null;
  ownerRole: ResolvedRole | null;
  stewardRole: ResolvedRole | null;
  spines: DecisionSpine[];
}

type TabId = 'overview' | 'kpis' | 'report-layout' | 'actions' | 'governance';

const TABS: { id: TabId; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'kpis', label: 'KPIs' },
  { id: 'report-layout', label: 'Report Layout' },
  { id: 'actions', label: 'Actions' },
  { id: 'governance', label: 'Governance' },
];

// ─── PropRow ──────────────────────────────────────────────────────────────────

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
      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-4)', lineHeight: 1.5, paddingTop: 1 }}>
        {label}
      </span>
      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-2)', lineHeight: 1.5 }}>
        {value || '—'}
      </span>
    </div>
  );
}

// ─── Domain pill ──────────────────────────────────────────────────────────────

const DOMAIN_HUES: Record<string, number> = {
  commercial: 250,
  finance: 150,
  operations: 130,
  supplychain: 30,
  xd: 310,
};

function DomainPill({ domain }: { domain: string }) {
  const hue = DOMAIN_HUES[domain.toLowerCase()] ?? 200;
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '2px 8px',
        borderRadius: 999,
        fontSize: 'var(--text-xs)',
        fontWeight: 500,
        background: `oklch(0.22 0.05 ${hue} / 0.4)`,
        color: `oklch(0.7 0.15 ${hue})`,
      }}
    >
      {domain}
    </span>
  );
}

// ─── Main BracketDetail component ─────────────────────────────────────────────

export function BracketDetail({ bracket, factsheet, ownerRole, stewardRole, spines }: Props) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [spineOpen, setSpineOpen] = useState(false);
  const [title, setTitle] = useState(bracket.title);
  const [description, setDescription] = useState(
    bracket.value_driver_model?.impact_logic ?? ''
  );
  const [editingTitle, setEditingTitle] = useState(false);
  const [editingDesc, setEditingDesc] = useState(false);
  const titleInputRef = useRef<HTMLInputElement>(null);
  const descTextareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editingTitle) titleInputRef.current?.focus();
  }, [editingTitle]);

  useEffect(() => {
    if (editingDesc) descTextareaRef.current?.focus();
  }, [editingDesc]);

  return (
    <div style={{ display: 'flex', height: '100%', gap: 0, minHeight: 0 }}>
      {/* ── Main scrollable area ────────────────────────────────────── */}
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

          {/* Domain pill + ID badge */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 8,
              flexWrap: 'wrap',
            }}
          >
            <DomainPill domain={bracket.domain} />
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-xs)',
                color: 'var(--ink-3)',
              }}
            >
              {bracket.id}
            </span>
          </div>

          {/* Inline-editable title */}
          {editingTitle ? (
            <input
              ref={titleInputRef}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={() => setEditingTitle(false)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === 'Escape') setEditingTitle(false);
              }}
              style={{
                display: 'block',
                width: '100%',
                fontSize: 30,
                fontWeight: 500,
                letterSpacing: '-0.02em',
                lineHeight: 1.2,
                color: 'var(--ink)',
                background: 'transparent',
                border: 'none',
                borderBottom: '2px solid var(--accent)',
                outline: 'none',
                padding: '0 0 4px',
                marginBottom: 12,
                fontFamily: 'inherit',
                boxSizing: 'border-box',
              }}
            />
          ) : (
            <h1
              onClick={() => setEditingTitle(true)}
              title="Click to edit"
              style={{
                margin: '0 0 12px',
                fontSize: 30,
                fontWeight: 500,
                letterSpacing: '-0.02em',
                lineHeight: 1.2,
                color: 'var(--ink)',
                cursor: 'text',
              }}
            >
              {title}
            </h1>
          )}

          {/* Inline-editable description */}
          {editingDesc ? (
            <textarea
              ref={descTextareaRef}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onBlur={() => setEditingDesc(false)}
              rows={3}
              style={{
                display: 'block',
                width: '100%',
                fontSize: 14.5,
                lineHeight: 1.6,
                color: 'var(--ink-2)',
                background: 'transparent',
                border: 'none',
                borderBottom: '2px solid var(--accent)',
                outline: 'none',
                padding: '0 0 4px',
                resize: 'none',
                fontFamily: 'inherit',
                boxSizing: 'border-box',
              }}
            />
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

          {/* Tab content */}
          {activeTab === 'overview' && (
            <BracketOverviewTab bracket={bracket} factsheet={factsheet} />
          )}
          {activeTab === 'kpis' && (
            <BracketKpisTab bracket={bracket} factsheet={factsheet} />
          )}
          {activeTab === 'report-layout' && (
            <ReportLayoutTab bracket={bracket} />
          )}
          {activeTab === 'actions' && (
            <ActionsTab bracket={bracket} />
          )}
          {activeTab === 'governance' && (
            <GovernanceTab bracket={bracket} factsheet={factsheet} />
          )}
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
        {/* Properties card */}
        <div style={card}>
          <div style={cardHead}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
              Properties
            </span>
          </div>
          <div style={{ padding: '6px var(--pad) 10px' }}>
            <PropRow label="Domain" value={bracket.domain} />
            <PropRow
              label="Owner"
              value={
                <RoleChip
                  roleId={bracket.governance.owner_role}
                  resolved={ownerRole ?? undefined}
                />
              }
            />
            <PropRow
              label="Steward"
              value={
                <RoleChip
                  roleId={bracket.governance.steward_role}
                  resolved={stewardRole ?? undefined}
                />
              }
            />
            <PropRow
              label="Strategic KPI"
              value={
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)' }}>
                  {bracket.orchestration.strategic_kpi_id}
                </span>
              }
            />
            <PropRow
              label="Report"
              value={bracket.ux_layout_rules.report_structure}
            />
            <PropRow
              label="Direction"
              value={bracket.value_driver_model.impact_direction}
            />
          </div>
        </div>

        {/* Open in Canvas button */}
        <button
          onClick={() => router.push('/lineage?focus=bracket:' + bracket.id)}
          style={{
            display: 'block',
            width: '100%',
            padding: '8px 0',
            border: '1px solid var(--line)',
            borderRadius: 'var(--radius)',
            background: 'transparent',
            color: 'var(--ink-3)',
            fontSize: '0.8125rem',
            fontWeight: 500,
            cursor: 'pointer',
            textAlign: 'center',
            marginBottom: 8,
          }}
        >
          Open in Canvas →
        </button>

        {/* View Decision Spine button */}
        <button
          onClick={() => setSpineOpen(true)}
          style={{
            display: 'block',
            width: '100%',
            padding: '8px 0',
            border: '1px solid var(--line)',
            borderRadius: 'var(--radius)',
            background: 'transparent',
            color: 'var(--ink-3)',
            fontSize: '0.8125rem',
            fontWeight: 500,
            cursor: 'pointer',
            textAlign: 'center',
            marginBottom: 24,
          }}
        >
          View Decision Spine →
        </button>

        {/* Studio AI card */}
        <div
          style={{
            padding: 14,
            borderRadius: 10,
            background: 'linear-gradient(180deg, var(--accent-soft), transparent)',
            border: '1px solid var(--line)',
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
            Want me to review this bracket&apos;s KPI coverage, validate the value
            driver model, or suggest missing action codes?
          </div>
          <button
            onClick={() =>
              window.dispatchEvent(new CustomEvent('studio:open-chat', {
                detail: {
                  entityContext: {
                    entityType: 'bracket' as const,
                    entityId: bracket.id,
                  },
                },
              }))
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
