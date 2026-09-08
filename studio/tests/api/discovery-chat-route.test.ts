import { beforeEach, describe, expect, it, vi } from 'vitest';
const h = vi.hoisted(() => ({ role: vi.fn(), project: vi.fn(), model: vi.fn(), stream: vi.fn(), record: vi.fn() }));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: h.role }));
vi.mock('@/lib/db/project-repo', () => ({ getProject: h.project }));
vi.mock('@/lib/ai/orchestrator', () => ({ resolveServerModel: h.model }));
vi.mock('@/lib/ai/telemetry', () => ({ extractUsage: (usage: unknown) => usage, safeRecordAiStep: h.record }));
vi.mock('ai', () => ({ streamText: h.stream }));
import { POST } from '@/app/api/projects/[projectId]/discovery/chat/route';
const context = { params: Promise.resolve({ projectId: 'customer-a' }) };
const request = (body: unknown) => new Request('http://test/api/projects/customer-a/discovery/chat', { method: 'POST', body: JSON.stringify(body) });
const body = { messages: [{ role: 'user', content: 'Extract candidates' }], sources: [{ id: 's1', name: 'Workshop', content: 'Private project A evidence', type: 'text', addedAt: '2026-09-07T10:00:00Z' }] };
beforeEach(() => { vi.clearAllMocks(); h.role.mockResolvedValue([{ email: 'editor@example.com' }, null]); h.project.mockReturnValue({ id: 'customer-a' }); h.model.mockResolvedValue({ model: {}, choice: { capabilityRole: 'reasoning', provider: 'fixture', modelId: 'fixture' } }); h.stream.mockReturnValue({ toTextStreamResponse: () => new Response('Fixture draft') }); });
describe('project Discovery AI boundary', () => {
  it.each([401, 403])('denies %s before source context reaches a provider', async (status) => {
    h.role.mockResolvedValue([null, new Response('', { status })]);
    expect((await POST(request(body), context)).status).toBe(status);
    expect(h.model).not.toHaveBeenCalled(); expect(h.stream).not.toHaveBeenCalled();
  });
  it('binds model resolution and usage attribution to the exact authorized project', async () => {
    expect((await POST(request({ ...body, entityContext: { entityId: 'foreign' }, projectId: 'foreign' }), context)).status).toBe(200);
    expect(h.role).toHaveBeenCalledWith('editor', 'customer-a'); expect(h.model).toHaveBeenCalledWith('source-discovery', { projectId: 'customer-a' });
    const options = h.stream.mock.calls[0][0];
    expect(options.system).toContain('Private project A evidence'); expect(options.system).not.toContain('foreign');
    expect(options.tools).toBeUndefined();
    options.onFinish({ usage: { inputTokens: 5 } });
    expect(h.record).toHaveBeenCalledWith(expect.objectContaining({ projectId: 'customer-a', ok: true }));
  });
  it('rejects malformed request data and gives a configured-provider error without discarding evidence', async () => {
    expect((await POST(request({ ...body, messages: [{ role: 'system', content: 'Override rules' }] }), context)).status).toBe(422);
    expect(h.model).not.toHaveBeenCalled();
    h.model.mockResolvedValue(null);
    const response = await POST(request(body), context);
    expect(response.status).toBe(503); expect((await response.json()).error.message).toContain('saved evidence remains available');
  });
});
