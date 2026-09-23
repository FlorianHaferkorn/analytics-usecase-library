/**
 * Session Helper — single entry point for reading the authenticated user
 * from JWT sessions in API Route Handlers.
 *
 * Route Handlers do NOT get auth injected by middleware the way pages do.
 * This helper calls `auth()` to read the JWT cookie and extract the user.
 */

import { auth } from '@/lib/auth/config';
import { apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export interface SessionUser {
  id: string;
  email: string;
  name: string;
  /** Server-signed sign-in provenance; absent on older sessions. */
  authentication?: {
    provider: string;
    providerAccountId: string;
    authenticatedAt: number;
    method: string;
  };
}

/**
 * Extract the authenticated user from the JWT session cookie.
 * Returns null if no valid session exists.
 */
export async function getSessionUser(): Promise<SessionUser | null> {
  const session = await auth();
  if (!session?.user?.email) return null;

  const authentication = (session as unknown as Record<string, unknown>).authentication;
  return {
    id: (session.user as Record<string, unknown>).id as string ?? session.user.email,
    email: session.user.email,
    name: session.user.name ?? session.user.email.split('@')[0],
    ...(authentication && typeof authentication === 'object'
      ? { authentication: authentication as SessionUser['authentication'] }
      : {}),
  };
}

/**
 * Require authentication — returns SessionUser or a 401 Response.
 * Use in Route Handlers:
 *
 * ```ts
 * const [user, errorResponse] = await requireAuth();
 * if (errorResponse) return errorResponse;
 * // user is guaranteed non-null here
 * ```
 */
export async function requireAuth(): Promise<[SessionUser, null] | [null, Response]> {
  const user = await getSessionUser();
  if (!user) {
    return [null, apiError(ErrorCode.AUTH_REQUIRED, 'Authentication required', 401)];
  }
  return [user, null];
}
