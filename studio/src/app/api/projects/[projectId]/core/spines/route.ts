/**
 * Tenant-scoped spines list — delegates to the canonical handler.
 * Middleware has already verified project membership before this runs.
 */
export { GET } from '@/app/api/core/spines/route';
