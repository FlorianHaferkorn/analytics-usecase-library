'use client';

import { useState } from 'react';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import type { FactsheetSummary } from '@/lib/core/factsheet-loader';
import { AiField } from '@/components/ai/ai-field';
import { card, cardHead } from '@/components/registry/kpi-detail-tabs';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Props {
  bracket: UseCaseBracketV20Lean;
  factsheet: FactsheetSummary | null;
}

// ─── MetaRow helper ───────────────────────────────────────────────────────────

function MetaRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '140px 1fr',
        gap: 8,
        padding: '8px 0',
        borderBottom: '1px solid var(--line-2)',
        alignItems: 'start',
      }}
    >
      <span
        style={{
          fontSize: 'var(--text-xs)',
          fontWeight: 500,
          color: 'var(--ink-4)',
          lineHeight: 1.5,
          paddingTop: 1,
        }}
      >
        {label}
      </span>
      <span style={{ fontSize: '0.8125rem', color: 'var(--ink-2)', lineHeight: 1.5 }}>
        {value || '—'}
      </span>
    </div>
  );
}

// ─── BracketOverviewTab ───────────────────────────────────────────────────────

export function BracketOverviewTab({ bracket, factsheet }: Props) {
  const [purpose, setPurpose] = useState(factsheet?.purpose ?? '');
  const [businessValue, setBusinessValue] = useState(factsheet?.business_value ?? '');
  const [questions, setQuestions] = useState<string[]>(
    factsheet?.business_questions ?? []
  );

  function handleAddQuestion() {
    setQuestions((prev) => [...prev, '']);
  }

  function handleQuestionChange(index: number, value: string) {
    setQuestions((prev) => prev.map((q, i) => (i === index ? value : q)));
  }

  const vdm = bracket.value_driver_model;

  return (
    <div>
      {/* Purpose card */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Purpose
          </span>
        </div>
        <div style={{ padding: 'var(--pad)' }}>
          <AiField
            entityType="use_case"
            entityId={bracket.id}
            entityName={bracket.title}
            fieldName="purpose"
            fieldLabel="Purpose"
            value={purpose}
            onChange={setPurpose}
            multiline
            rows={3}
            placeholder="Describe the business purpose of this use case…"
          />
        </div>
      </div>

      {/* Business Value card */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Business Value
          </span>
        </div>
        <div style={{ padding: 'var(--pad)' }}>
          <AiField
            entityType="use_case"
            entityId={bracket.id}
            entityName={bracket.title}
            fieldName="business_value"
            fieldLabel="Business Value"
            value={businessValue}
            onChange={setBusinessValue}
            multiline
            rows={3}
            placeholder="Describe the business value delivered by this use case…"
          />
        </div>
      </div>

      {/* Business Questions card */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Business Questions
          </span>
        </div>
        <div style={{ padding: 'var(--pad)' }}>
          {questions.map((q, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <AiField
                entityType="use_case"
                entityId={bracket.id}
                entityName={bracket.title}
                fieldName={`business_question_${i}`}
                fieldLabel={`Business Question ${i + 1}`}
                value={q}
                onChange={(v) => handleQuestionChange(i, v)}
                placeholder={`Question ${i + 1}…`}
              />
            </div>
          ))}
          <button
            onClick={handleAddQuestion}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 5,
              padding: '6px 12px',
              border: '1px solid var(--line)',
              borderRadius: 'var(--radius)',
              background: 'transparent',
              color: 'var(--ink-3)',
              fontSize: '0.8125rem',
              cursor: 'pointer',
              marginTop: questions.length > 0 ? 4 : 0,
            }}
          >
            + Add question
          </button>
        </div>
      </div>

      {/* Use Case Metadata card */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--ink)' }}>
            Use Case Metadata
          </span>
        </div>
        <div style={{ padding: '4px var(--pad) 12px' }}>
          <MetaRow
            label="Formula"
            value={
              <code
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  color: 'var(--ink-2)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                }}
              >
                {vdm.formula || '—'}
              </code>
            }
          />
          <MetaRow label="Primary Driver" value={vdm.primary_driver} />
          <MetaRow label="Impact Logic" value={vdm.impact_logic} />
          <MetaRow
            label="Critical Threshold"
            value={
              vdm.critical_threshold != null
                ? `${(vdm.critical_threshold * 100).toFixed(0)}%`
                : undefined
            }
          />
        </div>
      </div>
    </div>
  );
}
