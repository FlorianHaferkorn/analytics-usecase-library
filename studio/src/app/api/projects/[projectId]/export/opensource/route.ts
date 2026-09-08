/**
 * Tenant-scoped open-source export — delegates to the canonical handler.
 * Middleware has already verified project membership before this runs.
 */
export { unsupportedProjectExport as POST } from '@/lib/delivery/project-export-unsupported';
