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

/** Validation error (422) with field-level errors. */
export function apiValidationError(errors: string[]): NextResponse {
  return NextResponse.json(
    { error: { code: ErrorCode.VALIDATION_ERROR, message: 'Validation failed', details: errors } },
    { status: 422 },
  );
}
