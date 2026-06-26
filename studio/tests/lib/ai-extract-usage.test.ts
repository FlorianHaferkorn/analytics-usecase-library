import { describe, it, expect } from 'vitest';
import { extractUsage } from '@/lib/ai/telemetry';

describe('extractUsage (tolerant of AI SDK usage naming drift)', () => {
  it('reads v5-style inputTokens/outputTokens', () => {
    expect(extractUsage({ inputTokens: 100, outputTokens: 50 })).toMatchObject({ inputTokens: 100, outputTokens: 50 });
  });

  it('falls back to prompt/completionTokens', () => {
    expect(extractUsage({ promptTokens: 30, completionTokens: 20 })).toMatchObject({ inputTokens: 30, outputTokens: 20 });
  });

  it('extracts cache + reasoning details from either shape', () => {
    const u = extractUsage({
      inputTokens: 10, outputTokens: 5,
      inputTokenDetails: { cacheReadTokens: 7, cacheWriteTokens: 3 },
      outputTokenDetails: { reasoningTokens: 2 },
    });
    expect(u.cacheReadTokens).toBe(7);
    expect(u.cacheWriteTokens).toBe(3);
    expect(u.reasoningTokens).toBe(2);
  });

  it('defaults to 0 tokens for undefined/empty usage (never NaN)', () => {
    expect(extractUsage(undefined)).toMatchObject({ inputTokens: 0, outputTokens: 0 });
    expect(extractUsage({})).toMatchObject({ inputTokens: 0, outputTokens: 0 });
  });
});
