/**
 * preflight — standalone / local-first readiness check (I-6.5).
 *
 * A fresh installer runs this to learn whether the cockpit can operate
 * standalone with their own key (BYO-key): is an LLM provider configured, is the
 * Python bridge reachable, are the Core artifacts present, is the secrets
 * provider valid. The aggregation (`computeSetupReadiness`) is pure and the
 * decision is honest: a missing *required* check makes the install not-ready and
 * names the blocker — never a fake "all good".
 */

export type CheckStatus = 'ok' | 'warn' | 'missing';

export interface SetupCheck {
  key: 'llm_key' | 'secrets_provider' | 'python_bridge' | 'core_artifacts' | 'auth';
  label: string;
  status: CheckStatus;
  detail: string;
  required: boolean;
}

export interface SetupReadiness {
  ready: boolean;
  checks: SetupCheck[];
  /** Labels of required checks that are missing (empty when ready). */
  blockers: string[];
}

/** Pure aggregation: ready ⇔ no required check is `missing`. */
export function computeSetupReadiness(checks: SetupCheck[]): SetupReadiness {
  const blockers = checks.filter((c) => c.required && c.status === 'missing').map((c) => c.label);
  return { ready: blockers.length === 0, checks, blockers };
}

/** Which LLM provider (if any) a BYO key is configured for. Priority: Google → Anthropic → OpenAI. */
export function detectLlmProvider(env: Record<string, string | undefined>): string | null {
  if (env.GOOGLE_API_KEY || env.GEMINI_API_KEY) return 'google';
  if (env.ANTHROPIC_API_KEY) return 'anthropic';
  if (env.OPENAI_API_KEY) return 'openai';
  return null;
}

export function llmKeyCheck(env: Record<string, string | undefined>): SetupCheck {
  const provider = detectLlmProvider(env);
  return {
    key: 'llm_key',
    label: 'LLM-Key (BYO)',
    status: provider ? 'ok' : 'missing',
    detail: provider
      ? `${provider}-Key erkannt`
      : 'kein LLM-Key gesetzt (ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY)',
    required: true,
  };
}

export function secretsProviderCheck(env: Record<string, string | undefined>): SetupCheck {
  const raw = (env.SECRETS_PROVIDER ?? 'env').toLowerCase();
  const valid = raw === 'env' || raw === 'azure' || raw === 'aws';
  return {
    key: 'secrets_provider',
    label: 'Secrets-Provider',
    status: valid ? 'ok' : 'missing',
    detail: valid ? `SECRETS_PROVIDER=${raw}` : `ungültig: "${raw}" (env|azure|aws)`,
    required: true,
  };
}

export function authCheck(env: Record<string, string | undefined>): SetupCheck {
  const oauth = Boolean(env.GITHUB_ID && env.GITHUB_SECRET);
  return {
    key: 'auth',
    label: 'Auth',
    status: oauth ? 'ok' : 'warn',
    detail: oauth ? 'GitHub-OAuth konfiguriert' : 'nur Dev-Credentials (lokal-first ok)',
    required: false,
  };
}
