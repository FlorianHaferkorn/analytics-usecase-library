import { requireRole } from '@/lib/auth/require-role';
import { getProject } from '@/lib/db/project-repo';
import { readDiscovery, writeDiscovery } from '@/lib/db/discovery-repo';
import { validateDiscovery } from '@/lib/discovery/document';

export const runtime = 'nodejs';
type Context = { params: Promise<{ projectId: string }> };
const json = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } });

export async function GET(_request: Request, context: Context) {
  const { projectId } = await context.params;
  const [, denied] = await requireRole('viewer', projectId);
  if (denied) return denied;
  if (!getProject(projectId)) return json({ error: { message: 'Project not found.' } }, 404);
  const [, editDenied] = await requireRole('editor', projectId);
  try { return json({ projectId, canEdit: !editDenied, ...readDiscovery(projectId) }); }
  catch { return json({ error: { message: 'Discovery could not be loaded. Existing evidence has not been changed.' } }, 500); }
}

export async function PUT(request: Request, context: Context) {
  const { projectId } = await context.params;
  const [user, denied] = await requireRole('editor', projectId);
  if (denied) return denied;
  if (!getProject(projectId)) return json({ error: { message: 'Project not found.' } }, 404);
  try {
    // Bound the body before parsing; source count and field limits are also validated.
    const raw = await request.text();
    if (new TextEncoder().encode(raw).byteLength > 12 * 1024 * 1024) return json({ error: { message: 'Discovery draft exceeds the 12 MB saved-document limit.' } }, 413);
    let body: { document?: unknown; expectedRevision?: unknown };
    try { body = JSON.parse(raw); } catch { return json({ error: { message: 'Invalid JSON.' } }, 400); }
    if (!body || typeof body !== 'object' || !(body.expectedRevision === null || typeof body.expectedRevision === 'string' && /^[a-f0-9]{64}$/.test(body.expectedRevision))) return json({ error: { message: 'A valid expectedRevision is required.' } }, 422);
    const result = validateDiscovery(body.document);
    if (!result.document) return json({ error: { message: 'Discovery validation failed.', details: result.errors } }, 422);
    const snapshot = writeDiscovery(projectId, result.document, body.expectedRevision, user.email);
    if (!snapshot) return json({ error: { message: 'A newer draft was saved elsewhere. Reload before saving; your local draft has not been overwritten.' } }, 409);
    return json({ projectId, ...snapshot });
  } catch { return json({ error: { message: 'Discovery could not be saved. Keep this page open and try again.' } }, 500); }
}
