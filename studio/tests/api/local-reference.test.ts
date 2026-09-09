import { beforeEach, describe, expect, it, vi } from 'vitest';
const fake = vi.hoisted(() => ({ auth: vi.fn(), run: vi.fn() }));
vi.mock('@/lib/auth/session', () => ({ requireAuth: fake.auth }));
vi.mock('@/lib/bridge/local-reference', () => ({ runLocalReference: fake.run }));
import { POST } from '@/app/api/local-reference/route';
const body = { variant: 'dev_test_prod', confirmSynthetic: true };
const request = (value: unknown = body, headers: Record<string, string> = {}) => new Request('http://localhost:3000/api/local-reference', {
  method: 'POST', headers: { origin: 'http://localhost:3000', 'content-type': 'application/json', ...headers }, body: JSON.stringify(value),
});
beforeEach(() => { vi.clearAllMocks(); fake.auth.mockResolvedValue([{ email: 'demo@example.test' }, null]); fake.run.mockResolvedValue({ source_kind: 'synthetic' }); });
describe('Local reference boundary', () => {
  it('authenticates before any execution', async () => {
    fake.auth.mockResolvedValue([null, new Response('denied', { status: 401 })]);
    expect((await POST(request())).status).toBe(401); expect(fake.run).not.toHaveBeenCalled();
  });
  it.each([['origin', 'http://evil.test'], ['sec-fetch-site', 'cross-site'], ['content-type', 'text/plain']])('rejects cross-origin or non-JSON requests %s', async (key, value) => {
    expect((await POST(request(body, { [key]: value }))).status).toBe(403); expect(fake.run).not.toHaveBeenCalled();
  });
  it.each([null, [], 1, { ...body, project_ref: 'customer' }, { ...body, root: 'C:/customer' }, { ...body, actor: 'admin' }, { ...body, confirmSynthetic: 'true' }, { ...body, variant: ['dev_test_prod'] }, { ...body, variant: 'prod' }])('rejects untrusted scope or confirmation %o', async value => {
    expect((await POST(request(value))).status).toBe(422); expect(fake.run).not.toHaveBeenCalled();
  });
  it('bounds malformed and oversized requests', async () => {
    expect((await POST(request({ ...body, extra: 'x'.repeat(2100) }))).status).toBe(413);
    expect((await POST(new Request('http://localhost:3000/api/local-reference', { method: 'POST', headers: { origin: 'http://localhost:3000', 'content-type': 'application/json' }, body: '{' }))).status).toBe(400);
    expect(fake.run).not.toHaveBeenCalled();
  });
  it.each(['dev_test_prod', 'dev_prod'])('passes only the fixed variant %s and forbids caching', async variant => {
    const result = await POST(request({ ...body, variant }));
    expect(result.status).toBe(200); expect(result.headers.get('cache-control')).toBe('private, no-store');
    expect(fake.run).toHaveBeenCalledExactlyOnceWith(variant);
  });
  it('serializes execution and releases the guard after a sanitized failure', async () => {
    let reject!: (reason: Error) => void;
    fake.run.mockImplementationOnce(() => new Promise((_, fail) => { reject = fail; }));
    const first = POST(request()); await vi.waitFor(() => expect(fake.run).toHaveBeenCalledTimes(1));
    expect((await POST(request())).status).toBe(409);
    reject(new Error('private host path and credentials must not escape'));
    const response = await first; expect(response.status).toBe(503);
    expect(await response.text()).not.toContain('credentials');
    expect((await POST(request())).status).toBe(200);
  });
});
