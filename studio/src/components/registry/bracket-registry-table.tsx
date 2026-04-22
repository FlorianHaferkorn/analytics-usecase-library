'use client';

import { useState } from 'react';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import { Warning } from '@phosphor-icons/react';
import { BracketGovernancePanel } from './bracket-governance-panel';
import { StudioExpandedRow, StudioTable, StudioTableCell, StudioTableHeadCell, StudioTableShell } from '@/components/ui/studio-data';

interface Props {
  brackets: UseCaseBracketV20Lean[];
}

export function BracketRegistryTable({ brackets }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <StudioTableShell>
      <StudioTable>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--line)' }}>
            {['ID', 'Title', 'Domain', 'Strategic KPI', 'Drivers', 'Actions'].map((h) => (
              <StudioTableHeadCell key={h} style={{ fontWeight: 500, fontSize: '0.75rem' }}>{h}</StudioTableHeadCell>
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
      </StudioTable>
    </StudioTableShell>
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
          borderBottom: '1px solid var(--line)',
          cursor: 'pointer',
          transition: 'background-color var(--duration-fast) var(--ease-out)',
        }}
      >
        <StudioTableCell style={{ fontFamily: 'var(--font-mono)', color: 'var(--info)', fontSize: '0.75rem' }}>
          {bracket.id}
        </StudioTableCell>
        <StudioTableCell style={{ color: 'var(--ink)' }}>
          {bracket.title}
        </StudioTableCell>
        <StudioTableCell style={{ color: 'var(--ink-3)' }}>
          {bracket.domain}
        </StudioTableCell>
        <StudioTableCell style={{ fontFamily: 'var(--font-mono)', color: 'var(--mint)', fontSize: '0.75rem' }}>
          {bracket.orchestration.strategic_kpi_id}
        </StudioTableCell>
        <StudioTableCell style={{ color: 'var(--ink-2)', textAlign: 'center' }}>
          {driverCount}
        </StudioTableCell>
        <StudioTableCell style={{ textAlign: 'center' }}>
          <span style={{ color: hasActionGap ? 'var(--danger)' : 'var(--ink-2)' }}>
            {actionCount}
            {hasActionGap && <Warning size={12} style={{ verticalAlign: 'middle', marginLeft: '4px', color: 'var(--danger)' }} />}
          </span>
        </StudioTableCell>
      </tr>
      {isExpanded && (
        <StudioExpandedRow colSpan={6}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', fontSize: '0.8125rem' }}>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)' }}>Influencing KPIs</p>
                {bracket.orchestration.influencing_kpi_ids.map((id) => (
                  <p key={id} style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-2)', fontSize: '0.75rem' }}>{id}</p>
                ))}
              </div>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)' }}>Action Codes</p>
                {bracket.orchestration.action_code_ids.map((id) => (
                  <p key={id} style={{ fontFamily: 'var(--font-mono)', color: 'var(--gold)', fontSize: '0.75rem' }}>{id}</p>
                ))}
              </div>
              <div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)' }}>Value Driver</p>
                <p style={{ color: 'var(--ink-2)', fontSize: '0.75rem' }}>
                  {bracket.value_driver_model.impact_direction} {bracket.orchestration.strategic_kpi_id}
                </p>
                <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', marginTop: '8px' }}>Governance</p>
                <p style={{ color: 'var(--ink-2)', fontSize: '0.75rem' }}>
                  Owner: {bracket.governance.owner_role}
                </p>
                <p style={{ color: 'var(--ink-2)', fontSize: '0.75rem' }}>
                  Steward: {bracket.governance.steward_role}
                </p>
              </div>
            </div>
            <BracketGovernancePanel bracketId={bracket.id} />
        </StudioExpandedRow>
      )}
    </>
  );
}
