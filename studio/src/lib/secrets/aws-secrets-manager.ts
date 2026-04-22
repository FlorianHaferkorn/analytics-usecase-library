/**
 * AWS Secrets Manager Adapter.
 *
 * Used when SECRETS_PROVIDER=aws.
 * Requires AWS_REGION env var (defaults to us-east-1).
 * Authentication via standard AWS credential chain.
 *
 * Install: npm install @aws-sdk/client-secrets-manager
 *
 * At build time, @aws-sdk/client-secrets-manager resolves to a stub module
 * (via turbopack.resolveAlias in next.config.ts).  At runtime, the real
 * package is loaded as a server external (serverExternalPackages).
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

export async function getSecretFromAws(name: string): Promise<string> {
  const region = process.env.AWS_REGION ?? 'us-east-1';

  // Type assertions used because @aws-sdk/client-secrets-manager is an
  // optional peer dependency not present in devDependencies.
  const awsModule = await import('@aws-sdk/client-secrets-manager' as string) as {
    SecretsManagerClient: new (cfg: { region: string }) => { send(cmd: any): Promise<{ SecretString?: string }> };
    GetSecretValueCommand: new (params: { SecretId: string }) => any;
  };

  const client = new awsModule.SecretsManagerClient({ region });
  const response = await client.send(new awsModule.GetSecretValueCommand({ SecretId: name }));

  if (response.SecretString) {
    return response.SecretString;
  }

  throw new Error(`Secret "${name}" found in AWS Secrets Manager but has no string value`);
}
