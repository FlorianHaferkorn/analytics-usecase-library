/**
 * Standardized API Response Helpers.
 *
 * All API routes use these helpers for consistent response shapes:
 *   Success → { data: T }
 *   Error   → { error: { code, message } }
 */

import { NextResponse } from 'next/server';
import type { ErrorCodeValue } from './error-codes';
import { ErrorCode } from './error-codes';

/** Success response (200 by default). */
export function apiSuccess<T>(data: T, status = 200): NextResponse {
  return NextResponse.json(data, { status });
}

/** Created response (201). */
export function apiCreated<T>(data: T): NextResponse {
  return NextResponse.json(data, { status: 201 });
}

/** Error response with code and message; `extra` adds fields inside `error` (e.g. an evidence id). */
export function apiError(
  code: ErrorCodeValue,
  message: string,
  status: number,
  extra?: Record<string, unknown>,
): NextResponse {
  return NextResponse.json({ error: { ...extra, code, message } }, { status });
}

/** The code a route without a more specific one reports for an HTTP status. */
export function errorCodeForStatus(status: number): ErrorCodeValue {
  if (status === 401) return ErrorCode.AUTH_REQUIRED;
  if (status === 403) return ErrorCode.FORBIDDEN;
  if (status === 404) return ErrorCode.NOT_FOUND;
  if (status === 409) return ErrorCode.CONFLICT;
  if (status === 501) return ErrorCode.UNSUPPORTED;
  if (status === 503) return ErrorCode.SERVICE_UNAVAILABLE;
  if (status >= 500) return ErrorCode.INTERNAL_ERROR;
  return ErrorCode.VALIDATION_ERROR;
}

/**
 * Error response for routes that only know a status and a message (e.g. a bridge result).
 * A missing message falls back to a generic one so the body always has the standard shape.
 */
export function apiErrorForStatus(status: number, message: string | undefined, headers?: HeadersInit): NextResponse {
  return NextResponse.json(
    { error: { code: errorCodeForStatus(status), message: message || 'The request could not be completed.' } },
    { status, headers },
  );
}

/** Validation error (422) with field-level errors. */
export function apiValidationError(errors: string[]): NextResponse {
  return NextResponse.json(
    { error: { code: ErrorCode.VALIDATION_ERROR, message: 'Validation failed', details: errors } },
    { status: 422 },
  );
}
