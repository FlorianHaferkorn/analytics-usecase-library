/**
 * Tests for Scenario Engine.
 */

import { describe, it, expect } from 'vitest';
import { parseFormula } from '../../src/lib/simulation/formula-parser';
import { runScenario } from '../../src/lib/simulation/scenario-engine';

describe('runScenario', () => {
  it('returns zero delta when no overrides', () => {
    const formula = parseFormula('KPI-FIN-006 = KPI-FIN-001 + KPI-FIN-004 - KPI-FIN-005')!;
    const baseValues = new Map([
      ['KPI-FIN-006', 38],
      ['KPI-FIN-001', 25],
      ['KPI-FIN-004', 30],
      ['KPI-FIN-005', 17],
    ]);
    const result = runScenario(formula, baseValues, new Map(), 'minimize');
    expect(result.delta).toBe(0);
    expect(result.adjustedValue).toBe(38);
  });

  it('recalculates additive formula with overrides', () => {
    const formula = parseFormula('KPI-FIN-006 = KPI-FIN-001 + KPI-FIN-004 - KPI-FIN-005')!;
    const baseValues = new Map([
      ['KPI-FIN-006', 38],
      ['KPI-FIN-001', 25],
      ['KPI-FIN-004', 30],
      ['KPI-FIN-005', 17],
    ]);
    // Reduce DSO from 25 to 20
    const overrides = new Map([['KPI-FIN-001', 20]]);
    const result = runScenario(formula, baseValues, overrides, 'minimize');
    // 20 + 30 - 17 = 33
    expect(result.adjustedValue).toBe(33);
    expect(result.delta).toBe(-5);
    expect(result.isImprovement).toBe(true); // minimize: negative delta = improvement
  });

  it('handles functional formula with overrides', () => {
    const formula = parseFormula('KPI-COM-013 = f(KPI-COM-001, KPI-COM-002)')!;
    const baseValues = new Map([
      ['KPI-COM-013', 40],
      ['KPI-COM-001', 100],
      ['KPI-COM-002', 200],
    ]);
    // Increase KPI-COM-001 by 10% (100 → 110)
    const overrides = new Map([['KPI-COM-001', 110]]);
    const result = runScenario(formula, baseValues, overrides, 'maximize');
    // 10% increase in one of 2 drivers → 5% avg → 40 * 1.05 = 42
    expect(result.adjustedValue).toBeCloseTo(42, 0);
    expect(result.isImprovement).toBe(true);
  });

  it('marks degradation correctly for maximize', () => {
    const formula = parseFormula('KPI-OPS-011 = f(KPI-OPS-016)')!;
    const baseValues = new Map([['KPI-OPS-011', 100], ['KPI-OPS-016', 50]]);
    const overrides = new Map([['KPI-OPS-016', 40]]); // 20% decrease
    const result = runScenario(formula, baseValues, overrides, 'maximize');
    expect(result.delta).toBeLessThan(0);
    expect(result.isImprovement).toBe(false);
  });

  it('marks improvement correctly for minimize', () => {
    const formula = parseFormula('KPI-OPS-011 = f(KPI-OPS-016)')!;
    const baseValues = new Map([['KPI-OPS-011', 100], ['KPI-OPS-016', 50]]);
    const overrides = new Map([['KPI-OPS-016', 40]]); // decrease
    const result = runScenario(formula, baseValues, overrides, 'minimize');
    expect(result.delta).toBeLessThan(0);
    expect(result.isImprovement).toBe(true);
  });

  it('computes driver contributions', () => {
    const formula = parseFormula('KPI-FIN-006 = KPI-FIN-001 + KPI-FIN-004 - KPI-FIN-005')!;
    const baseValues = new Map([
      ['KPI-FIN-006', 38],
      ['KPI-FIN-001', 25],
      ['KPI-FIN-004', 30],
      ['KPI-FIN-005', 17],
    ]);
    const overrides = new Map([['KPI-FIN-001', 20], ['KPI-FIN-005', 20]]);
    const result = runScenario(formula, baseValues, overrides, 'minimize');
    // DSO contribution: 20 - 25 = -5
    // DPO contribution: -(20) - -(17) = -3
    expect(result.driverContributions).toHaveLength(3);
    const dso = result.driverContributions.find((c) => c.kpiId === 'KPI-FIN-001')!;
    expect(dso.contribution).toBe(-5);
    const dpo = result.driverContributions.find((c) => c.kpiId === 'KPI-FIN-005')!;
    expect(dpo.contribution).toBe(-3);
  });
});
