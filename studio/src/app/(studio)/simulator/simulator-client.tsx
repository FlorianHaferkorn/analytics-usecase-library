'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { parseFormula } from '@/lib/simulation/formula-parser';
import { runScenario } from '@/lib/simulation/scenario-engine';
import { ScenarioPanel } from '@/components/simulator/scenario-panel';
import { ImpactChart } from '@/components/simulator/impact-chart';
import { StudioSelect } from '@/components/ui/studio-data';
import { StudioField, StudioPage, StudioPageHeader, StudioPanel, StudioToolbar, StudioWorkflowFooter } from '@/components/ui/studio-page';
import { SpineContextCard } from '@/components/compose/spine-context-card';
import { AiField } from '@/components/ai/ai-field';
import { useDomainFilter } from '@/lib/hooks/use-domain-filter';
import { filterByDomain } from '@/lib/studio/domain-filter';
import type { AuroraKpiValue } from '@/lib/aurora/kpi-snapshot';
import type { DecisionSpine } from '@/lib/schemas/decision-spine';
import styles from './simulator-client.module.css';
import { formatKpiValue, kpiUnit } from '@/lib/format/kpi-value';
import { driverSliderRange } from '@/lib/simulation/slider-range';

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

function getUnit(kpiId: string, auroraKpis?: Record<string, AuroraKpiValue> | null): string {
  // Currency comes from the supplied data, not from a large number or an amount ID.
  return auroraKpis?.[kpiId]?.unit ?? (kpiId.includes('.amount') ? '' : kpiUnit(kpiId));
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
      const unit = getUnit(id, auroraKpis);
      const { minRange, maxRange } = driverSliderRange(base, unit, id);
      return {
        kpiId: id,
        label: id.split('.').slice(-2).join('.'),
        baseValue: base,
        unit,
        minRange,
        maxRange,
      };
    });
  }, [parsed, baseValues, auroraKpis]);

  const handleOverride = useCallback((kpiId: string, value: number) => {
    setOverrides((prev) => new Map(prev).set(kpiId, value));
  }, []);

  const handleReset = useCallback(() => setOverrides(new Map()), []);
  const overriddenDrivers = overrides.size;
  const resultUnchanged = result ? Math.abs(result.delta) <= Number.EPSILON * Math.max(1, Math.abs(result.baselineValue)) * 8 : true;
  const resultUnit = result ? getUnit(result.target, auroraKpis) : '';

  const handleWhyTarget = useCallback((kpiId: string) => {
    if (!bracket) return;
    const overrideValue = overrides.get(kpiId) ?? baseValues.get(kpiId) ?? 0;
    const message = `For ${bracket.title}, explain why the target for ${kpiId} matters and what achieving it would mean. The formula is: ${bracket.formula}. Current value: ${overrideValue.toFixed(2)}.`;
    openChatWithContext(message);
  }, [bracket, overrides, baseValues]);

  return (
    <StudioPage>
      <StudioPageHeader
        eyebrow="Shape / Simulate"
        title="What-if Simulator"
        description="Adjust driver values and compare their calculated impact on the selected KPI."
        badge={auroraLinked ? 'Aurora Showcase' : selectedId || 'No selection'}
        tone={auroraLinked ? 'info' : 'warning'}
      />

      <p className={styles.disclaimer}>
        <strong>Illustrative simulation.</strong> {auroraLinked
          ? 'Aurora showcase values are used where available; remaining values are synthetic. Not a production forecast.'
          : 'Baseline values are synthetic, not live customer data. Results are not a production forecast.'}
      </p>

      {/* Header */}
      <StudioToolbar>
        <StudioField label="Scenario focus">
          <StudioSelect
            value={selectedId}
            onChange={(e) => { setSelectedId(e.target.value); setOverrides(new Map()); }}
            style={{
              fontSize: '0.875rem',
              width: 'min(100%, 32rem)',
              minWidth: 0,
            }}
          >
            {visibleBrackets.map((b) => (
              <option key={b.id} value={b.id}>{b.id} — {b.title}</option>
            ))}
          </StudioSelect>
        </StudioField>
        <span className={styles.scenarioMeta}>{drivers.length} drivers · {overriddenDrivers} overrides</span>
        {bracket && (
          <span style={{ fontSize: '0.75rem', color: 'var(--ink-3)' }}>
            {bracket.impactDirection === 'maximize' ? '↑' : '↓'} {bracket.strategicKpiId}
          </span>
        )}
      </StudioToolbar>

      {/* Result card */}
      {result && (
        <StudioPanel tone={resultUnchanged ? 'default' : result.isImprovement ? 'success' : 'warning'} title="Simulation Result" description="Calculated change from the illustrative baseline after your driver overrides." compactHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--pad)', flexWrap: 'wrap' }}>
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)' }}>Strategic KPI</p>
            <p style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--ink)' }}>
              {formatKpiValue(result.adjustedValue, result.target, resultUnit)}
            </p>
          </div>
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)' }}>Baseline</p>
            <p style={{ fontSize: '1rem', color: 'var(--ink-2)' }}>{formatKpiValue(result.baselineValue, result.target, resultUnit)}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)' }}>Delta</p>
            <p style={{ fontSize: '1rem', fontWeight: 600, color: resultUnchanged ? 'var(--ink-3)' : result.isImprovement ? 'var(--accent)' : 'var(--danger)' }}>
              {resultUnchanged ? 'No change' : <>{result.delta > 0 ? '+' : ''}{formatKpiValue(result.delta, result.target, resultUnit === '%' ? 'pp' : resultUnit)} ({result.deltaPercent > 0 ? '+' : ''}{formatKpiValue(result.deltaPercent, 'relative.pct')})</>}
            </p>
          </div>
          </div>
        </StudioPanel>
      )}

      {/* Two-column: sliders + impact chart */}
      {parsed && (
        <div className={styles.workbench}>
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
              targetKpiId={result.target}
              targetUnit={resultUnit}
            />
          )}
        </div>
      )}

      <details className={styles.details}>
        <summary>Assumptions, decision context and impact logic</summary>
        <div className={styles.detailsBody}>
          <p>This is a sensitivity analysis of the configured formula, not a prediction of customer performance. {auroraLinked
            ? 'Linked driver values use the Aurora showcase snapshot; missing values use the synthetic fallback.'
            : 'The fallback derives repeatable example values from KPI identifiers: percentage drivers use 30–80% and day-based drivers use 20–50 days.'} Validate the baseline, units, formula and driver ranges with customer evidence before using results in a business case.</p>
          {spines.length > 0 && bracket && <SpineContextCard spines={spines} bracketId={bracket.id} />}
          {bracket && (
            <StudioPanel title="Impact logic" description="Describe why the drivers affect this KPI. This explanation does not change the calculation formula." compactHeader>
              <AiField entityType="bracket" entityId={bracket.id} entityName={bracket.title} fieldName="impact_logic" fieldLabel="Impact Logic" value={impactLogic} onChange={setImpactLogic} multiline rows={2} placeholder="Describe how the drivers affect the strategic KPI…" />
            </StudioPanel>
          )}
          {bracket && <StudioPanel title="Calculation formula" compactHeader><code className={styles.formula}>{bracket.formula}</code></StudioPanel>}
        </div>
      </details>

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
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-3)', fontSize: 'var(--text-xs)' }}>{d.label}</span>
                <span>Why?</span>
              </button>
            ))}
          </div>
        </StudioPanel>
      )}

      <StudioWorkflowFooter label="Continue to Generate" href="/generate" />
    </StudioPage>
  );
}
