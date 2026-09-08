import { requireRole } from '@/lib/auth/require-role';
import { readDiscovery } from '@/lib/db/discovery-repo';
import { loadProjectPackage, transferDiscoveryToPackage } from '@/lib/bridge/project-package-repository';
import { parse } from 'yaml';

export const runtime = 'nodejs';
type Context = { params: Promise<{ projectId: string }> };
const json = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } });

export async function GET(_request: Request, context: Context) {
  const { projectId } = await context.params;
  const [, denied] = await requireRole('editor', projectId);
  if (denied) return denied;
  const head = await loadProjectPackage(projectId);
  if (!head.ok) return json({ error: head.error ?? 'Package is unavailable.' }, 503);
  if (!head.value) return json({ error: 'Create or import this project’s Package before transferring evidence.' }, 409);
  if (head.value.revision.project_ref !== projectId) return json({ error: 'Package belongs to a different project.' }, 409);
  const manifest = parse(Buffer.from(head.value.files.find((file) => file.path === 'package.yaml')!.contentBase64, 'base64').toString('utf-8'));
  const opportunityPath = manifest.modules.find((entry: { module_type: string }) => entry.module_type === 'opportunity').path;
  const opportunity = parse(Buffer.from(head.value.files.find((file) => file.path === opportunityPath)!.contentBase64, 'base64').toString('utf-8'));
  return json({ projectId, head: head.value.revision, objectives: opportunity.objectives, scopeStatus: opportunity.scope_status });
}

export async function POST(request: Request, context: Context) {
  const { projectId } = await context.params;
  const [user, denied] = await requireRole('editor', projectId);
  if (denied) return denied;
  try {
    const raw = await request.text();
    if (raw.length > 160000) return json({ error: 'Review request is too large.' }, 413);
    const body = JSON.parse(raw);
    if (!body || body.confirmed !== true || !/^[a-f0-9]{64}$/.test(body.discoveryRevision ?? '') || !/^[a-f0-9]{64}$/.test(body.expectedHeadRevisionHash ?? '') || typeof body.rationale !== 'string' || body.rationale.trim().length < 20 || body.rationale.length > 4000 || !Array.isArray(body.candidateKeys) || !body.candidateKeys.length || body.candidateKeys.length > 500 || body.candidateKeys.some((key: unknown) => typeof key !== 'string') || new Set(body.candidateKeys).size !== body.candidateKeys.length) return json({ error: 'A saved revision, unique selection, rationale and explicit review confirmation are required.' }, 422);
    // Snapshot is server-owned. No caller-supplied document or actor is trusted.
    const snapshot = readDiscovery(projectId);
    if (snapshot.revision !== body.discoveryRevision) return json({ error: 'Discovery changed. Reload and review the saved evidence again.' }, 409);
    if (!Array.isArray(body.objectiveKeys) || body.objectiveKeys.some((key: unknown) => typeof key !== 'string')) return json({ error: 'Explicit objective mapping selection is required.' }, 422);
    const transferred = await transferDiscoveryToPackage(projectId, {
      discoveryRevision: snapshot.revision, expectedHeadRevisionHash: body.expectedHeadRevisionHash,
      document: snapshot.document, candidateKeys: body.candidateKeys, objectiveKeys: body.objectiveKeys, rationale: body.rationale, actor: user.email,
    });
    if (!transferred.ok) return json({ error: transferred.error ?? 'Transfer failed; no approval was granted.' }, transferred.status ?? (transferred.available ? 422 : 503));
    return json({ projectId, revision: transferred.value, status: 'proposed' });
  } catch { return json({ error: 'Invalid review request or unavailable saved evidence. No approval was granted.' }, 400); }
}
