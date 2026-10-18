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
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  CONFLICT: 'CONFLICT',
  UNSUPPORTED: 'UNSUPPORTED',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
} as const;

export type ErrorCodeValue = (typeof ErrorCode)[keyof typeof ErrorCode];
