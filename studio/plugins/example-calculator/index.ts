/**
 * Example Calculator Plugin — Demonstrates the plugin SDK.
 *
 * Provides a simple percentage-of-total calculator for KPI values.
 */

export interface CalculatorInput {
  value: number;
  total: number;
}

export interface CalculatorOutput {
  percentage: number;
  formatted: string;
}

/** Calculate a value as a percentage of a total. */
export function calculatePercentage(input: CalculatorInput): CalculatorOutput {
  if (input.total === 0) {
    return { percentage: 0, formatted: '0.0%' };
  }
  const percentage = (input.value / input.total) * 100;
  return {
    percentage: Math.round(percentage * 10) / 10,
    formatted: `${(Math.round(percentage * 10) / 10).toFixed(1)}%`,
  };
}

/** Hook handler for onKpiEvaluate — enriches KPI data with percentage calculations. */
export function onKpiEvaluate(data: unknown): void {
  const record = data as Record<string, unknown>;
  if (typeof record.value === 'number' && typeof record.total === 'number') {
    const result = calculatePercentage({ value: record.value, total: record.total });
    record.percentage = result.percentage;
    record.percentageFormatted = result.formatted;
  }
}
