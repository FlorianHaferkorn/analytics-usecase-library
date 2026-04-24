'use client';

import { useMemo } from 'react';
import { useRouter } from 'next/navigation';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import type { FactsheetSummary } from '@/lib/core/factsheet-loader';
import { card, cardHead } from '@/components/registry/kpi-detail-tabs';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Props {
  bracket: UseCaseBracketV20Lean;
  factsheet: FactsheetSummary | null;
}

type KpiRole = 'Strategic' | 'Influencing' | 'Supporting';

interface KpiRow {
  id: string;
  role: KpiRole;
}

// ─── Role Pill ────────────────────────────────────────────────────────────────

const ROLE_STYLES: Record<KpiRole, { bg: string; fg: string }> = {
  Strategic: { bg: 'var(--accent-soft)', fg: 'var(--accent)' },
  Influencing: { bg: 'var(--hover)', fg: 'var(--ink-2)' },
  Supporting: { bg: 'var(--line)', fg: 'var(--ink-4)' },
};

function RolePill({ role }: { role: KpiRole }) {
  const s = ROLE_STYLES[role];
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
        whiteSpace: 'nowrap',
      }}
    >
      {role}
    </span>
  );
}

// ─── Table styles ─────────────────────────────────────────────────────────────

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

const tdBase: React.CSSProperties = {
  padding: '12px var(--pad)',
  borderBottom: '1px solid var(--line-2)',
  fontSize: '0.8125rem',
  verticalAlign: 'middle',
};

// ─── BracketKpisTab ───────────────────────────────────────────────────────────

export function BracketKpisTab({ bracket, factsheet }: Props) {
  const router = useRouter();

  const rows = useMemo<KpiRow[]>(() => {
    const { strategic_kpi_id, influencing_kpi_ids, supporting_kpi_ids } =
      bracket.orchestration;

    return [
      { id: strategic_kpi_id, role: 'Strategic' as KpiRole },
      ...influencing_kpi_ids.map((id) => ({ id, role: 'Influencing' as KpiRole })),
      ...(supporting_kpi_ids ?? []).map((id) => ({ id, role: 'Supporting' as KpiRole })),
    ];
  }, [bracket.orchestration]);

  function getKpiPurpose(kpiId: string): string {
    if (!factsheet) return '';
    const entry = factsheet.kpi_roles.find((k) => k.kpi_id === kpiId);
    return entry?.role ?? '';
  }

  return (
    <div style={card}>
      <div style={cardHead}>
        <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
          KPI References
        </span>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.625rem',
            color: 'var(--ink-4)',
            background: 'var(--line-2)',
            padding: '1px 5px',
            borderRadius: 4,
          }}
        >
          {rows.length}
        </span>
      </div>

      <table
        style={{ width: '100%', borderCollapse: 'collapse' }}
        role="table"
        aria-label="KPI references"
      >
        <thead>
          <tr>
            <th style={thStyle}>KPI ID</th>
            <th style={thStyle}>Role</th>
            <th style={thStyle}>Use Case Purpose</th>
            <th style={{ ...thStyle, textAlign: 'right' }}>Link</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const purpose = getKpiPurpose(row.id);

            return (
              <tr
                key={row.id}
                onClick={() => router.push(`/catalog/${row.id}`)}
                style={{ cursor: 'pointer' }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLTableRowElement).style.background =
                    'var(--hover)';
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLTableRowElement).style.background =
                    'transparent';
                }}
              >
                {/* KPI ID */}
                <td
                  style={{
                    ...tdBase,
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.75rem',
                    color: 'var(--ink-3)',
                  }}
                >
                  {row.id}
                </td>

                {/* Role */}
                <td style={tdBase}>
                  <RolePill role={row.role} />
                </td>

                {/* Use Case Purpose (from factsheet kpi_roles) */}
                <td style={{ ...tdBase, color: 'var(--ink-3)' }}>
                  {purpose || (
                    <span style={{ color: 'var(--ink-4)', fontStyle: 'italic' }}>—</span>
                  )}
                </td>

                {/* Link */}
                <td style={{ ...tdBase, textAlign: 'right' }}>
                  <span
                    style={{
                      color: 'var(--accent)',
                      fontSize: '0.8125rem',
                      fontWeight: 500,
                    }}
                  >
                    View →
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {rows.length === 0 && (
        <p
          style={{
            margin: 0,
            padding: 'var(--pad)',
            textAlign: 'center',
            color: 'var(--ink-4)',
            fontSize: '0.8125rem',
          }}
        >
          No KPIs referenced in this bracket.
        </p>
      )}
    </div>
  );
}
