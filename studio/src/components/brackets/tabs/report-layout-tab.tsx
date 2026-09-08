'use client';

import { useState } from 'react';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import { AiField } from '@/components/ai/ai-field';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Props {
  bracket: UseCaseBracketV20Lean;
}

type VisualType =
  | 'kpi_card'
  | 'trend_line'
  | 'line_chart'
  | 'bar_chart'
  | 'bar_chart_horizontal'
  | 'waterfall'
  | 'stacked_bar'
  | 'funnel';

interface SlotState {
  slot_id: string;
  visual_type: VisualType;
  kpi_id?: string;
  kpi_ids?: string[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const VISUAL_TYPE_OPTIONS: VisualType[] = [
  'kpi_card',
  'trend_line',
  'line_chart',
  'bar_chart',
  'bar_chart_horizontal',
  'waterfall',
  'stacked_bar',
  'funnel',
];

const sectionLabel: React.CSSProperties = {
  fontSize: 'var(--text-xs)',
  fontWeight: 600,
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
  color: 'var(--ink-3)',
  marginBottom: 8,
};

const divider: React.CSSProperties = {
  borderTop: '1px solid var(--line)',
  margin: '24px 0',
};

// ─── SlotCard ─────────────────────────────────────────────────────────────────

interface SlotCardProps {
  slot: SlotState;
  onVisualTypeChange: (slotId: string, value: VisualType) => void;
}

function SlotCard({ slot, onVisualTypeChange }: SlotCardProps) {
  const kpiLabels: string[] = slot.kpi_ids
    ? slot.kpi_ids
    : slot.kpi_id
    ? [slot.kpi_id]
    : [];

  return (
    <div
      style={{
        flex: 1,
        minWidth: 0,
        height: 160,
        background: 'var(--panel)',
        border: '1px solid var(--line)',
        borderRadius: 8,
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Card header */}
      <div
        style={{
          padding: '8px 10px 6px',
          borderBottom: '1px solid var(--line-2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 8,
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            color: 'var(--ink-3)',
            letterSpacing: '0.04em',
          }}
        >
          {slot.slot_id}
        </span>
        <select
          value={slot.visual_type}
          onChange={(e) => onVisualTypeChange(slot.slot_id, e.target.value as VisualType)}
          style={{
            background: 'var(--bg-2)',
            border: '1px solid var(--line)',
            borderRadius: 4,
            color: 'var(--ink-2)',
            fontSize: 'var(--text-xs)',
            padding: '2px 6px',
            cursor: 'pointer',
          }}
        >
          {VISUAL_TYPE_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </div>

      {/* KPI pills */}
      <div
        style={{
          padding: '8px 10px',
          flex: 1,
          overflow: 'hidden',
          display: 'flex',
          flexWrap: 'wrap',
          alignContent: 'flex-start',
          gap: 4,
        }}
      >
        {kpiLabels.length > 0 ? (
          kpiLabels.map((id) => (
            <span
              key={id}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-xs)',
                color: 'var(--ink-3)',
                background: 'var(--hover)',
                borderRadius: 4,
                padding: '2px 6px',
                whiteSpace: 'nowrap',
              }}
            >
              {id}
            </span>
          ))
        ) : (
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-4)', fontStyle: 'italic' }}>
            No KPI assigned
          </span>
        )}
      </div>
    </div>
  );
}

// ─── ReportLayoutTab ──────────────────────────────────────────────────────────

export function ReportLayoutTab({ bracket }: Props) {
  const page1 = bracket.ux_layout_rules.page_1_summary;
  const page2 = bracket.ux_layout_rules.page_2_execution;

  // decision_question and big_idea exist in YAML data but are not yet in the
  // generated schema type — access via index signature with a runtime guard.
  const page1Extra = page1 as Record<string, unknown>;

  const [decisionQuestion, setDecisionQuestion] = useState(
    typeof page1Extra['decision_question'] === 'string'
      ? page1Extra['decision_question']
      : ''
  );
  const [bigIdea, setBigIdea] = useState(
    typeof page1Extra['big_idea'] === 'string' ? page1Extra['big_idea'] : ''
  );

  const [slots, setSlots] = useState<SlotState[]>(() => {
    const raw = page1.component_30s ?? [];
    return raw.map((s, i) => ({
      slot_id: s.slot_id ?? `Main_${i + 1}`,
      visual_type: s.visual_type as VisualType,
      kpi_id: s.kpi_id,
      kpi_ids: s.kpi_ids,
    }));
  });

  const [saveState, setSaveState] = useState<'idle' | 'saved'>('idle');

  function handleVisualTypeChange(slotId: string, value: VisualType) {
    setSlots((prev) =>
      prev.map((s) => (s.slot_id === slotId ? { ...s, visual_type: value } : s))
    );
  }

  function handleSave() {
    // Stub: POST to /api/brackets/[id]/layout (endpoint not yet implemented)
    setSaveState('saved');
    setTimeout(() => setSaveState('idle'), 1800);
  }

  const evidenceColumns = page2.component_300s.evidence_columns ?? [];

  return (
    <div style={{ paddingBottom: 32 }}>
      {/* ── Section A: Page 1 Overview ─────────────────────────────── */}
      <div style={sectionLabel}>Page 1 — Overview (3s / 30s)</div>

      <div
        style={{
          background: 'var(--panel)',
          border: '1px solid var(--line)',
          borderRadius: 8,
          padding: '16px',
          marginBottom: 16,
        }}
      >
        <div style={{ marginBottom: 14 }}>
          <div
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              color: 'var(--ink-3)',
              marginBottom: 6,
            }}
          >
            Decision Question
          </div>
          <AiField
            entityType="use_case"
            entityId={bracket.id}
            entityName={bracket.title}
            fieldName="decision_question"
            fieldLabel="Decision Question"
            value={decisionQuestion}
            onChange={setDecisionQuestion}
            placeholder="Are we on track for our targets this month?"
          />
        </div>

        <div>
          <div
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              color: 'var(--ink-3)',
              marginBottom: 6,
            }}
          >
            Big Idea
          </div>
          <AiField
            entityType="use_case"
            entityId={bracket.id}
            entityName={bracket.title}
            fieldName="big_idea"
            fieldLabel="Big Idea"
            value={bigIdea}
            onChange={setBigIdea}
            multiline
            rows={2}
            placeholder="One-sentence headline for the page narrative…"
          />
        </div>
      </div>

      {/* Grid canvas — 30s slots */}
      <div
        style={{
          fontSize: 'var(--text-xs)',
          fontWeight: 600,
          color: 'var(--ink-3)',
          marginBottom: 8,
        }}
      >
        30-Second Layer — Main Slots
      </div>
      <div
        style={{
          display: 'flex',
          gap: 12,
          width: '100%',
          marginBottom: 8,
        }}
      >
        {slots.length > 0 ? (
          slots.map((slot) => (
            <SlotCard
              key={slot.slot_id}
              slot={slot}
              onVisualTypeChange={handleVisualTypeChange}
            />
          ))
        ) : (
          <div
            style={{
              flex: 1,
              height: 160,
              border: '1px dashed var(--line)',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--ink-4)',
              fontSize: 13,
            }}
          >
            No 30s slots defined
          </div>
        )}
      </div>

      <div style={divider} />

      {/* ── Section B: Page 2 Detail ───────────────────────────────── */}
      <div style={sectionLabel}>Page 2 — Detail (300s)</div>

      <div
        style={{
          background: 'var(--panel)',
          border: '1px solid var(--line)',
          borderRadius: 8,
          padding: '16px',
        }}
      >
        <div style={{ marginBottom: 14 }}>
          <div
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              color: 'var(--ink-3)',
              marginBottom: 6,
            }}
          >
            Evidence Grain
          </div>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--ink-2)',
              background: 'var(--hover)',
              padding: '3px 8px',
              borderRadius: 4,
            }}
          >
            {page2.component_300s.evidence_grain || '—'}
          </span>
        </div>

        <div style={{ marginBottom: 14 }}>
          <div
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              color: 'var(--ink-3)',
              marginBottom: 6,
            }}
          >
            Evidence Columns
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {evidenceColumns.length > 0 ? (
              evidenceColumns.map((col) => (
                <span
                  key={col}
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 'var(--text-xs)',
                    color: 'var(--ink-3)',
                    background: 'var(--hover)',
                    padding: '2px 7px',
                    borderRadius: 4,
                  }}
                >
                  {col}
                </span>
              ))
            ) : (
              <span style={{ fontSize: 12, color: 'var(--ink-4)', fontStyle: 'italic' }}>
                No columns defined
              </span>
            )}
          </div>
        </div>

        <div>
          <div
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              color: 'var(--ink-3)',
              marginBottom: 6,
            }}
          >
            Action Panel
          </div>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '3px 10px',
              borderRadius: 999,
              fontSize: 'var(--text-xs)',
              fontWeight: 500,
              background: page2.component_300s.action_panel
                ? 'var(--accent-soft)'
                : 'var(--hover)',
              color: page2.component_300s.action_panel
                ? 'var(--accent)'
                : 'var(--ink-3)',
              border: '1px solid var(--line)',
            }}
          >
            {page2.component_300s.action_panel ? 'Enabled' : 'Disabled'}
          </span>
        </div>
      </div>

      {/* ── Save stub ──────────────────────────────────────────────── */}
      <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end' }}>
        <button
          onClick={handleSave}
          style={{
            padding: '7px 16px',
            border: '1px solid var(--line)',
            borderRadius: 6,
            background: 'transparent',
            color: saveState === 'saved' ? 'var(--accent)' : 'var(--ink-3)',
            fontSize: 13,
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'color 150ms',
          }}
        >
          {saveState === 'saved' ? 'Saved' : 'Save changes'}
        </button>
      </div>
    </div>
  );
}
