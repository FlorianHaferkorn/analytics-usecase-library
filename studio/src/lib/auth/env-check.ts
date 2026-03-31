/**
 * Auth Environment Validation — ensures AUTH_SECRET is properly configured.
 *
 * Throws in production if AUTH_SECRET is missing or still a placeholder.
 * Warns in development to aid local setup.
 */

const PLACEHOLDER_VALUES = ['changeme', 'your-secret-here', 'placeholder', 'secret'];

export function validateAuthEnv(): void {
  const secret = process.env.AUTH_SECRET ?? process.env.NEXTAUTH_SECRET ?? '';
  const isProduction = process.env.NODE_ENV === 'production';

  if (!secret) {
    if (isProduction) {
      throw new Error('AUTH_SECRET is required in production. Generate one with: openssl rand -base64 32');
    }
    console.warn('[auth] AUTH_SECRET not set — using insecure default for development.');
    return;
  }

  if (PLACEHOLDER_VALUES.includes(secret.toLowerCase())) {
    if (isProduction) {
      throw new Error('AUTH_SECRET is still a placeholder value. Generate a real secret: openssl rand -base64 32');
    }
    console.warn('[auth] AUTH_SECRET appears to be a placeholder — replace before deploying.');
  }
}
