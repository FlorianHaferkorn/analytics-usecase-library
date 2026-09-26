import { beforeEach, describe, expect, it, vi } from 'vitest';

const h = vi.hoisted(() => ({
  role: vi.fn(), project: vi.fn(), load: vi.fn(), head: vi.fn(), candidate: vi.fn(),
  list: vi.fn(), get: vi.fn(), submit: vi.fn(), finish: vi.fn(),
}));
vi.mock('@/lib/auth/require-role', () => ({ requireRole: h.role }));
vi.mock('@/lib/db/project-repo', () => ({ getProject: h.project }));
vi.mock('@/lib/bridge/project-package-repository', () => ({ loadProjectPackage: h.load, getPackageHead: h.head }));
vi.mock('@/lib/ai/policy-review', () => ({ aiPolicyReviewCandidate: h.candidate }));
vi.mock('@/lib/db/ai-policy-review-repo', () => ({
  AiPolicyReviewError: class extends Error {}, listAiPolicyReviews: h.list,
  getAiPolicyReview: h.get, submitAiPolicyReview: h.submit, finishAiPolicyReview: h.finish,
}));

const projectId = 'project_demo';
const revisionHash = 'a'.repeat(64);
const reviewId = '11111111-1111-4111-8111-111111111111';
const context = { params: Promise.resolve({ projectId }) };
const review = { id: reviewId, project_id: projectId, revision_hash: revisionHash,
  route_id: 'discovery_public', route_hash: 'b'.repeat(64), decision_ref: 'ai_decision',
  submitted_by: 'editor@example.com', status: 'pending' };

function post(body: unknown) {
  return new Request(`http://local/api/projects/${projectId}/ai-policy-reviews`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  h.role.mockResolvedValue([{ email: 'reviewer@example.com' }, null]);
  h.project.mockReturnValue({ id: projectId });
  h.load.mockResolvedValue({ ok: true, value: { revision: { revision_hash: revisionHash }, files: [] } });
  h.head.mockResolvedValue({ ok: true, value: { revision_hash: revisionHash } });
  h.candidate.mockReturnValue({ projectId, revisionHash, routeId: 'discovery_public', routeHash: review.route_hash,
    decisionRef: 'ai_decision' });
  h.get.mockReturnValue(review);
  h.submit.mockReturnValue(review);
  h.finish.mockReturnValue({ ...review, status: 'approved' });
  h.list.mockReturnValue([review]);
});

describe('AI policy review API', () => {
  it('allows a viewer to inspect receipts but never reports model egress enabled', async () => {
    const { GET } = await import('@/app/api/projects/[projectId]/ai-policy-reviews/route');
    const response = await GET(new Request('http://local'), context);
    expect(response.status).toBe(200);
    expect(h.role).toHaveBeenCalledWith('viewer', projectId);
    expect((await response.json()).egressEnabled).toBe(false);
  });

  it('submits only current, pinned package content as an editor', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/ai-policy-reviews/route');
    const response = await POST(post({ action: 'submit', revisionHash, routeId: 'discovery_public' }), context);
    expect(response.status).toBe(201);
    expect(h.role).toHaveBeenCalledWith('editor', projectId);
    expect(h.candidate).toHaveBeenCalledOnce();
    expect(h.submit).toHaveBeenCalledOnce();
    expect((await response.json()).egressEnabled).toBe(false);
  });

  it('rejects a stale submission before storing a review', async () => {
    h.load.mockResolvedValue({ ok: true, value: { revision: { revision_hash: 'c'.repeat(64) }, files: [] } });
    const { POST } = await import('@/app/api/projects/[projectId]/ai-policy-reviews/route');
    const response = await POST(post({ action: 'submit', revisionHash, routeId: 'discovery_public' }), context);
    expect(response.status).toBe(409);
    expect(h.submit).not.toHaveBeenCalled();
  });

  it('requires admin and rechecks HEAD before approving', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/ai-policy-reviews/route');
    h.head.mockResolvedValue({ ok: true, value: { revision_hash: 'c'.repeat(64) } });
    const response = await POST(post({ action: 'approve', reviewId, rationale: 'Provider and input boundary reviewed against evidence.' }), context);
    expect(response.status).toBe(409);
    expect(h.role).toHaveBeenCalledWith('admin', projectId);
    expect(h.finish).not.toHaveBeenCalled();
  });

  it('does not let an editor invoke the review decision', async () => {
    h.role.mockResolvedValue([null, new Response('Forbidden', { status: 403 })]);
    const { POST } = await import('@/app/api/projects/[projectId]/ai-policy-reviews/route');
    const response = await POST(post({ action: 'approve', reviewId, rationale: 'Provider and input boundary reviewed against evidence.' }), context);
    expect(response.status).toBe(403);
    expect(h.role).toHaveBeenCalledWith('admin', projectId);
    expect(h.get).not.toHaveBeenCalled();
    expect(h.finish).not.toHaveBeenCalled();
  });

  it('approves only by saved review ID with explicit rationale', async () => {
    const { POST } = await import('@/app/api/projects/[projectId]/ai-policy-reviews/route');
    const response = await POST(post({ action: 'approve', reviewId, rationale: 'Provider and input boundary reviewed against evidence.' }), context);
    expect(response.status).toBe(200);
    expect(h.finish).toHaveBeenCalledWith(projectId, reviewId, 'approve', 'reviewer@example.com',
      'Provider and input boundary reviewed against evidence.', expect.objectContaining({ routeHash: review.route_hash }));
    expect((await response.json()).egressEnabled).toBe(false);
  });
});
