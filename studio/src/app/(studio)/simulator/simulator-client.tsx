'use client';

import { useState, useMemo, useCallback } from 'react';
import { parseFormula } from '@/lib/simulation/formula-parser';
import { runScenario } from '@/lib/simulation/scenario-engine';
import { ScenarioPanel } from '@/components/simulator/scenario-panel';
import { ImpactChart } from '@/components/simulator/impact-chart';

interface BracketSummary {
  id: string;
  title: string;
  domain: string;
  formula: string;
  impactDirection: 'maximize' | 'minimize';
  primaryDriver?: string;
  strategicKpiId: string;
  influencingKpiIds: string[];
}

interface Props {
  brackets: BracketSummary[];
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

export function SimulatorClient({ brackets }: Props) {
  const [selectedId, setSelectedId] = useState(brackets[0]?.id ?? '');
  const [overrides, setOverrides] = useState<Map<string, number>>(new Map());

  const bracket = brackets.find((b) => b.id === selectedId);
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
      {/* Illustrative data banner */}
      <div
        style={{
          padding: 'var(--sp-1) var(--sp-2)',
          backgroundColor: 'rgba(255,184,0,0.1)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--gold)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--sp-1)',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: 'var(--gold)', fontWeight: 600 }}>
          Illustrative Data
        </span>
        <span style={{ fontSize: '0.6875rem', color: 'var(--slate-400)' }}>
          Values are derived from KPI naming conventions. Connect real data sources for production use.
        </span>
      </div>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
        <select
          value={selectedId}
          onChange={(e) => { setSelectedId(e.target.value); setOverrides(new Map()); }}
          style={{
            padding: 'var(--sp-1) var(--sp-1-5)',
            backgroundColor: 'var(--slate-800)',
            border: '1px solid var(--slate-700)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--slate-100)',
            fontSize: '0.875rem',
            minWidth: '280px',
          }}
        >
          {brackets.map((b) => (
            <option key={b.id} value={b.id}>{b.id} — {b.title}</option>
          ))}
        </select>
        {bracket && (
          <span style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>
            {bracket.impactDirection === 'maximize' ? '↑' : '↓'} {bracket.strategicKpiId}
          </span>
        )}
      </div>

      {/* Result card */}
      {result && (
        <div
          style={{
            padding: 'var(--sp-2)',
            backgroundColor: result.isImprovement ? 'rgba(0,212,170,0.1)' : 'rgba(239,68,68,0.1)',
            borderRadius: 'var(--radius-lg)',
            border: `1px solid ${result.isImprovement ? 'var(--mint)' : 'var(--danger)'}`,
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--sp-3)',
          }}
        >
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>Strategic KPI</p>
            <p style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--slate-50)' }}>
              {result.adjustedValue.toFixed(1)}
              <span style={{ fontSize: '0.875rem', color: 'var(--slate-400)' }}> {getUnit(result.target)}</span>
            </p>
          </div>
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>Baseline</p>
            <p style={{ fontSize: '1rem', color: 'var(--slate-300)' }}>{result.baselineValue.toFixed(1)}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>Delta</p>
            <p style={{ fontSize: '1rem', fontWeight: 600, color: result.isImprovement ? 'var(--mint)' : 'var(--danger)' }}>
              {result.delta >= 0 ? '+' : ''}{result.delta.toFixed(2)} ({result.deltaPercent >= 0 ? '+' : ''}{result.deltaPercent.toFixed(1)}%)
            </p>
          </div>
        </div>
      )}

      {/* Two-column: sliders + impact chart */}
      {parsed && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-2)' }}>
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

      {/* Formula display */}
      {bracket && (
        <div style={{ padding: 'var(--sp-1-5)', backgroundColor: 'var(--slate-800)', borderRadius: 'var(--radius-md)', border: '1px solid var(--slate-700)' }}>
          <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', marginBottom: '4px' }}>Formula</p>
          <code style={{ fontSize: '0.75rem', color: 'var(--slate-300)', fontFamily: 'var(--font-mono)' }}>
            {bracket.formula}
          </code>
        </div>
      )}
    </div>
  );
}
