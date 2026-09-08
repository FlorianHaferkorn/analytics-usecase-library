'use client';

import { useMemo, useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import type { GoldenThreadData } from '@/components/flow/golden-thread-flow';
import { matchesDomainFilter } from '@/lib/studio/domain-filter';
import { StudioPanel, StudioSegmentedControl } from '@/components/ui/studio-page';

const GoldenThreadFlow = dynamic(
  () => import('@/components/flow/golden-thread-flow').then((m) => m.GoldenThreadFlow),
  { ssr: false, loading: () => <div style={{ padding: 'var(--pad)', color: 'var(--ink-4)' }}>Loading flow…</div> },
);

// ─── Types ────────────────────────────────────────────────────────────────────

interface BracketEntry {
  id: string;
  title: string;
  domain: string;
  strategicKpiId: string;
  impactDirection: string;
  influencingKpiIds: string[];
  actionCodeIds: string[];
}

interface Props {
  strategyAnchor: string;
  brackets: BracketEntry[];
  actionDetails: Array<[string, { name: string; status: string; domain: string; triggerKpis: string[] }]>;
  kpiNames: Record<string, string>;
  actionNames: Record<string, string>;
  domains: string[];
  activeDomainFilter?: string | null;
}

type ViewMode = 'flow' | 'list';

// ─── Badge helper ─────────────────────────────────────────────────────────────

function Badge({
  label,
  bg,
  color,
}: {
  label: string;
  bg: string;
  color: string;
}) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 20,
        height: 20,
        flexShrink: 0,
        borderRadius: 999,
        background: bg,
        color,
        fontSize: 'var(--text-2xs)',
        fontWeight: 600,
      }}
    >
      {label}
    </span>
  );
}

function DomainChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        padding: '3px 10px',
        borderRadius: 999,
        border: active ? '1px solid var(--accent)' : '1px solid var(--line)',
        background: active ? 'var(--accent-soft)' : 'transparent',
        color: active ? 'var(--accent)' : 'var(--ink-3)',
        fontSize: 12,
        cursor: 'pointer',
        fontWeight: active ? 500 : 400,
        transition: 'all 150ms',
      }}
    >
      {label}
    </button>
  );
}

function BracketNode({
  bracket,
  kpiNames,
  actionNames,
  expanded,
  onToggle,
}: {
  bracket: BracketEntry;
  kpiNames: Record<string, string>;
  actionNames: Record<string, string>;
  expanded: boolean;
  onToggle: () => void;
}) {
  const router = useRouter();

  return (
    <div
      style={{
        borderRadius: 8,
        border: '1px solid var(--line)',
        background: 'var(--panel)',
        overflow: 'hidden',
      }}
    >
      <div
        onClick={onToggle}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '10px 12px',
          cursor: 'pointer',
        }}
      >
        <span
          style={{
            fontSize: 'var(--text-2xs)',
            color: 'var(--ink-4)',
            display: 'inline-block',
            transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
            transition: 'transform 200ms',
            width: 12,
            flexShrink: 0,
          }}
        >
          ▶
        </span>
        <Badge label="B" bg="var(--accent-soft)" color="var(--accent)" />
        <span
          onClick={(e) => {
            e.stopPropagation();
            router.push('/brackets/' + bracket.id);
          }}
          style={{ fontSize: 14, color: 'var(--ink)', fontWeight: 500, flex: 1, cursor: 'pointer' }}
        >
          {bracket.title}
        </span>
        <span
          style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--ink-3)',
            padding: '1px 6px',
            borderRadius: 999,
            border: '1px solid var(--line)',
            flexShrink: 0,
          }}
        >
          {bracket.domain}
        </span>
      </div>

      {expanded && (
        <div style={{ borderTop: '1px solid var(--line)', paddingBottom: 4 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px 8px 40px' }}>
            <Badge label="K" bg="oklch(0.22 0.04 250 / 0.4)" color="oklch(0.65 0.12 250)" />
            <span
              onClick={() => router.push('/catalog/' + bracket.strategicKpiId)}
              style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent)', cursor: 'pointer' }}
            >
              {bracket.strategicKpiId}
            </span>
            {kpiNames[bracket.strategicKpiId] && (
              <span style={{ fontSize: 12, color: 'var(--ink-3)' }}>{kpiNames[bracket.strategicKpiId]}</span>
            )}
          </div>
          {bracket.actionCodeIds.map((aid) => (
            <div key={aid} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px 6px 56px' }}>
              <Badge label="A" bg="oklch(0.22 0.05 75 / 0.3)" color="oklch(0.75 0.15 75)" />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>{aid}</span>
              {actionNames[aid] && <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-4)' }}>{actionNames[aid]}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── GoldenThreadTab ──────────────────────────────────────────────────────────

export function GoldenThreadTab({
  strategyAnchor,
  brackets,
  actionDetails,
  kpiNames,
  actionNames,
  domains,
  activeDomainFilter = null,
}: Props) {
  const [viewMode, setViewMode] = useState<ViewMode>('flow');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [activeDomain, setActiveDomain] = useState<string>(activeDomainFilter ?? 'All');

  useEffect(() => {
    setActiveDomain(activeDomainFilter ?? 'All');
  }, [activeDomainFilter]);

  const filteredBrackets =
    activeDomain === 'All'
      ? brackets
      : brackets.filter((b) => matchesDomainFilter(b.domain, activeDomain));

  const flowData = useMemo<GoldenThreadData>(() => ({
    strategyAnchor,
    brackets: filteredBrackets,
    actionDetails: new Map(actionDetails),
    kpiNames,
  }), [strategyAnchor, filteredBrackets, actionDetails, kpiNames]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--gap)',
          padding: '12px var(--pad)',
          borderBottom: '1px solid var(--line)',
          flexShrink: 0,
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', gap: 6, flex: 1, flexWrap: 'wrap', alignItems: 'center' }}>
          <DomainChip label="All" active={activeDomain === 'All'} onClick={() => setActiveDomain('All')} />
          {domains.map((d) => (
            <DomainChip key={d} label={d} active={activeDomain === d} onClick={() => setActiveDomain(d)} />
          ))}
        </div>
        <StudioSegmentedControl
          value={viewMode}
          onChange={setViewMode}
          options={[
            { value: 'flow', label: 'Flow map' },
            { value: 'list', label: 'Use-case list' },
          ]}
        />
      </div>

      {viewMode === 'flow' ? (
        <div style={{ flex: 1, minHeight: 560, display: 'flex', flexDirection: 'column', padding: 'var(--gap) var(--pad) var(--pad)' }}>
          <StudioPanel title="Golden Thread" compactHeader bare style={{ flex: 1, minHeight: 520, overflow: 'hidden' }}>
            <div style={{ flex: 1, minHeight: 480, display: 'flex', flexDirection: 'column' }}>
              <GoldenThreadFlow data={flowData} />
            </div>
          </StudioPanel>
        </div>
      ) : (
        <div style={{ flex: 1, overflow: 'auto', padding: 'var(--pad)' }}>
          <div style={{ maxWidth: 800, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <p style={{ fontSize: 13, color: 'var(--ink-3)', marginBottom: 8, lineHeight: 1.6 }}>
              {filteredBrackets.length} use case{filteredBrackets.length !== 1 ? 's' : ''} — strategic intent → KPIs → actions
            </p>
            {filteredBrackets.map((bracket) => (
              <BracketNode
                key={bracket.id}
                bracket={bracket}
                kpiNames={kpiNames}
                actionNames={actionNames}
                expanded={expanded.has(bracket.id)}
                onToggle={() => {
                  setExpanded((prev) => {
                    const next = new Set(prev);
                    if (next.has(bracket.id)) next.delete(bracket.id);
                    else next.add(bracket.id);
                    return next;
                  });
                }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
