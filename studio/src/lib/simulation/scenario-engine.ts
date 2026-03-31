/**
 * Scenario Engine — Recomputes strategic KPI values given user overrides.
 *
 * For additive formulas: sums adjusted terms.
 * For functional formulas: computes weighted average of % changes.
 */

import type { ParsedFormula, AdditiveFormula, FunctionalFormula } from './formula-parser';

export interface DriverContribution {
  kpiId: string;
  baseValue: number;
  adjustedValue: number;
  contribution: number;
}

export interface ScenarioResult {
  target: string;
  baselineValue: number;
  adjustedValue: number;
  delta: number;
  deltaPercent: number;
  impactDirection: 'maximize' | 'minimize';
  isImprovement: boolean;
  driverContributions: DriverContribution[];
}

function computeAdditive(
  formula: AdditiveFormula,
  baseValues: Map<string, number>,
  overrides: Map<string, number>,
): { adjustedValue: number; contributions: DriverContribution[] } {
  let adjustedValue = 0;
  const contributions: DriverContribution[] = [];

  for (const term of formula.terms) {
    const base = baseValues.get(term.kpiId) ?? 0;
    const adjusted = overrides.get(term.kpiId) ?? base;
    const signed = term.operator === '-' ? -adjusted : adjusted;
    const signedBase = term.operator === '-' ? -base : base;
    adjustedValue += signed;

    contributions.push({
      kpiId: term.kpiId,
      baseValue: base,
      adjustedValue: adjusted,
      contribution: signed - signedBase,
    });
  }

  return { adjustedValue, contributions };
}

function computeFunctional(
  formula: FunctionalFormula,
  baseValues: Map<string, number>,
  overrides: Map<string, number>,
  baselineTarget: number,
): { adjustedValue: number; contributions: DriverContribution[] } {
  const contributions: DriverContribution[] = [];
  let totalPctChange = 0;
  let driverCount = 0;

  for (const driverId of formula.drivers) {
    const base = baseValues.get(driverId) ?? 0;
    const adjusted = overrides.get(driverId) ?? base;
    const pctChange = base !== 0 ? (adjusted - base) / Math.abs(base) : 0;
    totalPctChange += pctChange;
    driverCount++;

    contributions.push({
      kpiId: driverId,
      baseValue: base,
      adjustedValue: adjusted,
      contribution: driverCount > 0 ? (pctChange / (driverCount || 1)) * baselineTarget : 0,
    });
  }

  // Average the % changes across all drivers and apply to baseline
  const avgPctChange = driverCount > 0 ? totalPctChange / driverCount : 0;
  const adjustedValue = baselineTarget * (1 + avgPctChange);

  // Recalculate contributions with final weight
  for (const c of contributions) {
    const pctChange = c.baseValue !== 0 ? (c.adjustedValue - c.baseValue) / Math.abs(c.baseValue) : 0;
    c.contribution = (pctChange / (driverCount || 1)) * baselineTarget;
  }

  return { adjustedValue, contributions };
}

/**
 * Run a scenario simulation given a formula, base values, and user overrides.
 */
export function runScenario(
  formula: ParsedFormula,
  baseValues: Map<string, number>,
  overrides: Map<string, number>,
  impactDirection: 'maximize' | 'minimize' = 'maximize',
): ScenarioResult {
  const baselineValue = baseValues.get(formula.target) ?? 0;

  const { adjustedValue, contributions } = formula.type === 'additive'
    ? computeAdditive(formula, baseValues, overrides)
    : computeFunctional(formula, baseValues, overrides, baselineValue);

  const delta = adjustedValue - baselineValue;
  const deltaPercent = baselineValue !== 0 ? (delta / Math.abs(baselineValue)) * 100 : 0;

  const isImprovement = impactDirection === 'maximize' ? delta > 0 : delta < 0;

  return {
    target: formula.target,
    baselineValue,
    adjustedValue,
    delta,
    deltaPercent,
    impactDirection,
    isImprovement,
    driverContributions: contributions,
  };
}
