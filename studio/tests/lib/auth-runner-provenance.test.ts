// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest';

type Token = Record<string, unknown>;
type Callbacks = {
  jwt: (input: { token: Token; user?: { id: string; email?: string }; account?: Record<string, unknown>; trigger?: string; session?: unknown }) => Promise<Token>;
  session: (input: { session: Token; token: Token }) => Token;
};
const capture = vi.hoisted(() => ({ callbacks: null as Callbacks | null }));
vi.mock('next-auth', () => ({ default: vi.fn((options: { callbacks: Callbacks }) => {
  capture.callbacks = options.callbacks;
  return { auth: vi.fn(), handlers: {}, signIn: vi.fn(), signOut: vi.fn() };
}) }));
vi.mock('next-auth/providers/github', () => ({ default: vi.fn() }));
vi.mock('next-auth/providers/credentials', () => ({ default: vi.fn() }));
vi.mock('@/lib/auth/env-check', () => ({ validateAuthEnv: vi.fn() }));
import '@/lib/auth/config';

const identity = { provider: 'github', providerAccountId: '12345', type: 'oauth' };
const provenance = { provider: 'github', providerAccountId: '12345', authenticatedAt: 1000, method: 'oauth' };
describe('server sign-in provenance', () => {
  beforeEach(() => { vi.restoreAllMocks(); });
  it('derives stable provider identity and time from the completed provider sign-in, not user fields', async () => {
    vi.spyOn(Date, 'now').mockReturnValue(1000);
    const token = await capture.callbacks!.jwt({ token: {}, user: { id: 'not-the-provider-id' }, account: identity, trigger: 'signIn' });
    expect(token.authentication).toEqual(provenance);
  });
  it('marks credentials sign-in as credentials even when replacing a former OAuth JWT', async () => {
    const token = await capture.callbacks!.jwt({ token: { authentication: provenance }, user: { id: 'admin@example.com' }, account: { provider: 'credentials', providerAccountId: 'admin@example.com', type: 'credentials' }, trigger: 'signIn' });
    expect(token.authentication).toMatchObject({ provider: 'credentials', method: 'credentials' });
  });
  it('does not upgrade a legacy JWT or refresh its authentication time during reads', async () => {
    expect((await capture.callbacks!.jwt({ token: {} })).authentication).toBeUndefined();
    expect((await capture.callbacks!.jwt({ token: { authentication: provenance } })).authentication).toEqual(provenance);
  });
  it('ignores provenance and account spoofing through session update payloads', async () => {
    const token = await capture.callbacks!.jwt({ token: {}, trigger: 'update', session: { authentication: provenance }, user: { id: 'spoofed' }, account: identity });
    expect(token.authentication).toBeUndefined();
  });
  it('clears a prior provenance if a new sign-in has no verified account record', async () => {
    expect((await capture.callbacks!.jwt({ token: { authentication: provenance }, user: { id: 'new' }, trigger: 'signIn' })).authentication).toBeUndefined();
  });
  it('projects only JWT provenance into the session and removes user supplied provenance from legacy sessions', () => {
    expect(capture.callbacks!.session({ token: { authentication: provenance }, session: { authentication: { provider: 'fake' } } }).authentication).toEqual(provenance);
    expect(capture.callbacks!.session({ token: {}, session: { authentication: provenance } }).authentication).toBeUndefined();
  });
});
