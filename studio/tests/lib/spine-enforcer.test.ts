/**
 * Tests for Spine Enforcer.
 */

import { describe, it, expect } from 'vitest';
import { validateAgainstSpine } from '@/lib/governance/spine-enforcer';
import type { SpineRule } from '@/lib/governance/spine-enforcer';

describe('spine-enforcer', () => {
  const spineRules: SpineRule[] = [
    { kpi_id: 'KPI-COM-013', severity: 'RequiredIntervention', threshold: 30, condition: 'lt' },
    { kpi_id: 'cash.dso.days', severity: 'EarlyWarning', threshold: 45, condition: 'gt' },
  ];

  it('returns no violations when rules match', () => {
    const bracketRules = [
      { kpiId: 'KPI-COM-013', condition: 'lt', threshold: 30, severity: 'RequiredIntervention' },
      { kpiId: 'cash.dso.days', condition: 'gt', threshold: 45, severity: 'EarlyWarning' },
    ];
    const violations = validateAgainstSpine(bracketRules, spineRules);
    expect(violations).toHaveLength(0);
  });

  it('detects missing rules', () => {
    const violations = validateAgainstSpine([], spineRules);
    expect(violations).toHaveLength(2);
    expect(violations[0].message).toContain('Missing notification rule');
  });

  it('detects condition mismatch', () => {
    const bracketRules = [
      { kpiId: 'KPI-COM-013', condition: 'gt', threshold: 30, severity: 'RequiredIntervention' },
      { kpiId: 'cash.dso.days', condition: 'gt', threshold: 45, severity: 'EarlyWarning' },
    ];
    const violations = validateAgainstSpine(bracketRules, spineRules);
    expect(violations).toHaveLength(1);
    expect(violations[0].message).toContain('Condition mismatch');
  });

  it('detects severity mismatch', () => {
    const bracketRules = [
      { kpiId: 'KPI-COM-013', condition: 'lt', threshold: 30, severity: 'EarlyWarning' },
      { kpiId: 'cash.dso.days', condition: 'gt', threshold: 45, severity: 'EarlyWarning' },
    ];
    const violations = validateAgainstSpine(bracketRules, spineRules);
    expect(violations).toHaveLength(1);
    expect(violations[0].message).toContain('Severity mismatch');
  });

  it('handles empty spine gracefully', () => {
    const violations = validateAgainstSpine([{ kpiId: 'x', condition: 'lt', threshold: 1, severity: 'EarlyWarning' }], []);
    expect(violations).toHaveLength(0);
  });

  it('returns kpiId in violations', () => {
    const violations = validateAgainstSpine([], spineRules);
    expect(violations[0].kpiId).toBe('KPI-COM-013');
  });
});
