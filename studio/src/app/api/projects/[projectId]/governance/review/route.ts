/**
 * Tenant-scoped governance review — delegates to the canonical handler.
 * Middleware has already verified project membership before this runs.
 */
export { GET, POST } from '@/app/api/governance/review/route';
