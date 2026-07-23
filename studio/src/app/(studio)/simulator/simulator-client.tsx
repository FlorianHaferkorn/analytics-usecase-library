'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { parseFormula } from '@/lib/simulation/formula-parser';
import { runScenario } from '@/lib/simulation/scenario-engine';
import { ScenarioPanel } from '@/components/simulator/scenario-panel';
import { ImpactChart } from '@/components/simulator/impact-chart';
import { StudioSelect } from '@/components/ui/studio-data';
import { StudioField, StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader, StudioPanel, StudioToolbar, StudioWorkflowFooter } from '@/components/ui/studio-page';
import { SpineContextCard } from '@/components/compose/spine-context-card';
import { AiField } from '@/components/ai/ai-field';
import { useDomainFilter } from '@/lib/hooks/use-domain-filter';
import { filterByDomain } from '@/lib/studio/domain-filter';
import type { AuroraKpiValue } from '@/lib/aurora/kpi-snapshot';
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
  auroraKpis?: Record<string, AuroraKpiValue> | null;
  auroraLinked?: boolean;
}

/** Seeded baseline — Aurora snapshot first, then KPI-id heuristics. */
function seedBaseValue(kpiId: string, auroraKpis?: Record<string, AuroraKpiValue> | null): number {
  const aurora = auroraKpis?.[kpiId];
  if (aurora) return aurora.value;

  const seed = kpiId.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  const pseudo = ((seed * 9301 + 49297) % 233280) / 233280;
  if (kpiId.includes('.pct')) return 30 + pseudo * 50;
  if (kpiId.includes('.days')) return 20 + pseudo * 30;
  if (kpiId.includes('.amount')) return 1000 + pseudo * 5000;
  return 50 + pseudo * 100;
}

import { formatKpiValue } from '@/lib/format/kpi-value';

function getUnit(kpiId: string): string {
  if (kpiId.includes('.pct')) return '%';
  if (kpiId.includes('.days')) return 'd';
  if (kpiId.includes('.amount')) return '€';
  if (kpiId.includes('.hours')) return 'h';
  if (kpiId.includes('.minutes')) return 'min';
  if (kpiId.includes('.units') || kpiId.includes('.count')) return '';
  return '';
}

/** Dispatch studio:open-chat event with a pre-filled context message. */
function openChatWithContext(message: string) {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('studio:open-chat', { detail: { message } }),
    );
  }
}

export function SimulatorClient({ brackets, spines, auroraKpis = null, auroraLinked = false }: Props) {
  const { domainFilter } = useDomainFilter();
  const visibleBrackets = useMemo(
    () => filterByDomain(brackets, domainFilter, (b) => b.domain),
    [brackets, domainFilter],
  );
  const [selectedId, setSelectedId] = useState(visibleBrackets[0]?.id ?? '');
  const [overrides, setOverrides] = useState<Map<string, number>>(new Map());
  const [impactLogic, setImpactLogic] = useState('');

  useEffect(() => {
    if (!visibleBrackets.some((b) => b.id === selectedId)) {
      setSelectedId(visibleBrackets[0]?.id ?? '');
    }
  }, [visibleBrackets, selectedId]);

  const bracket = visibleBrackets.find((b) => b.id === selectedId);

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
      map.set(id, seedBaseValue(id, auroraKpis));
    }
    return map;
  }, [parsed, auroraKpis]);

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
        eyebrow="Forge / Compose"
        title="What-if Simulator"
        description="Run controlled what-if scenarios against bracket formulas. Baselines prefer Aurora Showcase snapshot values when linked."
        badge={auroraLinked ? 'Aurora Showcase' : selectedId || 'No selection'}
        tone={auroraLinked ? 'info' : 'warning'}
      />

      <StudioMetricBar>
        <StudioMetric label="Brackets" value={visibleBrackets.length} meta="available for simulation" tone="info" />
        <StudioMetric label="Drivers" value={drivers.length} meta="for current scenario" />
        <StudioMetric label="Overrides" value={overriddenDrivers} meta={overriddenDrivers > 0 ? 'manual deviations active' : 'using seeded baseline'} tone={overriddenDrivers > 0 ? 'warning' : 'success'} />
        <StudioMetric label="Target" value={bracket?.strategicKpiId ?? 'n/a'} meta={bracket ? bracket.impactDirection : 'select a bracket'} tone="success" />
      </StudioMetricBar>

      {/* Decision spine context — shown when a bracket is selected */}
      {spines.length > 0 && bracket && (
        <SpineContextCard spines={spines} bracketId={bracket.id} />
      )}

      {/* Illustrative data banner */}
      <StudioPanel tone={auroraLinked ? 'info' : 'warning'} title={auroraLinked ? 'Aurora Showcase Simulation' : 'Illustrative Simulation'} description={auroraLinked ? 'Driver baselines come from the Aurora gold KPI snapshot — showcase data, not production SSOT.' : 'This view operates on synthetic seeded values, not live production data.'}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span style={{ fontSize: '0.5625rem', color: 'var(--ink-4)' }}>{auroraLinked ? 'Aurora Showcase linked' : 'No live data'}</span>
        </div>
        {!auroraLinked && (
          <>
            <p style={{ fontSize: '0.6875rem', color: 'var(--ink-2)', lineHeight: 1.5, marginBottom: '4px' }}>
              This simulation runs a <strong style={{ color: 'var(--ink)' }}>sensitivity analysis</strong>: how does the strategic KPI change when driver KPIs vary? Baseline values are synthesised from KPI-ID conventions
              (e.&nbsp;g. <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.625rem' }}>.pct</code> → 30&ndash;80&thinsp;%,&nbsp;
              <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.625rem' }}>.days</code> → 20&ndash;50).
            </p>
            <p style={{ fontSize: '0.625rem', color: 'var(--ink-4)' }}>
              For production scenarios: connect a real data pipeline and store baseline values in the use-case bracket.
            </p>
          </>
        )}
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
            {visibleBrackets.map((b) => (
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
              {formatKpiValue(result.adjustedValue, result.target)}
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

      <StudioWorkflowFooter label="Continue to Generate" href="/generate" />
    </StudioPage>
  );
}
