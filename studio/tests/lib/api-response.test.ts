/**
 * Tests for API Response Helpers — standardized response shapes.
 */

import { describe, it, expect } from 'vitest';
import { apiSuccess, apiCreated, apiError, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

describe('api-response', () => {
  it('apiSuccess wraps data in { data } shape', async () => {
    const res = apiSuccess({ items: [1, 2, 3] });
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json).toEqual({ items: [1, 2, 3] });
  });

  it('apiSuccess accepts custom status code', async () => {
    const res = apiSuccess({ ok: true }, 202);
    expect(res.status).toBe(202);
  });

  it('apiCreated returns 201 with data', async () => {
    const res = apiCreated({ id: 'new-1' });
    expect(res.status).toBe(201);
    const json = await res.json();
    expect(json).toEqual({ id: 'new-1' });
  });

  it('apiError returns structured error shape', async () => {
    const res = apiError(ErrorCode.NOT_FOUND, 'Project not found', 404);
    expect(res.status).toBe(404);
    const json = await res.json();
    expect(json.error.code).toBe('NOT_FOUND');
    expect(json.error.message).toBe('Project not found');
  });

  it('apiError handles 403 forbidden', async () => {
    const res = apiError(ErrorCode.FORBIDDEN, 'Editor role required', 403);
    expect(res.status).toBe(403);
    const json = await res.json();
    expect(json.error.code).toBe('FORBIDDEN');
  });

  it('apiValidationError returns 422 with details', async () => {
    const res = apiValidationError(['Name is required', 'Email is invalid']);
    expect(res.status).toBe(422);
    const json = await res.json();
    expect(json.error.code).toBe('VALIDATION_ERROR');
    expect(json.error.message).toBe('Validation failed');
    expect(json.error.details).toEqual(['Name is required', 'Email is invalid']);
  });

  it('ErrorCode contains all expected codes', () => {
    expect(ErrorCode.AUTH_REQUIRED).toBe('AUTH_REQUIRED');
    expect(ErrorCode.FORBIDDEN).toBe('FORBIDDEN');
    expect(ErrorCode.NOT_FOUND).toBe('NOT_FOUND');
    expect(ErrorCode.VALIDATION_ERROR).toBe('VALIDATION_ERROR');
    expect(ErrorCode.CONFLICT).toBe('CONFLICT');
    expect(ErrorCode.INTERNAL_ERROR).toBe('INTERNAL_ERROR');
  });

  it('apiError handles 409 conflict', async () => {
    const res = apiError(ErrorCode.CONFLICT, 'Plugin already registered', 409);
    expect(res.status).toBe(409);
    const json = await res.json();
    expect(json.error.code).toBe('CONFLICT');
    expect(json.error.message).toBe('Plugin already registered');
  });
});
