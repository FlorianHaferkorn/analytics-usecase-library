import { describe, expect, it } from 'vitest';
import { formatReviewDate } from '@/lib/format/review-date';

describe('formatReviewDate', () => {
  it('keeps governed ISO dates stable', () => {
    expect(formatReviewDate('2026-08-27')).toBe('2026-08-27');
  });

  it('normalizes German catalog dates', () => {
    expect(formatReviewDate('27.08.2026')).toBe('2026-08-27');
  });

  it('does not expose invalid browser date output', () => {
    expect(formatReviewDate('31.02.2026')).toBe('—');
    expect(formatReviewDate('not-a-date')).toBe('—');
    expect(formatReviewDate(undefined)).toBe('—');
  });
});
