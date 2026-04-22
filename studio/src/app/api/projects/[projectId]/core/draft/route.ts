/**
 * Tenant-scoped draft creation — delegates to the canonical handler.
 * Middleware has already verified project membership before this runs.
 */
export { POST } from '@/app/api/core/draft/route';
