/**
 * Rule Engine — Evaluates notification rules against KPI values.
 */

import type { NotificationRule, EvaluationResult, RuleCondition } from './rule-types';

function checkCondition(
  condition: RuleCondition,
  value: number,
  threshold: number,
  thresholdUpper?: number,
): boolean {
  switch (condition) {
    case 'lt': return value < threshold;
    case 'gt': return value > threshold;
    case 'eq': return Math.abs(value - threshold) < 0.001;
    case 'between':
      return thresholdUpper !== undefined && value >= threshold && value <= thresholdUpper;
    default: return false;
  }
}

function conditionLabel(condition: RuleCondition, threshold: number, upper?: number): string {
  switch (condition) {
    case 'lt': return `< ${threshold}`;
    case 'gt': return `> ${threshold}`;
    case 'eq': return `= ${threshold}`;
    case 'between': return `between ${threshold} and ${upper ?? '?'}`;
  }
}

/**
 * Evaluate all enabled rules against provided KPI values.
 * Returns triggered notifications only.
 */
export function evaluateRules(
  rules: NotificationRule[],
  kpiValues: Map<string, number>,
): EvaluationResult[] {
  const results: EvaluationResult[] = [];

  for (const rule of rules) {
    if (!rule.enabled) continue;

    const value = kpiValues.get(rule.kpiId);
    if (value === undefined) continue;

    if (checkCondition(rule.condition, value, rule.threshold, rule.thresholdUpper)) {
      results.push({
        ruleId: rule.id,
        ruleName: rule.name,
        kpiId: rule.kpiId,
        kpiValue: value,
        severity: rule.severity,
        spineId: rule.spineId,
        message: `${rule.name}: ${rule.kpiId} is ${value} (${conditionLabel(rule.condition, rule.threshold, rule.thresholdUpper)})`,
      });
    }
  }

  return results;
}
