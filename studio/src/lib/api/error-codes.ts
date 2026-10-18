/**
 * Standardized API Error Codes.
 *
 * Every API error response includes a machine-readable code
 * alongside a human-readable message.
 */

export const ErrorCode = {
  AUTH_REQUIRED: 'AUTH_REQUIRED',
  FORBIDDEN: 'FORBIDDEN',
  /** Signed in, but not a member of the requested project (tenant gate). */
  PROJECT_ACCESS_DENIED: 'PROJECT_ACCESS_DENIED',
  /** AI egress for this project/endpoint is not approved (default-deny gate). */
  AI_EGRESS_NOT_APPROVED: 'AI_EGRESS_NOT_APPROVED',
  /** The egress gate could not persist its audit evidence, so it refuses. */
  AI_EGRESS_AUDIT_FAILED: 'AI_EGRESS_AUDIT_FAILED',
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  CONFLICT: 'CONFLICT',
  /** The request was based on a revision that is no longer the head (saved elsewhere meanwhile). */
  STALE_REVISION: 'STALE_REVISION',
  UNSUPPORTED: 'UNSUPPORTED',
  /** A dependency (bridge, CLI, store) is unavailable; retrying later may succeed. */
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
} as const;

export type ErrorCodeValue = (typeof ErrorCode)[keyof typeof ErrorCode];
