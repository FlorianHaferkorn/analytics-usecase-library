/**
 * Tenant-scoped bracket list/create — delegates to the canonical handler.
 * Middleware has already verified project membership before this runs.
 */
export { GET, POST } from '@/app/api/core/brackets/route';
