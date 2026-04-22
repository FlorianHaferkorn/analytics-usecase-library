/**
 * Azure Key Vault Secrets Adapter.
 *
 * Used when SECRETS_PROVIDER=azure.
 * Requires AZURE_KEY_VAULT_URL env var pointing to your vault endpoint.
 * Authentication via DefaultAzureCredential (managed identity, env vars, CLI).
 *
 * Install: npm install @azure/keyvault-secrets @azure/identity
 *
 * At build time, @azure/keyvault-secrets and @azure/identity resolve to stub
 * modules (via turbopack.resolveAlias in next.config.ts).  At runtime, the
 * real packages are loaded as server externals (serverExternalPackages).
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

export async function getSecretFromAzureKeyVault(name: string): Promise<string> {
  const vaultUrl = process.env.AZURE_KEY_VAULT_URL;
  if (!vaultUrl) {
    throw new Error('AZURE_KEY_VAULT_URL environment variable is required for Azure Key Vault provider');
  }

  // Type assertions used because @azure/* are optional peer dependencies
  // and are not present in devDependencies.
  const kvModule = await import('@azure/keyvault-secrets' as string) as { SecretClient: new (url: string, cred: any) => { getSecret(n: string): Promise<{ value?: string }> } };
  const idModule = await import('@azure/identity' as string) as { DefaultAzureCredential: new () => any };

  const credential = new idModule.DefaultAzureCredential();
  const client = new kvModule.SecretClient(vaultUrl, credential);

  const secret = await client.getSecret(name);
  if (!secret.value) {
    throw new Error(`Secret "${name}" found in Azure Key Vault but has no value`);
  }
  return secret.value;
}
