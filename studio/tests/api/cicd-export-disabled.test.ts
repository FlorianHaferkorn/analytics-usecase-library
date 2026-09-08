import { describe, expect, it } from 'vitest';

import { POST } from '@/app/api/export/cicd/route';

describe('legacy CI/CD export route', () => {
  it('does not invent deployment workflows outside the governed target core', async () => {
    const response = await POST();
    const body = await response.json();

    expect(response.status).toBe(410);
    expect(body.error.code).toBe('UNSUPPORTED');
    expect(body.error.message).toContain('official vendor CLI');
  });
});
