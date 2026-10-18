/**
 * A stale head gets its own code, so the client can tell "saved elsewhere meanwhile"
 * apart from other conflicts that also answer 409.
 */

import { describe, expect, it } from 'vitest';
import { packageRepositoryError } from '@/lib/project-package/http';

async function errorOf(response: Response) {
  return { status: response.status, ...(await response.json()).error };
}

describe('packageRepositoryError', () => {
  it('maps stale_head to 409 STALE_REVISION', async () => {
    expect(await errorOf(packageRepositoryError({ available: true, ok: false, status: 409, code: 'stale_head', error: 'expected HEAD does not match' })))
      .toEqual({ status: 409, code: 'STALE_REVISION', message: 'expected HEAD does not match' });
  });

  it('keeps other conflicts as 409 CONFLICT', async () => {
    expect(await errorOf(packageRepositoryError({ available: true, ok: false, status: 409, error: 'Package already exists' })))
      .toMatchObject({ status: 409, code: 'CONFLICT' });
    expect(await errorOf(packageRepositoryError({ available: true, ok: false, error: 'Revision already exists' })))
      .toMatchObject({ status: 409, code: 'CONFLICT' });
  });
});
