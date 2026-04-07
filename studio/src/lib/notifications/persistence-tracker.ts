/**
 * Persistence Tracker — requires N consecutive violations before firing.
 *
 * Action codes typically require 2+ consecutive periods below threshold
 * to trigger. This prevents false alarms from single-period fluctuations.
 *
 * TODO: not yet wired into production — currently only used in tests.
 */

export interface PersistenceState {
  /** Number of consecutive periods the rule has been violated. */
  consecutiveCount: number;
  /** Timestamp of the first violation in this streak. */
  streakStart: string | null;
}

const state = new Map<string, PersistenceState>();

/**
 * Record a violation for a rule. Returns true if the violation
 * has persisted long enough to fire.
 */
export function recordViolation(
  ruleId: string,
  requiredConsecutive = 2,
): boolean {
  const current = state.get(ruleId) ?? { consecutiveCount: 0, streakStart: null };
  current.consecutiveCount += 1;
  if (!current.streakStart) {
    current.streakStart = new Date().toISOString();
  }
  state.set(ruleId, current);
  return current.consecutiveCount >= requiredConsecutive;
}

/** Reset a rule's violation streak (called when rule passes). */
export function resetViolation(ruleId: string): void {
  state.delete(ruleId);
}

/** Get current persistence state for a rule. */
export function getViolationState(ruleId: string): PersistenceState {
  return state.get(ruleId) ?? { consecutiveCount: 0, streakStart: null };
}

/** Clear all state (for testing). */
export function clearAllState(): void {
  state.clear();
}
