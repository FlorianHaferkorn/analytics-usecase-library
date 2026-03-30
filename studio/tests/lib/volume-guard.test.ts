/**
 * Tests for Volume Guard.
 */

import { describe, it, expect } from 'vitest';
import { isSignificantVolume } from '@/lib/notifications/volume-guard';

describe('volume-guard', () => {
  it('suppresses count below threshold', () => {
    expect(isSignificantVolume('orders.count', 3)).toBe(false);
  });

  it('passes count above threshold', () => {
    expect(isSignificantVolume('orders.count', 15)).toBe(true);
  });

  it('suppresses amount below threshold', () => {
    expect(isSignificantVolume('revenue.amount', 50)).toBe(false);
  });

  it('passes amount above threshold', () => {
    expect(isSignificantVolume('revenue.amount', 500)).toBe(true);
  });

  it('respects custom threshold', () => {
    expect(isSignificantVolume('any.kpi', 5, 10)).toBe(false);
    expect(isSignificantVolume('any.kpi', 15, 10)).toBe(true);
  });

  it('defaults to any non-zero value for unknown types', () => {
    expect(isSignificantVolume('margin.gm.pct', 0)).toBe(false);
    expect(isSignificantVolume('margin.gm.pct', 0.1)).toBe(true);
  });
});
