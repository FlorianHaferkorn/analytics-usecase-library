import { requireRole } from '@/lib/auth/require-role';
import { projectBatch, type BatchMode } from '@/lib/bridge/project-batch';
import type { BatchInspection, BatchPreview, BatchSaved, BatchTest, BatchOutput } from '@/lib/project/batch-types';
import { createHash } from 'node:crypto';
import { isDeepStrictEqual } from 'node:util';

export const runtime = 'nodejs';
type Context = { params: Promise<{ projectId: string }> };
const hash = (value: unknown): value is string => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const json = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'private, no-store' } });

export async function GET(request: Request, context: Context) {
  const { projectId } = await context.params;
  const [, denied] = await requireRole('viewer', projectId); if (denied) return denied;
  const revision = new URL(request.url).searchParams.get('revision');
  if (!hash(revision)) return json({ error: 'Select a pinned project version.' }, 422);
  const result = await projectBatch<BatchInspection>(projectId, revision, 'inspect');
  if (!result.ok || !result.value) return json({ error: result.error }, result.status ?? 503);
  if (result.value.project_ref !== projectId || result.value.revision_hash !== revision) return json({ error: 'Project version mismatch.' }, 409);
  return json(result.value);
}

export async function POST(request: Request, context: Context) {
  const { projectId } = await context.params;
  const [viewer, denied] = await requireRole('viewer', projectId); if (denied) return denied;
  if (request.headers.get('origin') !== new URL(request.url).origin || request.headers.get('sec-fetch-site') === 'cross-site' || request.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== 'application/json') return json({ error: 'A same-origin JSON request is required.' }, 403);
  let body: Record<string, unknown>;
  try { const raw = await request.text(); if (raw.length > 256_000) return json({ error: 'Batch request exceeds the local input limit.' }, 413); body = JSON.parse(raw); }
  catch { return json({ error: 'Invalid JSON.' }, 400); }
  if (!body || typeof body !== 'object' || Array.isArray(body) || !hash(body.revisionHash) || typeof body.mode !== 'string' || !['preview', 'save', 'test', 'export'].includes(body.mode)) return json({ error: 'Select a supported operation and pinned version.' }, 422);
  const allowed: Record<string, string[]> = { preview: ['contract'], save: ['contract', 'previewHash', 'rationale', 'confirmed'], test: ['batches', 'confirmed'], export: ['confirmed'] };
  if (Object.keys(body).some(key => !['mode', 'revisionHash', ...allowed[body.mode as string]].includes(key))) return json({ error: 'Unexpected input fields. Actor, paths, state and credentials are not accepted.' }, 422);
  const input: Record<string, unknown> = {};
  if (body.mode === 'preview' || body.mode === 'save') {
    if (!body.contract || typeof body.contract !== 'object' || Array.isArray(body.contract)) return json({ error: 'A structured batch contract is required.' }, 422);
    input.contract = body.contract;
  }
  if (body.mode === 'save') {
    const [editor, forbidden] = await requireRole('editor', projectId); if (forbidden) return forbidden;
    if (!hash(body.previewHash) || body.confirmed !== true || typeof body.rationale !== 'string' || body.rationale.trim().length < 20 || body.rationale.length > 2000) return json({ error: 'Review the exact preview, add a rationale and confirm saving a new Working version.' }, 422);
    Object.assign(input, { preview_hash: body.previewHash, actor: editor.email, rationale: body.rationale.trim(), confirmed: true });
  }
  if (body.mode === 'test') {
    if (body.confirmed !== true || !Array.isArray(body.batches) || !body.batches.length || body.batches.length > 3 || body.batches.some(batch => !batch || typeof batch !== 'object' || Array.isArray(batch) || Object.keys(batch).some(key => !['batch_id', 'rows'].includes(key)) || typeof batch.batch_id !== 'string' || !Array.isArray(batch.rows) || batch.rows.length > 1000)) return json({ error: 'Confirm a bounded local test with up to three batches of 1,000 rows each. Existing state cannot be supplied.' }, 422);
    input.batches = body.batches;
  }
  if (body.mode === 'export' && body.confirmed !== true) return json({ error: 'Confirm generation from the existing released version.' }, 422);
  const result = await projectBatch<BatchPreview | BatchSaved | BatchTest | BatchOutput>(projectId, body.revisionHash, body.mode as BatchMode, input);
  if (!result.ok || !result.value) return json({ error: result.error }, result.status ?? 503);
  const value = result.value;
  if (body.mode === 'export') {
    const output = value as BatchOutput;
    if (output.output_type !== 'batch_ingestion_bundle' || output.manifest?.project_ref !== projectId || output.manifest.revision_hash !== body.revisionHash || !Array.isArray(output.files)) return json({ error: 'Generated output identity mismatch.' }, 409);
    if (!output.files.length || !Array.isArray(output.manifest.files) || !output.manifest.files.length) return json({ error: 'Empty generated output inventory.' }, 409);
    const paths = new Set<string>();
    for (const file of output.files) {
      if (!file || typeof file.path !== 'string' || file.path.includes(':') || file.path.includes('\\') || file.path.split('/').some(part => !part || part === '.' || part === '..') || paths.has(file.path.toLowerCase()) || typeof file.content !== 'string') return json({ error: 'Unsafe generated output inventory.' }, 409);
      paths.add(file.path.toLowerCase());
    }
    const covered = new Set<string>();
    for (const item of output.manifest.files) {
      if (!item || typeof item.path !== 'string' || covered.has(item.path) || !hash(item.sha256)) return json({ error: 'Invalid generated hash inventory.' }, 409);
      covered.add(item.path);
      const file = output.files.find(file => file.path === item.path);
      if (!file || createHash('sha256').update(file.content, 'utf8').digest('hex') !== item.sha256) return json({ error: 'Generated output hash mismatch.' }, 409);
    }
    if (output.files.some(file => file.path !== 'output-manifest.json' && !covered.has(file.path))) return json({ error: 'Generated output is not fully covered by hashes.' }, 409);
    const manifestFile = output.files.find(file => file.path === 'output-manifest.json');
    try { if (!manifestFile || !isDeepStrictEqual(JSON.parse(manifestFile.content), output.manifest)) return json({ error: 'Generated manifest mismatch.' }, 409); }
    catch { return json({ error: 'Invalid generated manifest.' }, 409); }
  } else {
    const scoped = value as BatchPreview | BatchSaved | BatchTest;
    if (scoped.project_ref !== projectId || !hash(scoped.revision_hash) || (body.mode === 'save' ? (scoped as BatchSaved).parent_revision_hash !== body.revisionHash || (scoped as BatchSaved).state !== 'working' || (scoped as BatchSaved).release_required !== true : scoped.revision_hash !== body.revisionHash)) return json({ error: 'Project version mismatch. Reload the Package before continuing.' }, 409);
    if (body.mode === 'test' && ((scoped as BatchTest).evidence_kind !== 'local_check' || (scoped as BatchTest).tenant_actions_performed !== false)) return json({ error: 'Local evidence scope mismatch.' }, 409);
    if (body.mode === 'save' && ((scoped as BatchSaved).tenant_actions_performed !== false || scoped.revision_hash === body.revisionHash)) return json({ error: 'Working version scope mismatch.' }, 409);
  }
  void viewer; // Authorization is checked above; no client identity is forwarded.
  return json(value);
}
