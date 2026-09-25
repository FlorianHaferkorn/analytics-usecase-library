'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { parse } from 'yaml';
import { StudioButton, StudioPanel } from '@/components/ui/studio-page';
import { StudioSelect, StudioTextarea } from '@/components/ui/studio-data';
import type { PackageSnapshot } from '@/lib/bridge/project-package-repository';

interface RoutePreview {
  id: string;
  task_role: string;
  profile: { provider: string; data_handling: { processing_boundary: string } };
  allowed_inputs: Array<{ classification: string; data_form: string; purpose: string }>;
  provider_region: string | null;
  expires_at: string | null;
}
interface Review {
  id: string;
  revision_hash: string;
  route_id: string;
  status: 'pending' | 'approved' | 'rejected';
  submitted_by: string;
  reviewed_by: string | null;
  rationale: string | null;
}

function policyRoutes(snapshot: PackageSnapshot): RoutePreview[] {
  try {
    const decode = (content: string) => new TextDecoder('utf-8', { fatal: true }).decode(
      Uint8Array.from(atob(content), (character) => character.charCodeAt(0)));
    const manifestFile = snapshot.files.find((file) => file.path === 'package.yaml');
    if (!manifestFile) return [];
    const manifest = parse(decode(manifestFile.contentBase64)) as { modules?: Array<{ module_type: string; path: string }> };
    const modulePath = manifest.modules?.find((entry) => entry.module_type === 'ai_data_handling')?.path;
    const policyFile = snapshot.files.find((file) => file.path === modulePath);
    if (!policyFile) return [];
    const policy = parse(decode(policyFile.contentBase64)) as { routes?: RoutePreview[] };
    return Array.isArray(policy.routes) ? policy.routes.filter((route) => typeof route.id === 'string') : [];
  } catch { return []; }
}

export function AiPolicyReviewPanel({ projectId, snapshot, dirty }: {
  projectId: string; snapshot: PackageSnapshot; dirty: boolean;
}) {
  const routes = useMemo(() => policyRoutes(snapshot), [snapshot]);
  const revisionHash = snapshot.revision.revision_hash;
  const [routeId, setRouteId] = useState(routes[0]?.id ?? '');
  const [reviews, setReviews] = useState<Review[]>([]);
  const [rationale, setRationale] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('A separate administrator must attest this exact policy and package revision.');
  const selected = routes.find((route) => route.id === routeId) ?? routes[0];
  const current = reviews.find((review) => review.revision_hash === revisionHash && review.route_id === selected?.id);
  const endpoint = `/api/projects/${encodeURIComponent(projectId)}/ai-policy-reviews`;

  const refresh = useCallback(async () => {
    try {
      const response = await fetch(endpoint, { cache: 'no-store' });
      if (!response.ok) throw new Error('Review status unavailable.');
      const body = await response.json() as { reviews?: Review[] };
      setReviews(body.reviews ?? []);
    } catch { setMessage('Review status unavailable. Existing approvals cannot be assumed.'); }
  }, [endpoint]);
  useEffect(() => { if (routes.length) void refresh(); }, [refresh, routes.length]);
  if (!routes.length) return null;

  async function act(action: 'submit' | 'approve' | 'reject') {
    if (!selected || dirty) return;
    setBusy(true);
    setMessage('Checking the saved policy and package revision…');
    try {
      const response = await fetch(endpoint, {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify(action === 'submit'
          ? { action, revisionHash, routeId: selected.id }
          : { action, reviewId: current?.id, rationale }),
      });
      const body = await response.json() as { error?: { message?: string }; review?: Review };
      if (!response.ok) throw new Error(body.error?.message ?? 'Review action failed.');
      await refresh();
      setMessage(action === 'submit' ? 'Submitted for independent review.'
        : action === 'approve' ? 'Policy review recorded. AI processing remains blocked until the remaining runtime gates pass.'
          : 'Policy review rejected; the author may submit a corrected revision.');
      setRationale('');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Review action failed.'); }
    finally { setBusy(false); }
  }

  return <StudioPanel title="AI data-handling review" description="Independent review of a route in this immutable Project Package revision. Approval here does not enable model calls." compactHeader>
    <div style={{ display: 'grid', gap: 'var(--gap)', padding: 'var(--space-4)' }}>
      <label style={{ display: 'grid', gap: 'var(--space-1)' }}>
        <span>AI route</span>
        <StudioSelect aria-label="AI route" value={selected?.id ?? ''} onChange={(event) => setRouteId(event.target.value)}>
          {routes.map((route) => <option key={route.id} value={route.id}>{route.id} · {route.task_role}</option>)}
        </StudioSelect>
      </label>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-3)', color: 'var(--ink-3)', fontSize: 'var(--text-sm)' }}>
        <span>Version {revisionHash.slice(0, 12)}</span>
        <span>Provider {selected?.profile?.provider ?? '—'}</span>
        <span>Boundary {selected?.profile?.data_handling?.processing_boundary ?? '—'}</span>
        <span>Region {selected?.provider_region ?? 'unconfirmed'}</span>
        <span>Expires {selected?.expires_at ?? 'unconfirmed'}</span>
      </div>
      <p style={{ margin: 0, color: 'var(--ink-3)', fontSize: 'var(--text-sm)' }}>
        Allowed inputs: {selected?.allowed_inputs?.map((item) => `${item.classification} / ${item.data_form} / ${item.purpose}`).join('; ') || 'none'}.
        Verify the full policy, provider evidence and decision in the saved package before approving.
      </p>
      <p style={{ margin: 0 }}>Review: <strong>{current?.status ?? 'not submitted'}</strong>
        {current?.submitted_by ? ` · submitted by ${current.submitted_by}` : ''}
        {current?.reviewed_by ? ` · reviewed by ${current.reviewed_by}` : ''}</p>
      <StudioTextarea aria-label="AI policy review rationale" value={rationale} maxLength={2000}
        placeholder="Explain the review decision and cite the verified evidence (20–2000 characters)."
        onChange={(event) => setRationale(event.target.value)} />
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
        <StudioButton disabled={dirty || busy || current?.status === 'pending' || current?.status === 'approved'} onClick={() => void act('submit')}>Submit policy review</StudioButton>
        <StudioButton disabled={dirty || busy || current?.status !== 'pending' || rationale.trim().length < 20} onClick={() => void act('approve')}>Approve as admin</StudioButton>
        <StudioButton disabled={dirty || busy || current?.status !== 'pending' || rationale.trim().length < 20} onClick={() => void act('reject')}>Reject as admin</StudioButton>
      </div>
      <p role="status" style={{ margin: 0, color: 'var(--ink-3)', fontSize: 'var(--text-sm)' }}>{dirty ? 'Save the package before submitting or reviewing.' : message}</p>
    </div>
  </StudioPanel>;
}
