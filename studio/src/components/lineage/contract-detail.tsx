'use client';

import { useState } from 'react';
import type { DataContract } from '@/lib/schemas';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import { StudioTable, StudioTableCell, StudioTableHeadCell, StudioTableShell } from '@/components/ui/studio-data';

interface Props {
  contracts: DataContract[];
}

function ContractCard({ contract }: { contract: DataContract }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <StudioPanel tone={expanded ? 'info' : 'default'} style={{ padding: 0, overflow: 'hidden', border: `1px solid ${expanded ? 'var(--info)' : 'var(--slate-700)'}` }}>
      <StudioButton
        onClick={() => setExpanded(!expanded)}
        variant="ghost"
        style={{
          width: '100%',
          padding: 'var(--sp-1-5) var(--sp-2)',
          backgroundColor: 'transparent',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          textAlign: 'left',
        }}
      >
        <div>
          <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--slate-100)' }}>
            {contract.domain}
          </p>
          <p style={{ fontSize: '0.6875rem', color: 'var(--slate-400)' }}>
            v{contract.version} &middot; {contract.owner}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--sp-1)', alignItems: 'center' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>
            {contract.dimension?.length ?? 0} dims &middot; {contract.fact?.length ?? 0} facts
          </span>
          <span style={{ color: 'var(--slate-500)', transform: expanded ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform var(--duration-fast)' }}>
            &#x25BC;
          </span>
        </div>
      </StudioButton>

      {expanded && (
        <div style={{ padding: '0 var(--sp-2) var(--sp-2)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {/* Dimensions */}
          {(contract.dimension ?? []).map((dim) => (
            <div key={dim.name}>
              <p style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--slate-300)', marginBottom: '4px' }}>
                {dim.name} (dimension)
              </p>
              <StudioTableShell>
              <StudioTable>
                <colgroup>
                  <col style={{ width: '40%' }} />
                  <col style={{ width: '18%' }} />
                  <col style={{ width: '22%' }} />
                  <col style={{ width: '20%' }} />
                </colgroup>
                <thead>
                  <tr>
                    {['Column', 'Type', 'Role', 'Ref'].map((h) => (
                      <StudioTableHeadCell key={h} style={{ padding: '2px 8px', fontSize: '0.6875rem' }}>{h}</StudioTableHeadCell>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dim.columns.map((col) => (
                    <tr key={col.name}>
                      <StudioTableCell style={{ padding: '2px 8px', color: 'var(--slate-200)', fontFamily: 'monospace' }}>{col.name}</StudioTableCell>
                      <StudioTableCell style={{ padding: '2px 8px', color: 'var(--slate-400)' }}>{col.type}</StudioTableCell>
                      <StudioTableCell style={{ padding: '2px 8px', color: col.role === 'key' ? 'var(--gold)' : 'var(--slate-400)' }}>{col.role ?? '—'}</StudioTableCell>
                      <StudioTableCell style={{ padding: '2px 8px', color: 'var(--info)', fontFamily: 'monospace' }}>{col.ref ?? '—'}</StudioTableCell>
                    </tr>
                  ))}
                </tbody>
              </StudioTable>
              </StudioTableShell>
            </div>
          ))}

          {/* Facts */}
          {(contract.fact ?? []).map((fact) => (
            <div key={fact.name}>
              <p style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--slate-300)', marginBottom: '4px' }}>
                {fact.name} (fact &middot; grain: {fact.grain})
              </p>
              <StudioTableShell>
              <StudioTable>
                <colgroup>
                  <col style={{ width: '40%' }} />
                  <col style={{ width: '18%' }} />
                  <col style={{ width: '22%' }} />
                  <col style={{ width: '20%' }} />
                </colgroup>
                <thead>
                  <tr>
                    {['Column', 'Type', 'Agg', 'Ref'].map((h) => (
                      <StudioTableHeadCell key={h} style={{ padding: '2px 8px', fontSize: '0.6875rem' }}>{h}</StudioTableHeadCell>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {fact.columns.map((col) => (
                    <tr key={col.name}>
                      <StudioTableCell style={{ padding: '2px 8px', color: 'var(--slate-200)', fontFamily: 'monospace' }}>{col.name}</StudioTableCell>
                      <StudioTableCell style={{ padding: '2px 8px', color: 'var(--slate-400)' }}>{col.type}</StudioTableCell>
                      <StudioTableCell style={{ padding: '2px 8px', color: col.agg ? 'var(--mint)' : 'var(--slate-400)' }}>{col.agg ?? '—'}</StudioTableCell>
                      <StudioTableCell style={{ padding: '2px 8px', color: 'var(--info)', fontFamily: 'monospace' }}>{col.ref ?? '—'}</StudioTableCell>
                    </tr>
                  ))}
                </tbody>
              </StudioTable>
              </StudioTableShell>
            </div>
          ))}

          {/* Settings */}
          {contract.settings && (
            <div style={{ fontSize: '0.6875rem', color: 'var(--slate-400)' }}>
              {contract.settings.currency && <span>Currency: {contract.settings.currency} &middot; </span>}
              {contract.settings.time_zone && <span>TZ: {contract.settings.time_zone} &middot; </span>}
              {contract.settings.naming && <span>Naming: {contract.settings.naming}</span>}
            </div>
          )}
        </div>
      )}
    </StudioPanel>
  );
}

export function ContractDetailList({ contracts }: Props) {
  if (contracts.length === 0) {
    return <StudioEmptyState title="No data contracts found" description="Lineage has no contract metadata to render for the current context." />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
      {contracts.map((c) => (
        <ContractCard key={c.domain} contract={c} />
      ))}
    </div>
  );
}
