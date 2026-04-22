/**
 * Tenant-scoped bracket detail — delegates to the canonical handler.
 * Middleware has already verified project membership before this runs.
 */
export { GET, PUT } from '@/app/api/core/brackets/[id]/route';
