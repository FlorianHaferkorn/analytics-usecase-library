'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { parseFormula } from '@/lib/simulation/formula-parser';
import { runScenario } from '@/lib/simulation/scenario-engine';
import { ScenarioPanel } from '@/components/simulator/scenario-panel';
import { ImpactChart } from '@/components/simulator/impact-chart';
import { StudioSelect } from '@/components/ui/studio-data';
import { StudioField, StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader, StudioPanel, StudioToolbar } from '@/components/ui/studio-page';
import { SpineContextCard } from '@/components/compose/spine-context-card';
import { AiField } from '@/components/ai/ai-field';
import type { DecisionSpine } from '@/lib/schemas/decision-spine';

interface BracketSummary {
  id: string;
  title: string;
  domain: string;
  formula: string;
  impactDirection: 'maximize' | 'minimize';
  primaryDriver?: string;
  strategicKpiId: string;
  influencingKpiIds: string[];
  impactLogic: string;
}

interface Props {
  brackets: BracketSummary[];
  spines: DecisionSpine[];
}

/** Generate synthetic base values for KPI IDs based on naming conventions. */
function generateBaseValue(kpiId: string): number {
  if (kpiId.includes('.pct')) return 40 + Math.random() * 40;
  if (kpiId.includes('.days')) return 20 + Math.random() * 30;
  if (kpiId.includes('.amount')) return 1000 + Math.random() * 5000;
  if (kpiId.includes('.count')) return 50 + Math.random() * 200;
  if (kpiId.includes('.hours')) return 100 + Math.random() * 500;
  if (kpiId.includes('.units')) return 500 + Math.random() * 2000;
  if (kpiId.includes('.index')) return 50 + Math.random() * 50;
  if (kpiId.includes('.minutes')) return 5 + Math.random() * 20;
  return 100 + Math.random() * 100;
}

function getUnit(kpiId: string): string {
  if (kpiId.includes('.pct')) return '%';
  if (kpiId.includes('.days')) return 'd';
  if (kpiId.includes('.amount')) return '€K';
  if (kpiId.includes('.hours')) return 'h';
  if (kpiId.includes('.minutes')) return 'min';
  if (kpiId.includes('.units') || kpiId.includes('.count')) return '';
  return '';
}

// Suppress unused lint warning — generateBaseValue is kept for reference
void generateBaseValue;

/** Dispatch studio:open-chat event with a pre-filled context message. */
function openChatWithContext(message: string) {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('studio:open-chat', { detail: { message } }),
    );
  }
}

export function SimulatorClient({ brackets, spines }: Props) {
  const [selectedId, setSelectedId] = useState(brackets[0]?.id ?? '');
  const [overrides, setOverrides] = useState<Map<string, number>>(new Map());
  const [impactLogic, setImpactLogic] = useState('');

  const bracket = brackets.find((b) => b.id === selectedId);

  // Reset impactLogic when selected bracket changes
  useEffect(() => {
    setImpactLogic(bracket?.impactLogic ?? '');
  }, [selectedId, bracket?.impactLogic]);

  const parsed = useMemo(() => (bracket ? parseFormula(bracket.formula) : null), [bracket]);

  // Stable base values seeded per bracket
  const baseValues = useMemo(() => {
    if (!parsed) return new Map<string, number>();
    const map = new Map<string, number>();
    const allIds = parsed.type === 'additive'
      ? [parsed.target, ...parsed.terms.map((t) => t.kpiId)]
      : [parsed.target, ...parsed.drivers];
    for (const id of allIds) {
      // Seed pseudo-random from KPI ID for consistency
      const seed = id.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
      const pseudo = ((seed * 9301 + 49297) % 233280) / 233280;
      if (id.includes('.pct')) map.set(id, 30 + pseudo * 50);
      else if (id.includes('.days')) map.set(id, 20 + pseudo * 30);
      else if (id.includes('.amount')) map.set(id, 1000 + pseudo * 5000);
      else map.set(id, 50 + pseudo * 100);
    }
    return map;
  }, [parsed]);

  const result = useMemo(() => {
    if (!parsed || !bracket) return null;
    return runScenario(parsed, baseValues, overrides, bracket.impactDirection);
  }, [parsed, baseValues, overrides, bracket]);

  const drivers = useMemo(() => {
    if (!parsed) return [];
    const ids = parsed.type === 'additive' ? parsed.terms.map((t) => t.kpiId) : parsed.drivers;
    return ids.map((id) => {
      const base = baseValues.get(id) ?? 0;
      // Adaptive slider range based on KPI type
      let minRange: number;
      let maxRange: number;
      if (id.includes('.pct')) {
        minRange = Math.max(0, base - 15);
        maxRange = Math.min(100, base + 15);
      } else if (id.includes('.days') || id.includes('.hours') || id.includes('.minutes')) {
        minRange = Math.max(0, base * 0.5);
        maxRange = base * 1.5;
      } else {
        minRange = Math.max(0, base * 0.7);
        maxRange = base * 1.3;
      }
      return {
        kpiId: id,
        label: id.split('.').slice(-2).join('.'),
        baseValue: base,
        unit: getUnit(id),
        minRange,
        maxRange,
      };
    });
  }, [parsed, baseValues]);

  const handleOverride = useCallback((kpiId: string, value: number) => {
    setOverrides((prev) => new Map(prev).set(kpiId, value));
  }, []);

  const handleReset = useCallback(() => setOverrides(new Map()), []);
  const overriddenDrivers = overrides.size;

  const handleWhyTarget = useCallback((kpiId: string) => {
    if (!bracket) return;
    const overrideValue = overrides.get(kpiId) ?? baseValues.get(kpiId) ?? 0;
    const message = `For ${bracket.title}, explain why the target for ${kpiId} matters and what achieving it would mean. The formula is: ${bracket.formula}. Current value: ${overrideValue.toFixed(2)}.`;
    openChatWithContext(message);
  }, [bracket, overrides, baseValues]);

  return (
    <StudioPage>
      <StudioPageHeader
        eyebrow="Studio / What-if"
        title="Simulator"
        description="Run controlled what-if scenarios against bracket formulas to understand driver sensitivity before real data pipelines are wired in."
        badge={selectedId || 'No selection'}
        tone="warning"
      />

      <StudioMetricBar>
        <StudioMetric label="Brackets" value={brackets.length} meta="available for simulation" tone="info" />
        <StudioMetric label="Drivers" value={drivers.length} meta="for current scenario" />
        <StudioMetric label="Overrides" value={overriddenDrivers} meta={overriddenDrivers > 0 ? 'manual deviations active' : 'using seeded baseline'} tone={overriddenDrivers > 0 ? 'warning' : 'success'} />
        <StudioMetric label="Target" value={bracket?.strategicKpiId ?? 'n/a'} meta={bracket ? bracket.impactDirection : 'select a bracket'} tone="success" />
      </StudioMetricBar>

      {/* Decision spine context — shown when a bracket is selected */}
      {spines.length > 0 && bracket && (
        <SpineContextCard spines={spines} bracketId={bracket.id} />
      )}

      {/* Illustrative data banner */}
      <StudioPanel tone="warning" title="Illustrative Simulation" description="This view operates on synthetic seeded values, not live production data.">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span style={{ fontSize: '0.5625rem', color: 'var(--ink-4)' }}>Keine Echtdaten</span>
        </div>
        <p style={{ fontSize: '0.6875rem', color: 'var(--ink-2)', lineHeight: 1.5, marginBottom: '4px' }}>
          Diese Simulation zeigt eine <strong style={{ color: 'var(--ink)' }}>Sensitivitätsanalyse</strong>: Wie verändert sich der strategische KPI,
          wenn Treiber-KPIs variieren? Die Ausgangswerte werden anhand der KPI-ID-Konventionen
          (z.&nbsp;B. <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.625rem' }}>.pct</code> → 30&ndash;80&thinsp;%,&nbsp;
          <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.625rem' }}>.days</code> → 20&ndash;50) synthetisch erzeugt.
        </p>
        <p style={{ fontSize: '0.625rem', color: 'var(--ink-4)' }}>
          Für produktive Szenarien: echte Datenpipeline anschließen und Basiswerte im Use-Case-Bracket hinterlegen.
        </p>
      </StudioPanel>

      {/* Header */}
      <StudioToolbar>
        <StudioField label="Scenario focus">
          <StudioSelect
            value={selectedId}
            onChange={(e) => { setSelectedId(e.target.value); setOverrides(new Map()); }}
            style={{
              fontSize: '0.875rem',
              minWidth: '280px',
            }}
          >
            {brackets.map((b) => (
              <option key={b.id} value={b.id}>{b.id} — {b.title}</option>
            ))}
          </StudioSelect>
        </StudioField>
        {bracket && (
          <span style={{ fontSize: '0.75rem', color: 'var(--ink-3)' }}>
            {bracket.impactDirection === 'maximize' ? '↑' : '↓'} {bracket.strategicKpiId}
          </span>
        )}
      </StudioToolbar>

      {/* Impact Logic editor */}
      {bracket && (
        <StudioPanel title="Impact Logic" description="Describe how the driver KPIs affect the strategic KPI in this bracket.">
          <AiField
            entityType="bracket"
            entityId={bracket.id}
            entityName={bracket.title}
            fieldName="impact_logic"
            fieldLabel="Impact Logic"
            value={impactLogic}
            onChange={setImpactLogic}
            multiline
            rows={2}
            placeholder="Describe how the drivers affect the strategic KPI…"
          />
        </StudioPanel>
      )}

      {/* Result card */}
      {result && (
        <StudioPanel tone={result.isImprovement ? 'success' : 'warning'} title="Simulation Result" description="Compare the adjusted strategic KPI against its synthetic baseline after driver overrides.">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--pad)', flexWrap: 'wrap' }}>
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)' }}>Strategic KPI</p>
            <p style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--ink)' }}>
              {result.adjustedValue.toFixed(1)}
              <span style={{ fontSize: '0.875rem', color: 'var(--ink-3)' }}> {getUnit(result.target)}</span>
            </p>
          </div>
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)' }}>Baseline</p>
            <p style={{ fontSize: '1rem', color: 'var(--ink-2)' }}>{result.baselineValue.toFixed(1)}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)' }}>Delta</p>
            <p style={{ fontSize: '1rem', fontWeight: 600, color: result.isImprovement ? 'var(--accent)' : 'var(--danger)' }}>
              {result.delta >= 0 ? '+' : ''}{result.delta.toFixed(2)} ({result.deltaPercent >= 0 ? '+' : ''}{result.deltaPercent.toFixed(1)}%)
            </p>
          </div>
          </div>
        </StudioPanel>
      )}

      {/* Two-column: sliders + impact chart */}
      {parsed && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <ScenarioPanel
            drivers={drivers}
            overrides={overrides}
            onOverride={handleOverride}
            onReset={handleReset}
          />
          {result && (
            <ImpactChart
              contributions={result.driverContributions}
              impactDirection={result.impactDirection}
            />
          )}
        </div>
      )}

      {/* "Why this target?" — per-driver AI context buttons */}
      {bracket && drivers.length > 0 && (
        <StudioPanel title="Why This Target?" description="Ask the AI to explain why each driver target matters for the strategic KPI.">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {drivers.map((d) => (
              <button
                key={d.kpiId}
                onClick={() => handleWhyTarget(d.kpiId)}
                style={{
                  background: 'transparent',
                  border: '1px solid var(--line)',
                  borderRadius: 6,
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  color: 'var(--ink-3)',
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-4)', fontSize: '0.6875rem' }}>{d.label}</span>
                <span>Why?</span>
              </button>
            ))}
          </div>
        </StudioPanel>
      )}

      {/* Formula display */}
      {bracket && (
        <StudioPanel title="Formula" description="Current value-driver formula used for the simulation engine.">
          <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', marginBottom: '4px' }}>Formula</p>
          <code style={{ fontSize: '0.75rem', color: 'var(--ink-2)', fontFamily: 'var(--font-mono)' }}>
            {bracket.formula}
          </code>
        </StudioPanel>
      )}
    </StudioPage>
  );
}
