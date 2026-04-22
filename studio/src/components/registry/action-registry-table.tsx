'use client';

import { useState } from 'react';
import type { ActionCodeDefinitionV20AIMirror } from '@/lib/schemas';
import { getStatusColor } from '@/lib/status-colors';
import { StudioDataToolbar, StudioExpandedRow, StudioInlineStat, StudioInput, StudioSelect, StudioTable, StudioTableCell, StudioTableHeadCell, StudioTableShell } from '@/components/ui/studio-data';

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
      <StudioDataToolbar>
        <StudioInput
          type="text"
          placeholder="Search Action Codes..."
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
            <tr style={{ borderBottom: '1px solid var(--line)' }}>
              {['ID', 'Name', 'Domain', 'Impact', 'Status', 'Trigger KPIs'].map((h) => (
                <StudioTableHeadCell key={h}>{h}</StudioTableHeadCell>
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
        </StudioTable>
        {filtered.length === 0 && (
          <p style={{ padding: 'var(--pad)', textAlign: 'center', color: 'var(--ink-4)' }}>
            No Action Codes match the filter.
          </p>
        )}
      </StudioTableShell>
      <StudioInlineStat>
        Showing {filtered.length} of {actions.length} Action Codes
      </StudioInlineStat>
    </div>
  );
}

function ActionRow({ action, isExpanded, onToggle }: { action: ActionCodeDefinitionV20AIMirror; isExpanded: boolean; onToggle: () => void }) {
  return (
    <>
      <tr
        onClick={onToggle}
        style={{
          borderBottom: '1px solid var(--line)',
          cursor: 'pointer',
          transition: 'background-color var(--duration-fast) var(--ease-out)',
        }}
      >
        <StudioTableCell style={{ fontFamily: 'var(--font-mono)', color: 'var(--gold)', fontSize: '0.75rem' }}>{action.id}</StudioTableCell>
        <StudioTableCell style={{ color: 'var(--ink)' }}>{action.name}</StudioTableCell>
        <StudioTableCell style={{ color: 'var(--ink-3)' }}>{action.owner_domain}</StudioTableCell>
        <StudioTableCell style={{ color: 'var(--ink-3)' }}>{action.impact_dimension}</StudioTableCell>
        <StudioTableCell>
          <span style={{ color: getStatusColor(action.status), fontWeight: 500, fontSize: '0.75rem' }}>{action.status}</span>
        </StudioTableCell>
        <StudioTableCell style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--ink-3)' }}>
          {action.kpis.trigger_kpis.join(', ')}
        </StudioTableCell>
      </tr>
      {isExpanded && (
        <StudioExpandedRow colSpan={6}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', fontSize: '0.8125rem' }}>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)' }}>Trigger KPIs</p>
                <p style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-2)' }}>{action.kpis.trigger_kpis.join(', ')}</p>
                <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', marginTop: '8px' }}>Guardrail KPIs</p>
                <p style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-2)' }}>{(action.kpis.guardrail_kpis ?? []).join(', ') || '—'}</p>
              </div>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)' }}>Outcome KPIs</p>
                <p style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-2)' }}>{(action.kpis.outcome_kpis ?? []).join(', ') || '—'}</p>
                <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', marginTop: '8px' }}>Grain</p>
                <p style={{ color: 'var(--ink-2)' }}>{action.scope.default_grain}</p>
              </div>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)' }}>Owner Role</p>
                <p style={{ color: 'var(--ink-2)' }}>{action.owner_role}</p>
                <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', marginTop: '8px' }}>Steward Role</p>
                <p style={{ color: 'var(--ink-2)' }}>{action.steward_role}</p>
                {action.inherits_decision_spine && (
                  <>
                    <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', marginTop: '8px' }}>Decision Spine</p>
                    <p style={{ color: 'var(--info)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{action.inherits_decision_spine}</p>
                  </>
                )}
              </div>
            </div>
        </StudioExpandedRow>
      )}
    </>
  );
}
