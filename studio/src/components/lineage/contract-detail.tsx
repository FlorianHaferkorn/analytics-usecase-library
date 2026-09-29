'use client';

import { useState } from 'react';
import type { ResolvedContract } from '@/lib/core/contract-loader';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import { StudioTable, StudioTableCell, StudioTableHeadCell, StudioTableShell } from '@/components/ui/studio-data';

interface Props {
  contracts: ResolvedContract[];
}

function ContractCard({ contract }: { contract: ResolvedContract }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <StudioPanel tone={expanded ? 'info' : 'default'} style={{ padding: 0, overflow: 'hidden', border: `1px solid ${expanded ? 'var(--info)' : 'var(--line)'}` }}>
      <StudioButton
        onClick={() => setExpanded(!expanded)}
        variant="ghost"
        style={{
          width: '100%',
          padding: '12px 16px',
          backgroundColor: 'transparent',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          textAlign: 'left',
        }}
      >
        <div>
          <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--ink)' }}>
            {contract.domain}
          </p>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>
            v{contract.version} &middot; {contract.owner}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-4)' }}>
            {contract.dimension?.length ?? 0} dims &middot; {contract.fact?.length ?? 0} facts
          </span>
          <span style={{ color: 'var(--ink-4)', transform: expanded ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform var(--duration-fast)' }}>
            &#x25BC;
          </span>
        </div>
      </StudioButton>

      {expanded && (
        <div style={{ padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Dimensions */}
          {(contract.dimension ?? []).map((dim) => (
            <div key={dim.name}>
              <p style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--ink-2)', marginBottom: '4px' }}>
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
                      <StudioTableHeadCell key={h} style={{ padding: '2px 8px', fontSize: 'var(--text-xs)' }}>{h}</StudioTableHeadCell>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dim.columns.map((col) => (
                    <tr key={col.name}>
                      <StudioTableCell style={{ padding: '2px 8px', color: 'var(--ink-2)', fontFamily: 'monospace' }}>{col.name}</StudioTableCell>
                      <StudioTableCell style={{ padding: '2px 8px', color: 'var(--ink-3)' }}>{col.type}</StudioTableCell>
                      <StudioTableCell style={{ padding: '2px 8px', color: col.role === 'key' ? 'var(--warning)' : 'var(--ink-3)' }}>{col.role ?? '—'}</StudioTableCell>
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
              <p style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--ink-2)', marginBottom: '4px' }}>
                {fact.name} (fact &middot; grain: {fact.grain ?? '—'})
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
                      <StudioTableHeadCell key={h} style={{ padding: '2px 8px', fontSize: 'var(--text-xs)' }}>{h}</StudioTableHeadCell>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {fact.columns.map((col) => (
                    <tr key={col.name}>
                      <StudioTableCell style={{ padding: '2px 8px', color: 'var(--ink-2)', fontFamily: 'monospace' }}>{col.name}</StudioTableCell>
                      <StudioTableCell style={{ padding: '2px 8px', color: 'var(--ink-3)' }}>{col.type}</StudioTableCell>
                      <StudioTableCell style={{ padding: '2px 8px', color: col.agg ? 'var(--accent)' : 'var(--ink-3)' }}>{col.agg ?? '—'}</StudioTableCell>
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
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>
              {contract.settings.currency && <span>Currency: {contract.settings.currency} &middot; </span>}
              {contract.settings.timezone && <span>TZ: {contract.settings.timezone} &middot; </span>}
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {contracts.map((c) => (
        <ContractCard key={c.domain} contract={c} />
      ))}
    </div>
  );
}
