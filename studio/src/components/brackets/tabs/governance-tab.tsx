'use client';

import { useState } from 'react';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import type { FactsheetSummary } from '@/lib/core/factsheet-loader';
import { card, cardHead } from '@/components/registry/kpi-detail-tabs';
import { EditableList } from '@/components/brackets/editable-list';

interface Props {
  bracket: UseCaseBracketV20Lean;
  factsheet: FactsheetSummary | null;
}

const sectionLabel: React.CSSProperties = {
  fontSize: 11,
  textTransform: 'uppercase',
  color: 'var(--ink-3)',
  letterSpacing: '0.06em',
  fontWeight: 500,
  marginBottom: 8,
};

const dataGrid: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: '8px 16px',
};

const dataCell: React.CSSProperties = {
  padding: '8px 12px',
  background: 'var(--bg-2)',
  border: '1px solid var(--line)',
  borderRadius: 6,
};

const dataCellLabel: React.CSSProperties = {
  fontSize: 10.5,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  color: 'var(--ink-4)',
  marginBottom: 4,
};

const dataCellValue: React.CSSProperties = {
  fontSize: 12.5,
  color: 'var(--ink)',
  fontFamily: 'var(--font-mono)',
  wordBreak: 'break-word',
};

export function GovernanceTab({ bracket, factsheet }: Props) {
  const [outOfScope, setOutOfScope] = useState<string[]>(
    factsheet?.out_of_scope ?? []
  );
  const [successCriteria, setSuccessCriteria] = useState<string[]>([
    'Business questions answered',
    'KPI targets met',
  ]);
  const [risks, setRisks] = useState<string[]>([
    'Data freshness lag',
    'Grain mismatch',
  ]);

  const vdm = bracket.value_driver_model;

  return (
    <div>
      {/* Out of Scope */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Out of Scope
          </span>
        </div>
        <div style={{ padding: 'var(--pad)' }}>
          <EditableList
            label="Out of Scope Items"
            items={outOfScope}
            onChange={setOutOfScope}
            placeholder="Describe what is explicitly excluded…"
            entityType="use_case"
            entityId={bracket.id}
            entityName={bracket.title}
            fieldName="out_of_scope"
          />
        </div>
      </div>

      {/* Success Criteria */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Success Criteria
          </span>
        </div>
        <div style={{ padding: 'var(--pad)' }}>
          <EditableList
            label="Success Criteria"
            items={successCriteria}
            onChange={setSuccessCriteria}
            placeholder="Define a measurable success criterion…"
            entityType="use_case"
            entityId={bracket.id}
            entityName={bracket.title}
            fieldName="success_criteria"
          />
        </div>
      </div>

      {/* Risks */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Risks
          </span>
        </div>
        <div style={{ padding: 'var(--pad)' }}>
          <EditableList
            label="Identified Risks"
            items={risks}
            onChange={setRisks}
            placeholder="Describe a risk or assumption…"
            entityType="use_case"
            entityId={bracket.id}
            entityName={bracket.title}
            fieldName="risks"
          />
        </div>
      </div>

      {/* Data Requirements (read-only from value driver model) */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Data Requirements
          </span>
          <span style={{ fontSize: 11, color: 'var(--ink-4)' }}>from value driver model</span>
        </div>
        <div style={{ padding: 'var(--pad)' }}>
          <div style={sectionLabel}>Overview</div>
          <div style={dataGrid}>
            <div style={dataCell}>
              <div style={dataCellLabel}>Formula</div>
              <div
                style={{
                  ...dataCellValue,
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11.5,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {vdm.formula}
              </div>
            </div>

            <div style={dataCell}>
              <div style={dataCellLabel}>Primary Driver</div>
              <div style={dataCellValue}>
                {vdm.primary_driver ?? <span style={{ color: 'var(--ink-4)', fontStyle: 'italic', fontFamily: 'inherit' }}>—</span>}
              </div>
            </div>

            <div style={dataCell}>
              <div style={dataCellLabel}>Impact Direction</div>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '2px 8px',
                  borderRadius: 999,
                  fontSize: 11,
                  fontWeight: 500,
                  fontFamily: 'inherit',
                  background:
                    vdm.impact_direction === 'maximize'
                      ? 'oklch(0.25 0.06 145 / 0.4)'
                      : 'oklch(0.25 0.06 60 / 0.4)',
                  color:
                    vdm.impact_direction === 'maximize'
                      ? 'oklch(0.7 0.15 145)'
                      : 'oklch(0.7 0.15 60)',
                }}
              >
                {vdm.impact_direction}
              </span>
            </div>

            <div style={dataCell}>
              <div style={dataCellLabel}>Critical Threshold</div>
              <div style={dataCellValue}>
                {vdm.critical_threshold !== undefined
                  ? `${Math.round(vdm.critical_threshold * 100)}%`
                  : <span style={{ color: 'var(--ink-4)', fontStyle: 'italic', fontFamily: 'inherit' }}>—</span>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
