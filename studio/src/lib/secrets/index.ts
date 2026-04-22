/**
 * Secrets Manager — provider-agnostic secret lookup.
 *
 * Selection is driven by the SECRETS_PROVIDER environment variable:
 *   env    → process.env (default, local dev)
 *   azure  → Azure Key Vault (requires AZURE_KEY_VAULT_URL + @azure packages)
 *   aws    → AWS Secrets Manager (requires AWS_REGION + @aws-sdk packages)
 *
 * Usage:
 *   import { getSecret } from '@/lib/secrets';
 *   const key = await getSecret('ANTHROPIC_API_KEY');
 *
 * Cloud adapter modules (@azure/*, @aws-sdk/*) are loaded dynamically so they
 * are NOT included in the production bundle when using the env adapter.
 */

export type SecretsProvider = 'env' | 'azure' | 'aws';

function resolveProvider(): SecretsProvider {
  const raw = (process.env.SECRETS_PROVIDER ?? 'env').toLowerCase();
  if (raw === 'azure' || raw === 'aws' || raw === 'env') return raw as SecretsProvider;
  throw new Error(
    `Unknown SECRETS_PROVIDER="${raw}". Valid values: env | azure | aws`,
  );
}

/**
 * Retrieve a secret by name from the configured secrets provider.
 * Throws if the secret is missing or the provider is misconfigured.
 */
export async function getSecret(name: string): Promise<string> {
  const provider = resolveProvider();

  switch (provider) {
    case 'env': {
      const { getSecretFromEnv } = await import('./dev-env');
      return getSecretFromEnv(name);
    }
    case 'azure': {
      const { getSecretFromAzureKeyVault } = await import('./azure-key-vault');
      return getSecretFromAzureKeyVault(name);
    }
    case 'aws': {
      const { getSecretFromAws } = await import('./aws-secrets-manager');
      return getSecretFromAws(name);
    }
  }
}
