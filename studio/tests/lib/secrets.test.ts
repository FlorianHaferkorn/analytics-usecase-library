/**
 * Tests for the Secrets Manager adapters.
 *
 * The env adapter has no external dependencies and is tested directly.
 * The Azure and AWS adapters are tested with vi.doMock stubs.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

/* ===================================================================== */
/* dev-env adapter                                                        */
/* ===================================================================== */

describe('getSecretFromEnv', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
    vi.resetModules();
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('returns the env var value when present', async () => {
    process.env.MY_TEST_SECRET = 'super-secret-value';
    const { getSecretFromEnv } = await import('@/lib/secrets/dev-env');
    const result = await getSecretFromEnv('MY_TEST_SECRET');
    expect(result).toBe('super-secret-value');
  });

  it('throws when the env var is missing', async () => {
    delete process.env.MISSING_SECRET;
    const { getSecretFromEnv } = await import('@/lib/secrets/dev-env');
    await expect(getSecretFromEnv('MISSING_SECRET')).rejects.toThrow(
      'Secret "MISSING_SECRET" not found in environment variables',
    );
  });
});

/* ===================================================================== */
/* secrets/index.ts — provider selection                                 */
/* ===================================================================== */

describe('getSecret (index)', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
    vi.resetModules();
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('uses env adapter when SECRETS_PROVIDER=env (default)', async () => {
    process.env.SECRETS_PROVIDER = 'env';
    process.env.MY_API_KEY = 'env-key-value';
    const { getSecret } = await import('@/lib/secrets/index');
    const result = await getSecret('MY_API_KEY');
    expect(result).toBe('env-key-value');
  });

  it('uses env adapter when SECRETS_PROVIDER is unset', async () => {
    delete process.env.SECRETS_PROVIDER;
    process.env.FALLBACK_KEY = 'fallback-value';
    const { getSecret } = await import('@/lib/secrets/index');
    const result = await getSecret('FALLBACK_KEY');
    expect(result).toBe('fallback-value');
  });

  it('throws for an unknown SECRETS_PROVIDER value', async () => {
    process.env.SECRETS_PROVIDER = 'vault';
    const { getSecret } = await import('@/lib/secrets/index');
    await expect(getSecret('SOME_KEY')).rejects.toThrow('Unknown SECRETS_PROVIDER');
  });
});

/* ===================================================================== */
/* azure-key-vault adapter — env guard only (no real Azure SDK)          */
/* ===================================================================== */

describe('getSecretFromAzureKeyVault — env guard', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
    vi.resetModules();
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('throws when AZURE_KEY_VAULT_URL is not set', async () => {
    delete process.env.AZURE_KEY_VAULT_URL;
    const { getSecretFromAzureKeyVault } = await import('@/lib/secrets/azure-key-vault');
    await expect(getSecretFromAzureKeyVault('MY_KEY')).rejects.toThrow(
      'AZURE_KEY_VAULT_URL',
    );
  });
});

/* ===================================================================== */
/* azure-key-vault adapter — mocked via module mock                      */
/* ===================================================================== */

describe('getSecretFromAzureKeyVault (mocked)', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
    vi.resetModules();
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('returns the secret value when vault responds successfully', async () => {
    process.env.AZURE_KEY_VAULT_URL = 'https://my-vault.vault.azure.net/';

    // Mock the entire azure-key-vault adapter to return a controlled value.
    vi.doMock('@/lib/secrets/azure-key-vault', () => ({
      getSecretFromAzureKeyVault: vi.fn().mockResolvedValue('azure-secret-value'),
    }));

    const { getSecretFromAzureKeyVault } = await import('@/lib/secrets/azure-key-vault');
    const result = await getSecretFromAzureKeyVault('MY_KEY');
    expect(result).toBe('azure-secret-value');
  });

  it('throws when vault returns an error', async () => {
    process.env.AZURE_KEY_VAULT_URL = 'https://my-vault.vault.azure.net/';

    vi.doMock('@/lib/secrets/azure-key-vault', () => ({
      getSecretFromAzureKeyVault: vi.fn().mockRejectedValue(new Error('has no value')),
    }));

    const { getSecretFromAzureKeyVault } = await import('@/lib/secrets/azure-key-vault');
    await expect(getSecretFromAzureKeyVault('EMPTY_KEY')).rejects.toThrow('has no value');
  });
});

/* ===================================================================== */
/* aws-secrets-manager adapter — mocked via module mock                  */
/* ===================================================================== */

describe('getSecretFromAws (mocked)', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
    vi.resetModules();
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('returns the secret string value', async () => {
    process.env.AWS_REGION = 'eu-west-1';

    vi.doMock('@/lib/secrets/aws-secrets-manager', () => ({
      getSecretFromAws: vi.fn().mockResolvedValue('aws-secret-value'),
    }));

    const { getSecretFromAws } = await import('@/lib/secrets/aws-secrets-manager');
    const result = await getSecretFromAws('MY_AWS_KEY');
    expect(result).toBe('aws-secret-value');
  });

  it('throws when SecretString is absent', async () => {
    process.env.AWS_REGION = 'eu-west-1';

    vi.doMock('@/lib/secrets/aws-secrets-manager', () => ({
      getSecretFromAws: vi.fn().mockRejectedValue(new Error('no string value')),
    }));

    const { getSecretFromAws } = await import('@/lib/secrets/aws-secrets-manager');
    await expect(getSecretFromAws('BIN_KEY')).rejects.toThrow('no string value');
  });
});
