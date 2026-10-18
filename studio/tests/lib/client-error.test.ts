import { describe, expect, it } from 'vitest';
import { apiErrorCode, apiErrorMessage } from '@/lib/api/client-error';

describe('client-error', () => {
  it('reads the standard shape', () => {
    const body = { error: { code: 'CONFLICT', message: 'Stale release.' } };
    expect(apiErrorMessage(body, 'fallback')).toBe('Stale release.');
    expect(apiErrorCode(body)).toBe('CONFLICT');
  });
  it('reads a flat legacy string', () => {
    expect(apiErrorMessage({ error: 'Old text.' }, 'fallback')).toBe('Old text.');
    expect(apiErrorCode({ error: 'Old text.' })).toBeUndefined();
  });
  it.each([null, undefined, {}, { error: {} }, { error: '' }, { error: { message: 42 } }, 'not json'])('falls back for %j', (body) => {
    expect(apiErrorMessage(body, 'fallback')).toBe('fallback');
  });
});
