/**
 * Tests for Scenario Engine.
 */

import { describe, it, expect } from 'vitest';
import { parseFormula } from '../../src/lib/simulation/formula-parser';
import { runScenario } from '../../src/lib/simulation/scenario-engine';

describe('runScenario', () => {
  it('returns zero delta when no overrides', () => {
    const formula = parseFormula('wc.ccc.days = wc.dso.days + wc.dio.days - wc.dpo.days')!;
    const baseValues = new Map([
      ['wc.ccc.days', 38],
      ['wc.dso.days', 25],
      ['wc.dio.days', 30],
      ['wc.dpo.days', 17],
    ]);
    const result = runScenario(formula, baseValues, new Map(), 'minimize');
    expect(result.delta).toBe(0);
    expect(result.adjustedValue).toBe(38);
  });

  it('recalculates additive formula with overrides', () => {
    const formula = parseFormula('wc.ccc.days = wc.dso.days + wc.dio.days - wc.dpo.days')!;
    const baseValues = new Map([
      ['wc.ccc.days', 38],
      ['wc.dso.days', 25],
      ['wc.dio.days', 30],
      ['wc.dpo.days', 17],
    ]);
    // Reduce DSO from 25 to 20
    const overrides = new Map([['wc.dso.days', 20]]);
    const result = runScenario(formula, baseValues, overrides, 'minimize');
    // 20 + 30 - 17 = 33
    expect(result.adjustedValue).toBe(33);
    expect(result.delta).toBe(-5);
    expect(result.isImprovement).toBe(true); // minimize: negative delta = improvement
  });

  it('handles functional formula with overrides', () => {
    const formula = parseFormula('margin.gm.pct = f(sales.a, sales.b)')!;
    const baseValues = new Map([
      ['margin.gm.pct', 40],
      ['sales.a', 100],
      ['sales.b', 200],
    ]);
    // Increase sales.a by 10% (100 → 110)
    const overrides = new Map([['sales.a', 110]]);
    const result = runScenario(formula, baseValues, overrides, 'maximize');
    // 10% increase in one of 2 drivers → 5% avg → 40 * 1.05 = 42
    expect(result.adjustedValue).toBeCloseTo(42, 0);
    expect(result.isImprovement).toBe(true);
  });

  it('marks degradation correctly for maximize', () => {
    const formula = parseFormula('a.b = f(c.d)')!;
    const baseValues = new Map([['a.b', 100], ['c.d', 50]]);
    const overrides = new Map([['c.d', 40]]); // 20% decrease
    const result = runScenario(formula, baseValues, overrides, 'maximize');
    expect(result.delta).toBeLessThan(0);
    expect(result.isImprovement).toBe(false);
  });

  it('marks improvement correctly for minimize', () => {
    const formula = parseFormula('a.b = f(c.d)')!;
    const baseValues = new Map([['a.b', 100], ['c.d', 50]]);
    const overrides = new Map([['c.d', 40]]); // decrease
    const result = runScenario(formula, baseValues, overrides, 'minimize');
    expect(result.delta).toBeLessThan(0);
    expect(result.isImprovement).toBe(true);
  });

  it('computes driver contributions', () => {
    const formula = parseFormula('wc.ccc.days = wc.dso.days + wc.dio.days - wc.dpo.days')!;
    const baseValues = new Map([
      ['wc.ccc.days', 38],
      ['wc.dso.days', 25],
      ['wc.dio.days', 30],
      ['wc.dpo.days', 17],
    ]);
    const overrides = new Map([['wc.dso.days', 20], ['wc.dpo.days', 20]]);
    const result = runScenario(formula, baseValues, overrides, 'minimize');
    // DSO contribution: 20 - 25 = -5
    // DPO contribution: -(20) - -(17) = -3
    expect(result.driverContributions).toHaveLength(3);
    const dso = result.driverContributions.find((c) => c.kpiId === 'wc.dso.days')!;
    expect(dso.contribution).toBe(-5);
    const dpo = result.driverContributions.find((c) => c.kpiId === 'wc.dpo.days')!;
    expect(dpo.contribution).toBe(-3);
  });
});
