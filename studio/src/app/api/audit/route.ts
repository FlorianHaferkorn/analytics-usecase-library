/**
 * Audit API — Query audit events for a project.
 *
 * GET /api/audit?projectId=X&entityType=Y&entityId=Z&limit=50&offset=0
 */

import { getAuditEvents, getAuditEventsByEntity, getAuditEventCount } from '@/lib/db/audit-repo';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get('projectId') ?? 'default';
  const entityType = searchParams.get('entityType') as 'bracket' | 'project' | 'theme' | 'discovery' | null;
  const entityId = searchParams.get('entityId');
  const limit = Number(searchParams.get('limit') ?? '50');
  const offset = Number(searchParams.get('offset') ?? '0');

  if (entityType && entityId) {
    const events = getAuditEventsByEntity(entityType, entityId, limit);
    return Response.json({ events });
  }

  const events = getAuditEvents(projectId, limit, offset);
  const total = getAuditEventCount(projectId);
  return Response.json({ events, total });
}
