import 'server-only';

import { requireRole } from './require-role';
import type { SessionUser } from './session';
import { apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export interface RunnerAccess extends SessionUser {
  /** Stable provider identity, never an email, request field or display name. */
  actor: string;
}

const MAX_LOGIN_AGE_MS = 30 * 60 * 1000;

export interface RunnerAccessCheck {
  id: string;
  title: string;
  state: 'configured' | 'missing' | 'not_verified';
  detail: string;
  action: string;
}

const deniedChecks = new WeakMap<Response, RunnerAccessCheck>();
function denied(response: Response, check: RunnerAccessCheck): [null, Response] {
  deniedChecks.set(response, check);
  return [null, response];
}

function configuredOrigin(): URL | null {
  const configured = process.env.STUDIO_RUNNER_ORIGIN;
  try {
    const origin = new URL(configured ?? '');
    if (!['https:', 'http:'].includes(origin.protocol) || origin.origin !== configured
        || origin.username || origin.password) return null;
    if (origin.protocol === 'http:' && !['localhost', '127.0.0.1', '[::1]'].includes(origin.hostname)) return null;
    return origin;
  } catch { return null; }
}

function loginIsFresh(access: SessionUser, now: number): boolean {
  return !!access.authentication && now - access.authentication.authenticatedAt <= MAX_LOGIN_AGE_MS;
}

/** Call only after requireRunnerAccess succeeded; these are local checks, not tenant proof. */
export function runnerAccessReadiness(access: RunnerAccess): RunnerAccessCheck[] {
  const fresh = loginIsFresh(access, Date.now());
  const origin = configuredOrigin();
  return [
    { id: 'studio_access', title: 'Studio sign-in and project permission', state: 'configured',
      detail: 'Verified GitHub sign-in and current project administrator permission are present.',
      action: 'No access change is required. This does not verify Fabric permissions.' },
    { id: 'studio_session_secret', title: 'Session signing configuration', state: 'configured',
      detail: 'The host session secret passes the minimum configuration check; randomness and host protection are not proven by this check.',
      action: 'Keep a randomly generated secret protected on the host; never include it in a project package.' },
    { id: 'studio_fresh_login', title: 'Recent sign-in for approval and execution', state: fresh ? 'configured' : 'missing',
      detail: fresh ? 'The verified sign-in is within the 30-minute mutation window.' : 'Read-only inspection is available, but the sign-in is too old for approval or execution.',
      action: fresh ? 'Approve and execute within the sign-in window, or sign in again.' : 'Sign out and sign in again with GitHub before approving or executing.' },
    { id: 'studio_origin', title: 'Protected Studio origin', state: origin ? 'configured' : 'missing',
      detail: origin ? 'An exact HTTPS origin, or HTTP loopback origin for local use, is configured. Each mutation also checks the request origin.' : 'The host does not have a valid exact HTTPS or HTTP loopback origin configured.',
      action: origin ? 'Open Studio at the configured origin; cross-origin mutation requests remain blocked.' : 'Set STUDIO_RUNNER_ORIGIN on the host to the exact Studio origin without a trailing slash or path. Use HTTPS except on loopback.' },
  ];
}

/** Enrich only GET diagnostics; leave the protected guard and POST envelope unchanged. */
export async function runnerAccessReadinessFailure(response: Response): Promise<Response> {
  const check = deniedChecks.get(response) ?? {
    id: 'studio_access', title: 'Protected Studio access', state: 'missing' as const,
    detail: 'The protected access check did not succeed. Runner configuration was not inspected.',
    action: 'Sign in with GitHub and ask a project administrator to verify access. If access is already configured, check the host authentication setup.',
  };
  let body: Record<string, unknown>;
  try { body = await response.clone().json(); }
  catch { body = { error: { code: 'FORBIDDEN', message: 'Protected Studio access is required.' } }; }
  const headers = new Headers(response.headers);
  headers.delete('content-length');
  headers.set('Cache-Control', 'private, no-store');
  return Response.json({ ...body, checks: [check], checked_at: new Date().toISOString() }, { status: response.status, headers });
}

/**
 * Protected runner access, distinct from local/demo Studio authoring access.
 * The normal role helper reads the signed server session and current DB role.
 * Configuration is read only from the host environment, never forwarded headers.
 */
export async function requireRunnerAccess(
  projectId: string,
  request?: Request,
  mutation = false,
): Promise<[RunnerAccess, null] | [null, Response]> {
  const [user, roleError] = await requireRole('admin', projectId);
  if (roleError) return denied(roleError, {
    id: 'studio_access', title: 'Studio sign-in and project permission', state: 'missing',
    detail: roleError.status === 401 ? 'A Studio sign-in is required before runner access can be checked.' : 'The current account does not have the required project administrator access.',
    action: roleError.status === 401 ? 'Sign in with GitHub, then reopen this project.' : 'Ask a project administrator to grant the required project access to your verified account.',
  });

  // JWT provenance is meaningful only with a host-generated secret. This is a
  // minimum configuration check, not a claim that string length proves entropy.
  const secret = process.env.AUTH_SECRET ?? process.env.NEXTAUTH_SECRET ?? '';
  if (secret.trim().length < 32 || /changeme|your[-_ ]?secret|placeholder|replace[-_ ]?me/i.test(secret)
      || new Set(secret).size < 8) {
    return denied(apiError(ErrorCode.INTERNAL_ERROR,
      'The protected runner requires a securely generated session secret of at least 32 characters.', 503), {
      id: 'studio_session_secret', title: 'Session signing configuration', state: 'missing',
      detail: 'The host session signing configuration does not meet the protected runner minimum. Runner configuration was not inspected.',
      action: 'Configure a randomly generated AUTH_SECRET of at least 32 characters on the host, restart Studio and sign in again. Do not paste the secret into Studio.',
    });
  }

  const login = user.authentication;
  const now = Date.now();
  if (!login || login.provider !== 'github' || login.method !== 'oauth'
      || typeof login.providerAccountId !== 'string' || !/^[1-9][0-9]{0,19}$/.test(login.providerAccountId)
      || !Number.isSafeInteger(login.authenticatedAt) || login.authenticatedAt <= 0
      || login.authenticatedAt > now) {
    return denied(apiError(ErrorCode.FORBIDDEN,
      'A verified GitHub sign-in is required for the protected runner. Demo and legacy sessions are not accepted.', 403), {
      id: 'studio_access', title: 'Verified provider sign-in', state: 'missing',
      detail: 'The session does not carry valid verified GitHub sign-in provenance. Demo and legacy sessions cannot authorize the runner.',
      action: 'Sign out and sign in with GitHub. If GitHub sign-in is unavailable, ask the host administrator to configure it.',
    });
  }

  if (mutation) {
    if (!loginIsFresh(user, now)) {
      return [null, apiError(ErrorCode.FORBIDDEN,
        'Sign in again before approving or executing a runner plan. The sign-in must be less than 30 minutes old.', 403)];
    }
    const origin = configuredOrigin();
    if (!origin) {
      return [null, apiError(ErrorCode.INTERNAL_ERROR,
        'The protected runner requires an exact HTTPS origin; HTTP is allowed only on loopback.', 503)];
    }
    if (!request || request.headers.get('origin') !== origin.origin
        || request.headers.get('sec-fetch-site') === 'cross-site'
        || request.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== 'application/json') {
      return [null, apiError(ErrorCode.FORBIDDEN,
        'Runner mutations require a same-origin JSON request from the configured Studio origin.', 403)];
    }
  }
  return [{ ...user, actor: `github:${login.providerAccountId}` }, null];
}
