/**
 * Tenant gate: the 403 for a foreign project uses the standard error shape
 * { error: { code, message } } that every other API error uses.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';

const authMock = vi.fn();
vi.mock('@/lib/auth/config', () => ({ auth: () => authMock() }));

import { enforceProjectAccess, projectAccessDeniedResponse } from '@/lib/auth/enforce-project-access';

describe('enforce-project-access', () => {
  beforeEach(() => authMock.mockReset());

  it('projectAccessDeniedResponse returns 403 in the standard error shape', async () => {
    const res = projectAccessDeniedResponse();
    expect(res.status).toBe(403);
    expect(await res.json()).toEqual({
      error: { code: 'PROJECT_ACCESS_DENIED', message: 'You are not a member of this project.' },
    });
  });

  it('denies a signed-in user who is not a member of the project', async () => {
    authMock.mockResolvedValue({
      user: { email: 'a@example.test' },
      project_memberships: [{ projectId: 'p-1', role: 'viewer' }],
    });
    const res = await enforceProjectAccess('p-2');
    expect(res?.status).toBe(403);
    expect((await res!.json()).error.code).toBe('PROJECT_ACCESS_DENIED');
  });

  it('lets a member through and leaves the no-session case to the handler', async () => {
    authMock.mockResolvedValue({
      user: { email: 'a@example.test' },
      project_memberships: [{ projectId: 'p-1', role: 'viewer' }],
    });
    expect(await enforceProjectAccess('p-1')).toBeNull();
    authMock.mockResolvedValue(null);
    expect(await enforceProjectAccess('p-2')).toBeNull();
  });
});
