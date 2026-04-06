'use client';

import { useState, useMemo } from 'react';
import type { CatalogKpi } from '@/lib/core/catalog-loader';
import { StudioDataToolbar, StudioExpandedRow, StudioInlineStat, StudioInput, StudioSelect, StudioTable, StudioTableCell, StudioTableHeadCell, StudioTableShell } from '@/components/ui/studio-data';

interface Props {
  kpis: CatalogKpi[];
}

export function KpiRegistryTable({ kpis }: Props) {
  const [filter, setFilter] = useState('');
  const [domainFilter, setDomainFilter] = useState<string>('all');
  const [expanded, setExpanded] = useState<string | null>(null);

  const domains = useMemo(
    () => [...new Set(kpis.flatMap((k) => k.domain_tag ?? []))].sort(),
    [kpis]
  );

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
      <StudioDataToolbar>
        <StudioInput
          type="text"
          placeholder="Search KPIs..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{ flex: 1 }}
        />
        <StudioSelect value={domainFilter} onChange={(e) => setDomainFilter(e.target.value)}>
          <option value="all">All Domains</option>
          {domains.map((d) => <option key={d} value={d}>{d}</option>)}
        </StudioSelect>
      </StudioDataToolbar>

      <StudioTableShell>
        <StudioTable>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--slate-700)' }}>
              {['KPI ID', 'Name', 'Type', 'Domain', 'Use Cases', 'Score'].map((h) => (
                <StudioTableHeadCell key={h}>{h}</StudioTableHeadCell>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((kpi) => (
              <KpiRow
                key={kpi.kpi_id}
                kpi={kpi}
                isExpanded={expanded === kpi.kpi_id}
                onToggle={() => setExpanded(expanded === kpi.kpi_id ? null : kpi.kpi_id)}
              />
            ))}
          </tbody>
        </StudioTable>
        {filtered.length === 0 && (
          <p style={{ padding: 'var(--sp-3)', textAlign: 'center', color: 'var(--slate-500)' }}>
            No KPIs match the filter.
          </p>
        )}
      </StudioTableShell>
      <StudioInlineStat>
        Showing {filtered.length} of {kpis.length} KPIs
      </StudioInlineStat>
    </div>
  );
}

function KpiRow({ kpi, isExpanded, onToggle }: { kpi: CatalogKpi; isExpanded: boolean; onToggle: () => void }) {
  const score = kpi.metadata_quality?.completeness_score ?? 0;
  const scoreColor = score >= 0.9 ? 'var(--mint)' : score >= 0.7 ? 'var(--gold)' : 'var(--danger)';

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
        <StudioTableCell style={{ fontFamily: 'var(--font-mono)', color: 'var(--mint)', fontSize: '0.75rem' }}>{kpi.kpi_id}</StudioTableCell>
        <StudioTableCell style={{ color: 'var(--slate-100)' }}>{kpi.kpi_key}</StudioTableCell>
        <StudioTableCell>
          <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: '9999px', fontSize: '0.6875rem', fontWeight: 500, border: `1px solid ${kpi.kpi_role === 'strategic' ? 'var(--gold)' : 'var(--slate-400)'}`, color: kpi.kpi_role === 'strategic' ? 'var(--gold)' : 'var(--slate-400)' }}>
            {kpi.kpi_type}
          </span>
        </StudioTableCell>
        <StudioTableCell style={{ color: 'var(--slate-400)' }}>{(kpi.domain_tag ?? []).join(', ')}</StudioTableCell>
        <StudioTableCell style={{ color: 'var(--slate-400)' }}>{(kpi.use_case_ref ?? []).join(', ') || '—'}</StudioTableCell>
        <StudioTableCell style={{ color: scoreColor, fontWeight: 600 }}>{(score * 100).toFixed(0)}%</StudioTableCell>
      </tr>
      {isExpanded && (
        <StudioExpandedRow colSpan={6}>
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
                <DetailText mono>{(kpi.technical?.depends_on_measures ?? []).join(', ') || '—'}</DetailText>
                <DetailLabel>Owner</DetailLabel>
                <DetailText>{kpi.governance?.business_owner}</DetailText>
              </div>
            </div>
        </StudioExpandedRow>
      )}
    </>
  );
}

function DetailLabel({ children }: { children: React.ReactNode }) {
  return <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', marginBottom: '2px', marginTop: 'var(--sp-1)' }}>{children}</p>;
}

function DetailText({ children, mono }: { children: React.ReactNode; mono?: boolean }) {
  return <p style={{ fontSize: '0.8125rem', color: 'var(--slate-200)', fontFamily: mono ? 'var(--font-mono)' : undefined }}>{children}</p>;
}
