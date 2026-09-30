'use client';

/**
 * RefinementProposalsPanel — Wirkungs-Loop review surface (I-8.2/I-8.3,
 * ADR-0009 §5, Studio-Approval-Verdrahtung).
 *
 * The Python core (wirkung.py + refinement.py) already computes attribution and
 * derives proposals honestly; this panel is the missing Studio surface: run a
 * computation (governed refcalc baseline + supplied after-values), then
 * approve/reject any derived proposal through the same admin-gated, audited
 * gate bracket approvals use. Nothing here mutates the core — proposals stay
 * `pending_review` until a human decides.
 */

import { useState } from 'react';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import { StudioFormField, StudioFormGrid, StudioInput, StudioInlineStat } from '@/components/ui/studio-data';

type Method = 'before_after' | 'diff_in_diff' | 'holdout';

interface AttributionRecord {
  actionCodeId: string;
  kpiId: string;
  method: Method;
  status: 'computed' | 'uncomputed';
  t0: number | null;
  t1: number | null;
  delta: number | null;
  note: string;
}

interface RefinementLifecycle {
  proposal_key: string;
  status: 'pending_review' | 'approved' | 'rejected';
  decided_by: string | null;
}

interface RefinementProposal {
  actionCodeId: string;
  kpiId: string;
  trigger: 'no_effect' | 'material_effect';
  relChange: number;
  rationale: string;
  lifecycle?: RefinementLifecycle;
}

interface AttributeResponse {
  ok: boolean;
  available: boolean;
  outcomeKpis: string[];
  attribution: AttributionRecord[];
  refinements: RefinementProposal[];
  error?: string;
}

export function RefinementProposalsPanel() {
  const [useCase, setUseCase] = useState('COM-001');
  const [actionCodeId, setActionCodeId] = useState('C-M2.1');
  const [kpiId, setKpiId] = useState('KPI-COM-013');
  const [t1Value, setT1Value] = useState('');
  const [loading, setLoading] = useState(false);
  const [deciding, setDeciding] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AttributeResponse | null>(null);

  async function compute() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/wirkung/attribute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          useCase,
          actionCodeId,
          t1: kpiId && t1Value !== '' ? { [kpiId]: Number(t1Value) } : {},
        }),
      });
      const json = (await response.json()) as Record<string, unknown>;
      if (!response.ok) {
        const apiErr = json.error as { message?: string } | undefined;
        setError(apiErr?.message ?? `HTTP ${response.status}`);
        setResult(null);
        return;
      }
      const attributeResult = json as unknown as AttributeResponse;
      if (attributeResult.ok === false) {
        setError(attributeResult.error ?? `HTTP ${response.status}`);
        setResult(null);
        return;
      }
      setResult(attributeResult);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : 'Attribution failed');
    } finally {
      setLoading(false);
    }
  }

  async function decide(proposal: RefinementProposal, action: 'approve' | 'reject') {
    const key = `${proposal.actionCodeId}::${proposal.kpiId}`;
    setDeciding(key);
    setError(null);
    try {
      const response = await fetch('/api/wirkung/refinements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ proposalKey: key, action, justification: `Decided from Studio: ${action}` }),
      });
      const json = await response.json() as { proposal?: RefinementLifecycle; error?: { message?: string } };
      if (!response.ok) {
        setError(json.error?.message ?? `HTTP ${response.status}`);
        return;
      }
      setResult((prev) => prev && {
        ...prev,
        refinements: prev.refinements.map((p) =>
          p.actionCodeId === proposal.actionCodeId && p.kpiId === proposal.kpiId
            ? { ...p, lifecycle: json.proposal }
            : p,
        ),
      });
    } finally {
      setDeciding(null);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <StudioPanel
        title="Compute Attribution"
        description="Governed refcalc baseline (t0) for the use case + a supplied after-value (t1) for one outcome KPI. No live KPI feed exists yet (ADR-0009 O-1) — this is the honest, explicit-input path until one does."
      >
        <StudioFormGrid columns="1fr 1fr 1fr 1fr">
          <StudioFormField label="Use Case"><StudioInput value={useCase} onChange={(e) => setUseCase(e.target.value)} placeholder="COM-001" /></StudioFormField>
          <StudioFormField label="Action Code"><StudioInput value={actionCodeId} onChange={(e) => setActionCodeId(e.target.value)} placeholder="C-M2.1" /></StudioFormField>
          <StudioFormField label="KPI (after-value for)"><StudioInput value={kpiId} onChange={(e) => setKpiId(e.target.value)} placeholder="KPI-COM-013" /></StudioFormField>
          <StudioFormField label="t1 value"><StudioInput type="number" step="any" value={t1Value} onChange={(e) => setT1Value(e.target.value)} placeholder="0.45" /></StudioFormField>
        </StudioFormGrid>
        <StudioButton onClick={compute} disabled={loading || !useCase || !actionCodeId} variant="primary" tone="success" style={{ marginTop: '12px' }}>
          {loading ? 'Computing...' : 'Compute Attribution'}
        </StudioButton>
        {error && <StudioInlineStat>{error}</StudioInlineStat>}
      </StudioPanel>

      {result && (
        <StudioPanel title="Attribution" description={`Outcome KPIs: ${result.outcomeKpis.join(', ') || 'none'}`}>
          {result.attribution.length === 0 ? (
            <StudioEmptyState title="No attribution records" description="This action code has no outcome KPIs, or nothing was computed." />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {result.attribution.map((r) => (
                <div key={r.kpiId} style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--panel)', border: '1px solid var(--line)', fontSize: '0.75rem' }}>
                  <strong>{r.kpiId}</strong> — {r.status}
                  {r.status === 'computed' ? ` (t0=${r.t0}, t1=${r.t1}, delta=${r.delta})` : ''}
                  <div style={{ color: 'var(--ink-3)', marginTop: '2px' }}>{r.note}</div>
                </div>
              ))}
            </div>
          )}
        </StudioPanel>
      )}

      {result && (
        <StudioPanel title="Refinement Proposals" description="Reviewable, never auto-applied (ADR-0009). Approve requires an admin role, same as bracket approval." tone="warning">
          {result.refinements.length === 0 ? (
            <StudioEmptyState title="No proposals" description="No computed record crossed the no-effect/material-effect thresholds." />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {result.refinements.map((p) => {
                const key = `${p.actionCodeId}::${p.kpiId}`;
                const status = p.lifecycle?.status ?? 'pending_review';
                return (
                  <div key={key} style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--panel)', border: '1px solid var(--line)', fontSize: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong>{p.kpiId} — {p.trigger}</strong>
                      <span style={{ fontSize: 'var(--text-2xs)', textTransform: 'uppercase', color: status === 'pending_review' ? 'var(--warning)' : status === 'approved' ? 'var(--accent)' : 'var(--danger)' }}>
                        {status}
                      </span>
                    </div>
                    <div style={{ color: 'var(--ink-3)', marginTop: '2px' }}>{p.rationale}</div>
                    {status === 'pending_review' && (
                      <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                        <StudioButton onClick={() => decide(p, 'approve')} disabled={deciding === key} tone="success" variant="primary">
                          Approve
                        </StudioButton>
                        <StudioButton onClick={() => decide(p, 'reject')} disabled={deciding === key} variant="ghost">
                          Reject
                        </StudioButton>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </StudioPanel>
      )}
    </div>
  );
}
