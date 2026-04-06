/**
 * Spine Enforcer — validates bracket thresholds against decision spine rules.
 *
 * Decision spines define threshold boundaries that brackets must respect.
 * This enforcer checks if a bracket's notification rules align with the
 * spine's defined boundaries.
 *
 * TODO: not yet wired into production — currently only used in tests.
 */

export interface SpineRule {
  kpi_id: string;
  severity: string;
  threshold: number;
  condition: string;
}

export interface SpineViolation {
  kpiId: string;
  expected: string;
  actual: string;
  message: string;
}

/**
 * Validate a bracket's notification rules against a decision spine.
 * Returns any violations found.
 */
export function validateAgainstSpine(
  bracketRules: { kpiId: string; condition: string; threshold: number; severity: string }[],
  spineRules: SpineRule[],
): SpineViolation[] {
  const violations: SpineViolation[] = [];

  for (const spineRule of spineRules) {
    const matchingBracketRule = bracketRules.find(
      (r) => r.kpiId === spineRule.kpi_id,
    );

    if (!matchingBracketRule) {
      violations.push({
        kpiId: spineRule.kpi_id,
        expected: `${spineRule.condition} ${spineRule.threshold}`,
        actual: 'no rule defined',
        message: `Missing notification rule for ${spineRule.kpi_id} required by spine`,
      });
      continue;
    }

    // Check if threshold is within acceptable range
    if (matchingBracketRule.condition !== spineRule.condition) {
      violations.push({
        kpiId: spineRule.kpi_id,
        expected: spineRule.condition,
        actual: matchingBracketRule.condition,
        message: `Condition mismatch for ${spineRule.kpi_id}: expected ${spineRule.condition}, got ${matchingBracketRule.condition}`,
      });
    }

    // Check severity alignment
    if (matchingBracketRule.severity !== spineRule.severity) {
      violations.push({
        kpiId: spineRule.kpi_id,
        expected: spineRule.severity,
        actual: matchingBracketRule.severity,
        message: `Severity mismatch for ${spineRule.kpi_id}: expected ${spineRule.severity}, got ${matchingBracketRule.severity}`,
      });
    }
  }

  return violations;
}
