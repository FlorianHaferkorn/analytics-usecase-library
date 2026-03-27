'use client';

import { useState } from 'react';
import type { CatalogKpi } from '@/lib/core/catalog-loader';

interface Props {
  kpis: CatalogKpi[];
}

export function KpiRegistryTable({ kpis }: Props) {
  const [filter, setFilter] = useState('');
  const [domainFilter, setDomainFilter] = useState<string>('all');
  const [expanded, setExpanded] = useState<string | null>(null);

  const domains = [...new Set(kpis.flatMap((k) => k.domain_tag ?? []))].sort();

  const filtered = kpis.filter((kpi) => {
    const matchesText =
      !filter ||
      kpi.kpi_id.toLowerCase().includes(filter.toLowerCase()) ||
      kpi.kpi_key.toLowerCase().includes(filter.toLowerCase()) ||
      kpi.business?.purpose?.toLowerCase().includes(filter.toLowerCase());
    const matchesDomain =
      domainFilter === 'all' || (kpi.domain_tag ?? []).includes(domainFilter);
    return matchesText && matchesDomain;
  });

  return (
    <div>
      <div style={{ display: 'flex', gap: 'var(--sp-1)', marginBottom: 'var(--sp-2)' }}>
        <input
          type="text"
          placeholder="Search KPIs..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{
            flex: 1,
            padding: 'var(--sp-1) var(--sp-1-5)',
            backgroundColor: 'var(--slate-800)',
            border: '1px solid var(--slate-700)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--slate-100)',
            fontSize: '0.875rem',
            outline: 'none',
          }}
        />
        <select
          value={domainFilter}
          onChange={(e) => setDomainFilter(e.target.value)}
          style={{
            padding: 'var(--sp-1) var(--sp-1-5)',
            backgroundColor: 'var(--slate-800)',
            border: '1px solid var(--slate-700)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--slate-100)',
            fontSize: '0.875rem',
          }}
        >
          <option value="all">All Domains</option>
          {domains.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      <div
        style={{
          backgroundColor: 'var(--slate-800)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--slate-700)',
          overflow: 'hidden',
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--slate-700)' }}>
              {['KPI ID', 'Name', 'Type', 'Domain', 'Use Cases', 'Score'].map((h) => (
                <th
                  key={h}
                  style={{
                    padding: 'var(--sp-1) var(--sp-1-5)',
                    textAlign: 'left',
                    color: 'var(--slate-400)',
                    fontWeight: 500,
                    fontSize: '0.75rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((kpi) => (
              <KpiRow
                key={kpi.kpi_id}
                kpi={kpi}
                isExpanded={expanded === kpi.kpi_id}
                onToggle={() =>
                  setExpanded(expanded === kpi.kpi_id ? null : kpi.kpi_id)
                }
              />
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p style={{ padding: 'var(--sp-3)', textAlign: 'center', color: 'var(--slate-500)' }}>
            No KPIs match the filter.
          </p>
        )}
      </div>
      <p style={{ marginTop: 'var(--sp-1)', fontSize: '0.75rem', color: 'var(--slate-500)' }}>
        Showing {filtered.length} of {kpis.length} KPIs
      </p>
    </div>
  );
}

function KpiRow({
  kpi,
  isExpanded,
  onToggle,
}: {
  kpi: CatalogKpi;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const score = kpi.metadata_quality?.completeness_score ?? 0;
  const scoreColor =
    score >= 0.9 ? 'var(--mint)' : score >= 0.7 ? 'var(--gold)' : 'var(--danger)';

  return (
    <>
      <tr
        onClick={onToggle}
        style={{
          borderBottom: '1px solid var(--slate-700)',
          cursor: 'pointer',
          backgroundColor: isExpanded ? 'var(--slate-750, #283548)' : 'transparent',
          transition: 'background-color var(--duration-fast) var(--ease-out)',
        }}
      >
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', fontFamily: 'var(--font-mono)', color: 'var(--mint)', fontSize: '0.75rem' }}>
          {kpi.kpi_id}
        </td>
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', color: 'var(--slate-100)' }}>
          {kpi.kpi_key}
        </td>
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)' }}>
          <TypeBadge type={kpi.kpi_type} role={kpi.kpi_role} />
        </td>
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', color: 'var(--slate-400)' }}>
          {(kpi.domain_tag ?? []).join(', ')}
        </td>
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', color: 'var(--slate-400)' }}>
          {(kpi.use_case_ref ?? []).join(', ') || '—'}
        </td>
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', color: scoreColor, fontWeight: 600 }}>
          {(score * 100).toFixed(0)}%
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={6} style={{ padding: 'var(--sp-2) var(--sp-1-5)', backgroundColor: 'var(--slate-850, #182030)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-2)' }}>
              <div>
                <DetailLabel>Purpose</DetailLabel>
                <DetailText>{kpi.business?.purpose}</DetailText>
                <DetailLabel>Definition</DetailLabel>
                <DetailText>{kpi.business?.definition}</DetailText>
                <DetailLabel>Grain</DetailLabel>
                <DetailText>{kpi.business?.grain_scope}</DetailText>
              </div>
              <div>
                <DetailLabel>DAX Name</DetailLabel>
                <DetailText mono>{kpi.technical?.dax_name}</DetailText>
                <DetailLabel>Depends On</DetailLabel>
                <DetailText mono>
                  {(kpi.technical?.depends_on_measures ?? []).join(', ') || '—'}
                </DetailText>
                <DetailLabel>Owner</DetailLabel>
                <DetailText>{kpi.governance?.business_owner}</DetailText>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function TypeBadge({ type, role }: { type: string; role: string }) {
  const color = role === 'strategic' ? 'var(--gold)' : 'var(--slate-400)';
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: '9999px',
        fontSize: '0.6875rem',
        fontWeight: 500,
        border: `1px solid ${color}`,
        color,
      }}
    >
      {type}
    </span>
  );
}

function DetailLabel({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', marginBottom: '2px', marginTop: 'var(--sp-1)' }}>
      {children}
    </p>
  );
}

function DetailText({ children, mono }: { children: React.ReactNode; mono?: boolean }) {
  return (
    <p
      style={{
        fontSize: '0.8125rem',
        color: 'var(--slate-200)',
        fontFamily: mono ? 'var(--font-mono)' : undefined,
      }}
    >
      {children}
    </p>
  );
}
