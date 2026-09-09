import { requireAuth } from '@/lib/auth/session';
import { runLocalReference } from '@/lib/bridge/local-reference';

export const runtime = 'nodejs';
let running = false;
const json = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'private, no-store' } });

export async function POST(request: Request) {
  const [, denied] = await requireAuth();
  if (denied) return denied;
  if (request.headers.get('origin') !== new URL(request.url).origin || request.headers.get('sec-fetch-site') === 'cross-site'
    || request.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== 'application/json') return json({ error: 'A same-origin JSON request is required.' }, 403);
  let body: Record<string, unknown>;
  try {
    const raw = await request.text(); if (raw.length > 2048) return json({ error: 'Local reference request is too large.' }, 413);
    body = JSON.parse(raw);
  } catch { return json({ error: 'Invalid local reference request.' }, 400); }
  if (!body || Array.isArray(body) || Object.keys(body).some(key => !['variant', 'confirmSynthetic'].includes(key))
    || body.confirmSynthetic !== true || typeof body.variant !== 'string' || !['dev_test_prod', 'dev_prod'].includes(body.variant)) return json({ error: 'Choose a supported synthetic variant and confirm the local-only scope. Project, actor, path and credential inputs are not accepted.' }, 422);
  if (running) return json({ error: 'A local reference is already running on this server process. Wait for its result; do not retry automatically.' }, 409);
  running = true;
  try { return json(await runLocalReference(body.variant as 'dev_test_prod' | 'dev_prod')); }
  catch { return json({ error: 'The local reference did not complete. No tenant operation was requested; check the local fixture/runtime tests.' }, 503); }
  finally { running = false; }
}
