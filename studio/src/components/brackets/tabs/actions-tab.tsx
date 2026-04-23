'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import { card, cardHead } from '@/components/registry/kpi-detail-tabs';
import { EditableList } from '@/components/brackets/editable-list';
import { AiField } from '@/components/ai/ai-field';

interface Props {
  bracket: UseCaseBracketV20Lean;
}

const sectionLabel: React.CSSProperties = {
  fontSize: 11,
  textTransform: 'uppercase',
  color: 'var(--ink-3)',
  letterSpacing: '0.06em',
  fontWeight: 500,
  marginBottom: 8,
};

const fieldGroup: React.CSSProperties = {
  marginBottom: 16,
};

export function ActionsTab({ bracket }: Props) {
  const [actionCodeIds, setActionCodeIds] = useState<string[]>(
    bracket.orchestration.action_code_ids
  );
  const [impactLogic, setImpactLogic] = useState(
    bracket.value_driver_model.impact_logic ?? ''
  );
  const [primaryDriver, setPrimaryDriver] = useState(
    bracket.value_driver_model.primary_driver ?? ''
  );

  const direction = bracket.value_driver_model.impact_direction;
  const threshold = bracket.value_driver_model.critical_threshold;

  return (
    <div>
      {/* Action Code IDs card */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Linked Action Codes
          </span>
        </div>
        <div style={{ padding: 'var(--pad)' }}>
          <EditableList
            label="Linked Action Codes"
            items={actionCodeIds}
            onChange={setActionCodeIds}
            placeholder="e.g. AC-001"
            entityType="use_case"
            entityId={bracket.id}
            entityName={bracket.title}
            fieldName="action_code_ids"
          />

          {actionCodeIds.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={sectionLabel}>Quick links</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {actionCodeIds.filter((id) => id.trim()).map((id) => (
                  <Link
                    key={id}
                    href="/catalog"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      padding: '3px 10px',
                      borderRadius: 999,
                      fontSize: 11.5,
                      fontFamily: 'var(--font-mono)',
                      background: 'var(--bg-2)',
                      color: 'var(--accent)',
                      border: '1px solid var(--line)',
                      textDecoration: 'none',
                    }}
                  >
                    {id}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Value Driver Model card */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Value Driver Model
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Impact direction badge */}
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '2px 8px',
                borderRadius: 999,
                fontSize: 11,
                fontWeight: 500,
                background:
                  direction === 'maximize'
                    ? 'oklch(0.25 0.06 145 / 0.4)'
                    : 'oklch(0.25 0.06 60 / 0.4)',
                color:
                  direction === 'maximize'
                    ? 'oklch(0.7 0.15 145)'
                    : 'oklch(0.7 0.15 60)',
              }}
            >
              {direction}
            </span>
            {/* Critical threshold badge */}
            {threshold !== undefined && (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '2px 8px',
                  borderRadius: 999,
                  fontSize: 11,
                  fontWeight: 500,
                  background: 'var(--bg-2)',
                  color: 'var(--ink-3)',
                  border: '1px solid var(--line)',
                }}
              >
                threshold: {Math.round(threshold * 100)}%
              </span>
            )}
          </div>
        </div>

        <div style={{ padding: 'var(--pad)' }}>
          {/* Formula */}
          <div style={fieldGroup}>
            <div style={sectionLabel}>Formula</div>
            <pre
              style={{
                margin: 0,
                padding: '10px 14px',
                background: 'var(--bg-2)',
                border: '1px solid var(--line)',
                borderRadius: 6,
                fontSize: 12.5,
                fontFamily: 'var(--font-mono)',
                color: 'var(--ink)',
                overflowX: 'auto',
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {bracket.value_driver_model.formula}
            </pre>
          </div>

          {/* Primary Driver */}
          <div style={fieldGroup}>
            <div style={sectionLabel}>Primary Driver</div>
            <AiField
              entityType="use_case"
              entityId={bracket.id}
              entityName={bracket.title}
              fieldName="primary_driver"
              fieldLabel="Primary Driver"
              value={primaryDriver}
              onChange={setPrimaryDriver}
              placeholder="e.g. com.win_rate"
            />
          </div>

          {/* Impact Logic */}
          <div style={fieldGroup}>
            <div style={sectionLabel}>Impact Logic</div>
            <AiField
              entityType="use_case"
              entityId={bracket.id}
              entityName={bracket.title}
              fieldName="impact_logic"
              fieldLabel="Impact Logic"
              value={impactLogic}
              onChange={setImpactLogic}
              multiline
              rows={4}
              placeholder="Explain how the primary driver influences the strategic KPI…"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
