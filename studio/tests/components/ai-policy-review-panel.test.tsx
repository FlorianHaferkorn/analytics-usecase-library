import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { stringify } from 'yaml';
import { AiPolicyReviewPanel } from '@/components/delivery/ai-policy-review-panel';
import type { PackageSnapshot } from '@/lib/bridge/project-package-repository';

const fetchMock = vi.fn();
const hash = 'a'.repeat(64);
const file = (path: string, data: unknown) => ({ path, sha256: hash, size: 1, encoding: 'base64' as const,
  contentBase64: btoa(stringify(data)) });
const snapshot: PackageSnapshot = {
  revision: { revision_hash: hash, package_id: 'package_demo', project_ref: 'project_demo', revision: 1, parent_revision_hash: null },
  files: [
    file('package.yaml', { modules: [{ module_type: 'ai_data_handling', path: 'governance/ai.yaml' }] }),
    file('governance/ai.yaml', { routes: [{ id: 'discovery_public', task_role: 'source-discovery',
      profile: { provider: 'local', data_handling: { processing_boundary: 'local' } },
      allowed_inputs: [{ classification: 'public', data_form: 'metadata', purpose: 'studio_authoring' }],
      provider_region: 'local', expires_at: '2030-01-01T00:00:00Z' }] }),
  ],
};

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
  fetchMock.mockResolvedValue(new Response(JSON.stringify({ reviews: [], egressEnabled: false }), { status: 200 }));
});

describe('AI policy review panel', () => {
  it('shows the pinned route, independent-review requirement and no egress claim', async () => {
    render(<AiPolicyReviewPanel projectId="project_demo" snapshot={snapshot} dirty={false} />);
    expect(await screen.findByLabelText('AI route')).toBeTruthy();
    expect(screen.getByText(/Approval here does not enable model calls/)).toBeTruthy();
    expect(screen.getByText(/public \/ metadata \/ studio_authoring/)).toBeTruthy();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
  });

  it('will not submit an unsaved policy edit', async () => {
    render(<AiPolicyReviewPanel projectId="project_demo" snapshot={snapshot} dirty />);
    const submit = screen.getByRole('button', { name: 'Submit policy review' }) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);
    fireEvent.click(submit);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  });
});
