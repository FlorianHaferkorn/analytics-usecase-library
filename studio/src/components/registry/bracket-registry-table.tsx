'use client';

import { useState } from 'react';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';

interface Props {
  brackets: UseCaseBracketV20Lean[];
}

export function BracketRegistryTable({ brackets }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
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
            {['ID', 'Title', 'Domain', 'Strategic KPI', 'Drivers', 'Actions'].map((h) => (
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
          {brackets.map((bracket) => {
            const isExpanded = expanded === bracket.id;
            return (
              <BracketRow
                key={bracket.id}
                bracket={bracket}
                isExpanded={isExpanded}
                onToggle={() =>
                  setExpanded(isExpanded ? null : bracket.id)
                }
              />
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function BracketRow({
  bracket,
  isExpanded,
  onToggle,
}: {
  bracket: UseCaseBracketV20Lean;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const driverCount = bracket.orchestration.influencing_kpi_ids.length;
  const actionCount = bracket.orchestration.action_code_ids.length;
  const hasActionGap = driverCount > 0 && actionCount === 0;

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
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', fontFamily: 'var(--font-mono)', color: 'var(--info)', fontSize: '0.75rem' }}>
          {bracket.id}
        </td>
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', color: 'var(--slate-100)' }}>
          {bracket.title}
        </td>
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', color: 'var(--slate-400)' }}>
          {bracket.domain}
        </td>
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', fontFamily: 'var(--font-mono)', color: 'var(--mint)', fontSize: '0.75rem' }}>
          {bracket.orchestration.strategic_kpi_id}
        </td>
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', color: 'var(--slate-300)', textAlign: 'center' }}>
          {driverCount}
        </td>
        <td style={{ padding: 'var(--sp-1) var(--sp-1-5)', textAlign: 'center' }}>
          <span style={{ color: hasActionGap ? 'var(--danger)' : 'var(--slate-300)' }}>
            {actionCount}
            {hasActionGap && ' ⚠'}
          </span>
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={6} style={{ padding: 'var(--sp-2) var(--sp-1-5)', backgroundColor: 'var(--slate-850, #182030)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--sp-2)', fontSize: '0.8125rem' }}>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>Influencing KPIs</p>
                {bracket.orchestration.influencing_kpi_ids.map((id) => (
                  <p key={id} style={{ fontFamily: 'var(--font-mono)', color: 'var(--slate-200)', fontSize: '0.75rem' }}>{id}</p>
                ))}
              </div>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>Action Codes</p>
                {bracket.orchestration.action_code_ids.map((id) => (
                  <p key={id} style={{ fontFamily: 'var(--font-mono)', color: 'var(--gold)', fontSize: '0.75rem' }}>{id}</p>
                ))}
              </div>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>Value Driver</p>
                <p style={{ color: 'var(--slate-200)', fontSize: '0.75rem' }}>
                  {bracket.value_driver_model.impact_direction} {bracket.orchestration.strategic_kpi_id}
                </p>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', marginTop: 'var(--sp-1)' }}>Governance</p>
                <p style={{ color: 'var(--slate-200)', fontSize: '0.75rem' }}>
                  Owner: {bracket.governance.owner_role}
                </p>
                <p style={{ color: 'var(--slate-200)', fontSize: '0.75rem' }}>
                  Steward: {bracket.governance.steward_role}
                </p>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
