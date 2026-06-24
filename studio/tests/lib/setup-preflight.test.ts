import { describe, it, expect } from 'vitest';
import {
  computeSetupReadiness,
  detectLlmProvider,
  llmKeyCheck,
  secretsProviderCheck,
  authCheck,
  type SetupCheck,
} from '@/lib/setup/preflight';

const ok = (key: SetupCheck['key'], required = true): SetupCheck => ({ key, label: key, status: 'ok', detail: '', required });

describe('computeSetupReadiness', () => {
  it('is ready when every required check is ok', () => {
    const r = computeSetupReadiness([ok('llm_key'), ok('python_bridge'), ok('auth', false)]);
    expect(r.ready).toBe(true);
    expect(r.blockers).toEqual([]);
  });

  it('is blocked (and names the blocker) when a required check is missing', () => {
    const r = computeSetupReadiness([
      { key: 'llm_key', label: 'LLM-Key (BYO)', status: 'missing', detail: '', required: true },
      ok('python_bridge'),
    ]);
    expect(r.ready).toBe(false);
    expect(r.blockers).toEqual(['LLM-Key (BYO)']);
  });

  it('a missing OPTIONAL check does not block', () => {
    const r = computeSetupReadiness([
      ok('python_bridge'),
      { key: 'auth', label: 'Auth', status: 'warn', detail: '', required: false },
    ]);
    expect(r.ready).toBe(true);
  });
});

describe('detectLlmProvider (BYO key)', () => {
  it('prioritises Google → Anthropic → OpenAI', () => {
    expect(detectLlmProvider({ GOOGLE_API_KEY: 'x', ANTHROPIC_API_KEY: 'y' })).toBe('google');
    expect(detectLlmProvider({ ANTHROPIC_API_KEY: 'y', OPENAI_API_KEY: 'z' })).toBe('anthropic');
    expect(detectLlmProvider({ OPENAI_API_KEY: 'z' })).toBe('openai');
    expect(detectLlmProvider({})).toBeNull();
  });

  it('llmKeyCheck is missing+required with no key, ok with one', () => {
    expect(llmKeyCheck({})).toMatchObject({ status: 'missing', required: true });
    expect(llmKeyCheck({ ANTHROPIC_API_KEY: 'y' }).status).toBe('ok');
  });
});

describe('secretsProviderCheck', () => {
  it('defaults to env (ok) and rejects an unknown provider', () => {
    expect(secretsProviderCheck({}).status).toBe('ok');
    expect(secretsProviderCheck({ SECRETS_PROVIDER: 'azure' }).status).toBe('ok');
    expect(secretsProviderCheck({ SECRETS_PROVIDER: 'vault' }).status).toBe('missing');
  });
});

describe('authCheck', () => {
  it('warns (non-blocking) on dev-credentials, ok with GitHub OAuth', () => {
    expect(authCheck({})).toMatchObject({ status: 'warn', required: false });
    expect(authCheck({ GITHUB_ID: 'a', GITHUB_SECRET: 'b' }).status).toBe('ok');
  });
});
