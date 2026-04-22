/**
 * Dev/Env Secrets Adapter — reads secrets from process.env.
 *
 * Used when SECRETS_PROVIDER=env (the default for local development).
 * No network calls, no dependencies beyond Node.js.
 */

export async function getSecretFromEnv(name: string): Promise<string> {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Secret "${name}" not found in environment variables`);
  }
  return value;
}
