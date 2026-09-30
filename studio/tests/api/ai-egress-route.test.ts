import { beforeEach, describe, expect, it, vi } from 'vitest';

const h = vi.hoisted(() => ({ auth: vi.fn(), model: vi.fn(), stream: vi.fn(), generate: vi.fn(), audit: vi.fn(() => ({ id: 'aud-test' })) }));
vi.mock('@/lib/auth/session', () => ({ requireAuth: h.auth }));
vi.mock('@/lib/ai/orchestrator', () => ({ resolveServerModel: h.model }));
vi.mock('@/lib/ai/telemetry', () => ({ extractUsage: vi.fn(), safeRecordAiStep: vi.fn() }));
vi.mock('@/lib/ai/tools/discovery-tools', () => ({ discoveryTools: {} }));
vi.mock('ai', () => ({ streamText: h.stream, generateText: h.generate }));
vi.mock('@/lib/db/audit-repo', () => ({ logAuditEvent: h.audit }));

import { POST as chat } from '@/app/api/ai/chat/route';
import { POST as wizard } from '@/app/api/ai/wizard/route';
import { POST as factsheet } from '@/app/api/ai/factsheet-draft/route';

function request(path: string, body: unknown): Request {
  return new Request(`http://test/api/ai/${path}`, { method: 'POST', body: JSON.stringify(body) });
}

beforeEach(() => {
  vi.clearAllMocks();
  h.auth.mockResolvedValue([{ email: 'editor@example.com' }, null]);
  h.model.mockResolvedValue({ model: {}, choice: { provider: 'anthropic', modelId: 'fixture', capabilityRole: 'balanced' } });
});

describe('projectless AI data egress', () => {
  it.each([
    ['chat with client context', chat, 'chat', { messages: [{ role: 'user', content: 'Customer private data' }], context: 'Secret source data' }],
    ['chat with entity context', chat, 'chat', { messages: [{ role: 'user', content: 'Analyze this' }], entityContext: { entityType: 'kpi', entityId: 'KPI-COM-005' } }],
    ['wizard with user prompt', wizard, 'wizard', { kind: 'kpi', prompt: 'Customer private data' }],
  ] as const)('denies %s before model construction', async (_, handler, path, body) => {
    const response = await handler(request(path, body));
    expect(response.status).toBe(403);
    expect((await response.json()).code).toBe('AI_EGRESS_NOT_APPROVED');
    expect(h.model).not.toHaveBeenCalled();
    expect(h.stream).not.toHaveBeenCalled();
    expect(h.generate).not.toHaveBeenCalled();
    expect(h.audit).toHaveBeenCalled();
  });

  it('keeps the deterministic factsheet draft available without model egress', async () => {
    const response = await factsheet(request('factsheet-draft', { prompt: 'A private customer use case' }));
    expect(response.status).toBe(200);
    expect(await response.json()).toMatchObject({ name: 'A private customer use case', engine: 'deterministic', aiStatus: 'not-approved' });
    expect(h.model).not.toHaveBeenCalled();
    expect(h.generate).not.toHaveBeenCalled();
  });

  it('keeps deterministic reconciliation available without sending prose or YAML', async () => {
    const response = await factsheet(request('factsheet-draft', {
      mode: 'reconcile', editedSource: 'bracket',
      prose: '# Customer factsheet',
      bracket: 'orchestration:\n  strategic_kpi_id: KPI-COM-005\n  influencing_kpi_ids: []\n  action_code_ids: []',
    }));
    expect(response.status).toBe(200);
    expect((await response.json()).engine).toBe('deterministic');
    expect(h.model).not.toHaveBeenCalled();
    expect(h.generate).not.toHaveBeenCalled();
  });

  it('keeps authentication ahead of the egress gate', async () => {
    h.auth.mockResolvedValue([null, new Response('', { status: 401 })]);
    expect((await chat(request('chat', {}))).status).toBe(401);
    expect(h.model).not.toHaveBeenCalled();
  });

  it('preserves wizard kind validation before the egress gate', async () => {
    const response = await wizard(request('wizard', { kind: 'unknown', prompt: 'text' }));
    expect(response.status).toBe(400);
    expect(h.model).not.toHaveBeenCalled();
  });
});
