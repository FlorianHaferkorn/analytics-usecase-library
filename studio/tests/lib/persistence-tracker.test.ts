/**
 * Tests for Persistence Tracker.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  recordViolation,
  resetViolation,
  getViolationState,
  clearAllState,
} from '@/lib/notifications/persistence-tracker';

describe('persistence-tracker', () => {
  beforeEach(() => {
    clearAllState();
  });

  it('does not fire on single violation (default requires 2)', () => {
    const shouldFire = recordViolation('rule-1');
    expect(shouldFire).toBe(false);
    expect(getViolationState('rule-1').consecutiveCount).toBe(1);
  });

  it('fires after 2 consecutive violations', () => {
    recordViolation('rule-1');
    const shouldFire = recordViolation('rule-1');
    expect(shouldFire).toBe(true);
    expect(getViolationState('rule-1').consecutiveCount).toBe(2);
  });

  it('fires after custom consecutive count', () => {
    expect(recordViolation('rule-1', 3)).toBe(false);
    expect(recordViolation('rule-1', 3)).toBe(false);
    expect(recordViolation('rule-1', 3)).toBe(true);
  });

  it('resets streak on recovery', () => {
    recordViolation('rule-1');
    recordViolation('rule-1');
    resetViolation('rule-1');
    expect(getViolationState('rule-1').consecutiveCount).toBe(0);
    expect(recordViolation('rule-1')).toBe(false);
  });

  it('tracks separate rules independently', () => {
    recordViolation('rule-1');
    recordViolation('rule-2');
    recordViolation('rule-2');
    expect(getViolationState('rule-1').consecutiveCount).toBe(1);
    expect(getViolationState('rule-2').consecutiveCount).toBe(2);
  });

  it('sets streakStart on first violation', () => {
    recordViolation('rule-1');
    const state = getViolationState('rule-1');
    expect(state.streakStart).toBeTruthy();
  });
});
