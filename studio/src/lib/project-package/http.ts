import { ErrorCode } from '@/lib/api/error-codes';
import { apiError } from '@/lib/api/response';
import type { PackageRepositoryResult } from '@/lib/bridge/project-package-repository';

export const MAX_PACKAGE_JSON_CHARS = 145 * 1024 * 1024;
export const MAX_PACKAGE_ARCHIVE_BYTES = 100 * 1024 * 1024;

export function packageRepositoryError(
  result: PackageRepositoryResult<unknown>,
  fallback = 'Project Package operation failed',
): Response {
  const message = result.error || fallback;
  const normalized = message.toLowerCase();

  if (!result.available) {
    return apiError(ErrorCode.UNSUPPORTED, message, 503);
  }
  if (result.status === 409 || result.code === 'stale_head' || normalized.includes('already exists')) {
    return apiError(ErrorCode.CONFLICT, message, 409);
  }
  if (
    normalized.includes('does not exist')
    || normalized.includes('no revisions')
    || normalized.includes('unknown revision')
    || normalized.includes('revision not found')
  ) {
    return apiError(ErrorCode.NOT_FOUND, message, 404);
  }
  if (normalized.includes('size') || normalized.includes('too large') || normalized.includes('exceeds')) {
    return apiError(ErrorCode.VALIDATION_ERROR, message, 413);
  }
  return apiError(ErrorCode.VALIDATION_ERROR, message, 422);
}

export function contentLengthExceeds(request: Request, maximum: number): boolean {
  const value = request.headers.get('content-length');
  if (!value) return false;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > maximum;
}
