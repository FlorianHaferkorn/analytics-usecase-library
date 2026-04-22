/**
 * Tests for Auth Session Helper and Environment Validation.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

/* ------------------------------------------------------------------ */
/* env-check tests                                                    */
/* ------------------------------------------------------------------ */

describe('validateAuthEnv', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
    vi.restoreAllMocks();
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  async function loadModule() {
    // Re-import to re-execute the module-level call
    vi.resetModules();
    return import('@/lib/auth/env-check');
  }

  function setNodeEnv(value: string) {
    (process.env as Record<string, string>).NODE_ENV = value;
  }

  it('warns when AUTH_SECRET is missing in development', async () => {
    delete process.env.AUTH_SECRET;
    delete process.env.NEXTAUTH_SECRET;
    setNodeEnv('development');
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const mod = await loadModule();
    mod.validateAuthEnv();
    expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining('AUTH_SECRET not set'));
  });

  it('throws when AUTH_SECRET is missing in production', async () => {
    delete process.env.AUTH_SECRET;
    delete process.env.NEXTAUTH_SECRET;
    setNodeEnv('production');
    const mod = await loadModule();
    expect(() => mod.validateAuthEnv()).toThrow('AUTH_SECRET is required in production');
  });

  it('throws when AUTH_SECRET is a placeholder in production', async () => {
    process.env.AUTH_SECRET = 'changeme';
    setNodeEnv('production');
    const mod = await loadModule();
    expect(() => mod.validateAuthEnv()).toThrow('placeholder');
  });

  it('warns when AUTH_SECRET is a placeholder in development', async () => {
    process.env.AUTH_SECRET = 'changeme';
    setNodeEnv('development');
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const mod = await loadModule();
    mod.validateAuthEnv();
    expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining('placeholder'));
  });

  it('accepts a valid secret without warnings or errors', async () => {
    process.env.AUTH_SECRET = 'a-real-secret-that-is-secure-enough-1234';
    setNodeEnv('production');
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const mod = await loadModule();
    expect(() => mod.validateAuthEnv()).not.toThrow();
    expect(warnSpy).not.toHaveBeenCalled();
  });
});

/* ------------------------------------------------------------------ */
/* session helper tests                                                */
/* ------------------------------------------------------------------ */

// Mock the auth config before importing session helper
vi.mock('@/lib/auth/config', () => ({
  auth: vi.fn(),
}));

import { afterAll } from 'vitest';
import { getSessionUser, requireAuth } from '@/lib/auth/session';
import { auth } from '@/lib/auth/config';

type AuthReturn = Awaited<ReturnType<typeof auth>>;
const mockAuth = vi.mocked(auth);

describe('getSessionUser', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns user when session is valid', async () => {
    mockAuth.mockResolvedValue({
      user: { id: 'user-1', email: 'test@example.com', name: 'Test User' },
      expires: '',
    } as unknown as AuthReturn);

    const user = await getSessionUser();
    expect(user).toEqual({ id: 'user-1', email: 'test@example.com', name: 'Test User' });
  });

  it('returns null when no session exists', async () => {
    mockAuth.mockResolvedValue(null as unknown as AuthReturn);
    const user = await getSessionUser();
    expect(user).toBeNull();
  });

  it('returns null when session has no email', async () => {
    mockAuth.mockResolvedValue({
      user: { id: 'user-1' },
      expires: '',
    } as unknown as AuthReturn);

    const user = await getSessionUser();
    expect(user).toBeNull();
  });
});

describe('requireAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns user tuple when authenticated', async () => {
    mockAuth.mockResolvedValue({
      user: { id: 'user-1', email: 'admin@co.com', name: 'Admin' },
      expires: '',
    } as unknown as AuthReturn);

    const [user, error] = await requireAuth();
    expect(user).toEqual({ id: 'user-1', email: 'admin@co.com', name: 'Admin' });
    expect(error).toBeNull();
  });

  it('returns 401 response when not authenticated', async () => {
    mockAuth.mockResolvedValue(null as unknown as AuthReturn);

    const [user, error] = await requireAuth();
    expect(user).toBeNull();
    expect(error).toBeInstanceOf(Response);
    expect(error!.status).toBe(401);
  });
});
