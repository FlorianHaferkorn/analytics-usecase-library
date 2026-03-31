'use client';

import { useState } from 'react';
import type { DataContract } from '@/lib/schemas';

interface Props {
  contracts: DataContract[];
}

function ContractCard({ contract }: { contract: DataContract }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      style={{
        backgroundColor: 'var(--slate-800)',
        border: `1px solid ${expanded ? 'var(--info)' : 'var(--slate-700)'}`,
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
      }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          padding: 'var(--sp-1-5) var(--sp-2)',
          backgroundColor: 'transparent',
          border: 'none',
          cursor: 'pointer',
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
      </button>

      {expanded && (
        <div style={{ padding: '0 var(--sp-2) var(--sp-2)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {/* Dimensions */}
          {(contract.dimension ?? []).map((dim) => (
            <div key={dim.name}>
              <p style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--slate-300)', marginBottom: '4px' }}>
                {dim.name} (dimension)
              </p>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.6875rem' }}>
                <thead>
                  <tr>
                    {['Column', 'Type', 'Role', 'Ref'].map((h) => (
                      <th key={h} style={{ textAlign: 'left', padding: '2px 8px', color: 'var(--slate-500)', borderBottom: '1px solid var(--slate-700)' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dim.columns.map((col) => (
                    <tr key={col.name}>
                      <td style={{ padding: '2px 8px', color: 'var(--slate-200)', fontFamily: 'monospace' }}>{col.name}</td>
                      <td style={{ padding: '2px 8px', color: 'var(--slate-400)' }}>{col.type}</td>
                      <td style={{ padding: '2px 8px', color: col.role === 'key' ? 'var(--gold)' : 'var(--slate-400)' }}>{col.role ?? '—'}</td>
                      <td style={{ padding: '2px 8px', color: 'var(--info)', fontFamily: 'monospace' }}>{col.ref ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}

          {/* Facts */}
          {(contract.fact ?? []).map((fact) => (
            <div key={fact.name}>
              <p style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--slate-300)', marginBottom: '4px' }}>
                {fact.name} (fact &middot; grain: {fact.grain})
              </p>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.6875rem' }}>
                <thead>
                  <tr>
                    {['Column', 'Type', 'Agg', 'Ref'].map((h) => (
                      <th key={h} style={{ textAlign: 'left', padding: '2px 8px', color: 'var(--slate-500)', borderBottom: '1px solid var(--slate-700)' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {fact.columns.map((col) => (
                    <tr key={col.name}>
                      <td style={{ padding: '2px 8px', color: 'var(--slate-200)', fontFamily: 'monospace' }}>{col.name}</td>
                      <td style={{ padding: '2px 8px', color: 'var(--slate-400)' }}>{col.type}</td>
                      <td style={{ padding: '2px 8px', color: col.agg ? 'var(--mint)' : 'var(--slate-400)' }}>{col.agg ?? '—'}</td>
                      <td style={{ padding: '2px 8px', color: 'var(--info)', fontFamily: 'monospace' }}>{col.ref ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
    </div>
  );
}

export function ContractDetailList({ contracts }: Props) {
  if (contracts.length === 0) {
    return <p style={{ fontSize: '0.8125rem', color: 'var(--slate-500)' }}>No data contracts found.</p>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
      {contracts.map((c) => (
        <ContractCard key={c.domain} contract={c} />
      ))}
    </div>
  );
}
