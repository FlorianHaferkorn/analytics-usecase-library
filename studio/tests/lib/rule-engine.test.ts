/**
 * Tests for Notification Rule Engine.
 */

import { describe, it, expect } from 'vitest';
import { evaluateRules } from '../../src/lib/notifications/rule-engine';
import type { NotificationRule } from '../../src/lib/notifications/rule-types';

function makeRule(overrides: Partial<NotificationRule> = {}): NotificationRule {
  return {
    id: 'rule-1',
    projectId: 'default',
    name: 'Test Rule',
    kpiId: 'margin.gm.pct',
    condition: 'lt',
    threshold: 40,
    severity: 'EarlyWarning',
    enabled: true,
    createdAt: new Date().toISOString(),
    ...overrides,
  };
}

describe('evaluateRules', () => {
  it('triggers when value is less than threshold (lt)', () => {
    const rules = [makeRule({ condition: 'lt', threshold: 40 })];
    const values = new Map([['margin.gm.pct', 35]]);
    const results = evaluateRules(rules, values);
    expect(results).toHaveLength(1);
    expect(results[0].kpiValue).toBe(35);
    expect(results[0].severity).toBe('EarlyWarning');
  });

  it('does not trigger when value is above threshold (lt)', () => {
    const rules = [makeRule({ condition: 'lt', threshold: 40 })];
    const values = new Map([['margin.gm.pct', 45]]);
    expect(evaluateRules(rules, values)).toHaveLength(0);
  });

  it('triggers when value is greater than threshold (gt)', () => {
    const rules = [makeRule({ condition: 'gt', threshold: 100 })];
    const values = new Map([['margin.gm.pct', 120]]);
    expect(evaluateRules(rules, values)).toHaveLength(1);
  });

  it('triggers when value equals threshold (eq)', () => {
    const rules = [makeRule({ condition: 'eq', threshold: 50 })];
    const values = new Map([['margin.gm.pct', 50]]);
    expect(evaluateRules(rules, values)).toHaveLength(1);
  });

  it('triggers when value is between thresholds', () => {
    const rules = [makeRule({ condition: 'between', threshold: 30, thresholdUpper: 40 })];
    const values = new Map([['margin.gm.pct', 35]]);
    expect(evaluateRules(rules, values)).toHaveLength(1);
  });

  it('skips disabled rules', () => {
    const rules = [makeRule({ enabled: false })];
    const values = new Map([['margin.gm.pct', 35]]);
    expect(evaluateRules(rules, values)).toHaveLength(0);
  });

  it('skips rules for missing KPI values', () => {
    const rules = [makeRule({ kpiId: 'nonexistent.kpi' })];
    const values = new Map([['margin.gm.pct', 35]]);
    expect(evaluateRules(rules, values)).toHaveLength(0);
  });

  it('evaluates multiple rules and returns all triggered', () => {
    const rules = [
      makeRule({ id: 'r1', name: 'Low margin', kpiId: 'margin.gm.pct', condition: 'lt', threshold: 40 }),
      makeRule({ id: 'r2', name: 'High CCC', kpiId: 'wc.ccc.days', condition: 'gt', threshold: 35, severity: 'RequiredIntervention' }),
      makeRule({ id: 'r3', name: 'Safe OEE', kpiId: 'ops.oee.pct', condition: 'gt', threshold: 90 }),
    ];
    const values = new Map([
      ['margin.gm.pct', 38],
      ['wc.ccc.days', 42],
      ['ops.oee.pct', 76],
    ]);
    const results = evaluateRules(rules, values);
    expect(results).toHaveLength(2);
    expect(results[0].ruleId).toBe('r1');
    expect(results[1].ruleId).toBe('r2');
    expect(results[1].severity).toBe('RequiredIntervention');
  });
});
