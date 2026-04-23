'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

// ─── Types ────────────────────────────────────────────────────────────────────

interface BracketEntry {
  id: string;
  title: string;
  domain: string;
  strategicKpiId: string;
  actionCodeIds: string[];
}

interface Props {
  brackets: BracketEntry[];
  kpiNames: Record<string, string>;
  actionNames: Record<string, string>;
  domains: string[];
}

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
        fontSize: 10,
        fontWeight: 600,
      }}
    >
      {label}
    </span>
  );
}

// ─── KPI row ──────────────────────────────────────────────────────────────────

function KpiRow({
  kpiId,
  kpiName,
}: {
  kpiId: string;
  kpiName: string | undefined;
}) {
  const router = useRouter();
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '8px 12px 8px 40px',
      }}
    >
      <Badge
        label="K"
        bg="oklch(0.22 0.04 250 / 0.4)"
        color="oklch(0.65 0.12 250)"
      />
      <span
        onClick={() => router.push('/catalog/' + kpiId)}
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          color: 'var(--accent)',
          cursor: 'pointer',
        }}
      >
        {kpiId}
      </span>
      {kpiName && (
        <span style={{ fontSize: 12, color: 'var(--ink-3)' }}>{kpiName}</span>
      )}
    </div>
  );
}

// ─── Action row ───────────────────────────────────────────────────────────────

function ActionRow({
  actionId,
  actionName,
}: {
  actionId: string;
  actionName: string | undefined;
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '6px 12px 6px 56px',
      }}
    >
      <Badge
        label="A"
        bg="oklch(0.22 0.05 75 / 0.3)"
        color="oklch(0.75 0.15 75)"
      />
      <span
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--ink-3)',
        }}
      >
        {actionId}
      </span>
      {actionName && (
        <span style={{ fontSize: 11, color: 'var(--ink-4)' }}>{actionName}</span>
      )}
    </div>
  );
}

// ─── Bracket tree node ────────────────────────────────────────────────────────

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
      {/* Bracket header row */}
      <div
        onClick={onToggle}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '10px 12px',
          cursor: 'pointer',
          borderRadius: expanded ? '8px 8px 0 0' : 8,
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLDivElement).style.background = 'var(--hover)';
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLDivElement).style.background = 'transparent';
        }}
      >
        {/* Chevron */}
        <span
          style={{
            fontSize: 10,
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

        {/* [B] badge */}
        <Badge
          label="B"
          bg="var(--accent-soft)"
          color="var(--accent)"
        />

        {/* Title */}
        <span
          onClick={(e) => {
            e.stopPropagation();
            router.push('/brackets/' + bracket.id);
          }}
          style={{
            fontSize: 14,
            color: 'var(--ink)',
            fontWeight: 500,
            flex: 1,
            cursor: 'pointer',
          }}
        >
          {bracket.title}
        </span>

        {/* Domain pill */}
        <span
          style={{
            fontSize: 11,
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

      {/* Expanded children */}
      {expanded && (
        <div
          style={{
            borderTop: '1px solid var(--line)',
            paddingBottom: 4,
          }}
        >
          {/* Strategic KPI */}
          <KpiRow
            kpiId={bracket.strategicKpiId}
            kpiName={kpiNames[bracket.strategicKpiId]}
          />

          {/* Actions under this bracket */}
          {bracket.actionCodeIds.map((aid) => (
            <ActionRow
              key={aid}
              actionId={aid}
              actionName={actionNames[aid]}
            />
          ))}

          {bracket.actionCodeIds.length === 0 && (
            <div
              style={{
                padding: '6px 12px 6px 56px',
                fontSize: 11,
                color: 'var(--ink-4)',
              }}
            >
              No actions linked
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Domain chip ──────────────────────────────────────────────────────────────

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

// ─── GoldenThreadTab ──────────────────────────────────────────────────────────

export function GoldenThreadTab({
  brackets,
  kpiNames,
  actionNames,
  domains,
}: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [activeDomain, setActiveDomain] = useState<string>('All');

  const filteredBrackets =
    activeDomain === 'All'
      ? brackets
      : brackets.filter((b) => b.domain === activeDomain);

  function toggleBracket(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function expandAll() {
    setExpanded(new Set(filteredBrackets.map((b) => b.id)));
  }

  function collapseAll() {
    setExpanded(new Set());
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {/* Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '12px var(--pad)',
          borderBottom: '1px solid var(--line)',
          flexShrink: 0,
          flexWrap: 'wrap',
        }}
      >
        {/* Domain filters */}
        <div style={{ display: 'flex', gap: 6, flex: 1, flexWrap: 'wrap' }}>
          <DomainChip
            label="All"
            active={activeDomain === 'All'}
            onClick={() => setActiveDomain('All')}
          />
          {domains.map((d) => (
            <DomainChip
              key={d}
              label={d}
              active={activeDomain === d}
              onClick={() => setActiveDomain(d)}
            />
          ))}
        </div>

        {/* Expand / Collapse all */}
        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
          <button
            onClick={expandAll}
            style={{
              padding: '3px 10px',
              border: '1px solid var(--line)',
              borderRadius: 6,
              background: 'transparent',
              color: 'var(--ink-3)',
              fontSize: 12,
              cursor: 'pointer',
            }}
          >
            Expand all
          </button>
          <button
            onClick={collapseAll}
            style={{
              padding: '3px 10px',
              border: '1px solid var(--line)',
              borderRadius: 6,
              background: 'transparent',
              color: 'var(--ink-3)',
              fontSize: 12,
              cursor: 'pointer',
            }}
          >
            Collapse all
          </button>
        </div>
      </div>

      {/* Tree list */}
      <div style={{ flex: 1, overflow: 'auto', padding: 'var(--pad)' }}>
        {filteredBrackets.length === 0 ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: 200,
              color: 'var(--ink-4)',
              fontSize: 13,
              gap: 8,
            }}
          >
            <span style={{ fontSize: 24 }}>⬡</span>
            <span>No use cases for this domain</span>
          </div>
        ) : (
          <div
            style={{
              maxWidth: 800,
              margin: '0 auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}
          >
            {/* Header */}
            <p
              style={{
                fontSize: 13,
                color: 'var(--ink-3)',
                marginBottom: 8,
                lineHeight: 1.6,
              }}
            >
              {filteredBrackets.length} use case
              {filteredBrackets.length !== 1 ? 's' : ''} — strategic intent →
              KPIs → actions
            </p>

            {filteredBrackets.map((bracket) => (
              <BracketNode
                key={bracket.id}
                bracket={bracket}
                kpiNames={kpiNames}
                actionNames={actionNames}
                expanded={expanded.has(bracket.id)}
                onToggle={() => toggleBracket(bracket.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
