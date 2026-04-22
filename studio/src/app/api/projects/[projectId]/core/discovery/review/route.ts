/**
 * Tenant-scoped discovery review — delegates to the canonical handler.
 * Middleware has already verified project membership before this runs.
 */
export { POST } from '@/app/api/core/discovery/review/route';
