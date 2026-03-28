'use client';

import { useState } from 'react';
import type { ActionCodeDefinitionV20AIMirror } from '@/lib/schemas';
import { tableContainerStyle, tableStyle, thStyle, tdStyle, expandedRowStyle, filterInputStyle, filterSelectStyle, getStatusColor } from '@/lib/ui-styles';

interface Props {
  actions: ActionCodeDefinitionV20AIMirror[];
}

export function ActionRegistryTable({ actions }: Props) {
  const [filter, setFilter] = useState('');
  const [domainFilter, setDomainFilter] = useState<string>('all');
  const [expanded, setExpanded] = useState<string | null>(null);

  const domains = [...new Set(actions.map((a) => a.owner_domain))].sort();

  const filtered = actions.filter((action) => {
    const matchesText =
      !filter ||
      action.id.toLowerCase().includes(filter.toLowerCase()) ||
      action.name.toLowerCase().includes(filter.toLowerCase());
    const matchesDomain =
      domainFilter === 'all' || action.owner_domain === domainFilter;
    return matchesText && matchesDomain;
  });

  return (
    <div>
      <div style={{ display: 'flex', gap: 'var(--sp-1)', marginBottom: 'var(--sp-2)' }}>
        <input
          type="text"
          placeholder="Search Action Codes..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{ ...filterInputStyle, flex: 1 }}
        />
        <select value={domainFilter} onChange={(e) => setDomainFilter(e.target.value)} style={filterSelectStyle}>
          <option value="all">All Domains</option>
          {domains.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
      </div>

      <div style={tableContainerStyle}>
        <table style={tableStyle}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--slate-700)' }}>
              {['ID', 'Name', 'Domain', 'Impact', 'Status', 'Trigger KPIs'].map((h) => (
                <th key={h} style={thStyle}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((action) => (
              <ActionRow
                key={action.id}
                action={action}
                isExpanded={expanded === action.id}
                onToggle={() => setExpanded(expanded === action.id ? null : action.id)}
              />
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p style={{ padding: 'var(--sp-3)', textAlign: 'center', color: 'var(--slate-500)' }}>
            No Action Codes match the filter.
          </p>
        )}
      </div>
      <p style={{ marginTop: 'var(--sp-1)', fontSize: '0.75rem', color: 'var(--slate-500)' }}>
        Showing {filtered.length} of {actions.length} Action Codes
      </p>
    </div>
  );
}

function ActionRow({ action, isExpanded, onToggle }: { action: ActionCodeDefinitionV20AIMirror; isExpanded: boolean; onToggle: () => void }) {
  return (
    <>
      <tr
        onClick={onToggle}
        style={{
          borderBottom: '1px solid var(--slate-700)',
          cursor: 'pointer',
          transition: 'background-color var(--duration-fast) var(--ease-out)',
        }}
      >
        <td style={{ ...tdStyle, fontFamily: 'var(--font-mono)', color: 'var(--gold)', fontSize: '0.75rem' }}>{action.id}</td>
        <td style={{ ...tdStyle, color: 'var(--slate-100)' }}>{action.name}</td>
        <td style={{ ...tdStyle, color: 'var(--slate-400)' }}>{action.owner_domain}</td>
        <td style={{ ...tdStyle, color: 'var(--slate-400)' }}>{action.impact_dimension}</td>
        <td style={tdStyle}>
          <span style={{ color: getStatusColor(action.status), fontWeight: 500, fontSize: '0.75rem' }}>{action.status}</span>
        </td>
        <td style={{ ...tdStyle, fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--slate-400)' }}>
          {action.kpis.trigger_kpis.join(', ')}
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={6} style={expandedRowStyle}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--sp-2)', fontSize: '0.8125rem' }}>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>Trigger KPIs</p>
                <p style={{ fontFamily: 'var(--font-mono)', color: 'var(--slate-200)' }}>{action.kpis.trigger_kpis.join(', ')}</p>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', marginTop: 'var(--sp-1)' }}>Guardrail KPIs</p>
                <p style={{ fontFamily: 'var(--font-mono)', color: 'var(--slate-200)' }}>{(action.kpis.guardrail_kpis ?? []).join(', ') || '—'}</p>
              </div>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>Outcome KPIs</p>
                <p style={{ fontFamily: 'var(--font-mono)', color: 'var(--slate-200)' }}>{(action.kpis.outcome_kpis ?? []).join(', ') || '—'}</p>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', marginTop: 'var(--sp-1)' }}>Grain</p>
                <p style={{ color: 'var(--slate-200)' }}>{action.scope.default_grain}</p>
              </div>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>Owner Role</p>
                <p style={{ color: 'var(--slate-200)' }}>{action.owner_role}</p>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', marginTop: 'var(--sp-1)' }}>Steward Role</p>
                <p style={{ color: 'var(--slate-200)' }}>{action.steward_role}</p>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
