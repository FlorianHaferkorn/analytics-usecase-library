'use client';

import { useEffect, useState } from 'react';
import { ApprovalBadge } from './approval-badge';
import type { ApprovalAction, ApprovalRecord } from '@/lib/governance/approval-types';
import { StudioTextarea } from '@/components/ui/studio-data';
import { StudioButton, StudioEmptyState } from '@/components/ui/studio-page';

interface GovernanceComment {
  id: string;
  actor: string;
  comment: string;
  created_at: string;
}

interface GovernanceVersion {
  id: string;
  label: string;
  note: string | null;
  created_by: string;
  created_at: string;
}

interface ComparePayload {
  currentYaml: string;
  version: GovernanceVersion & { yaml_content: string };
}

interface Props {
  bracketId: string;
}

export function BracketGovernancePanel({ bracketId }: Props) {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [snapshotting, setSnapshotting] = useState(false);
  const [transitioning, setTransitioning] = useState<ApprovalAction | null>(null);
  const [comment, setComment] = useState('');
  const [justification, setJustification] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [lifecycle, setLifecycle] = useState<ApprovalRecord | null>(null);
  const [comments, setComments] = useState<GovernanceComment[]>([]);
  const [versions, setVersions] = useState<GovernanceVersion[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [compareData, setCompareData] = useState<ComparePayload | null>(null);
  const [restoringVersionId, setRestoringVersionId] = useState<string | null>(null);

  async function loadCompare(versionId: string) {
    const response = await fetch(`/api/governance/review?bracketId=${encodeURIComponent(bracketId)}&compareVersionId=${encodeURIComponent(versionId)}`);
    const json = await response.json() as { compare?: ComparePayload | null; error?: { message?: string } };
    if (!response.ok) {
      setError(json.error?.message ?? `HTTP ${response.status}`);
      return;
    }
    setCompareData(json.compare ?? null);
  }

  async function loadReviewData() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/governance/review?bracketId=${encodeURIComponent(bracketId)}`);
      const json = await response.json() as {
        lifecycle?: ApprovalRecord;
        comments?: GovernanceComment[];
        versions?: GovernanceVersion[];
        compare?: ComparePayload | null;
        error?: { message?: string };
      };
      if (!response.ok) {
        setError(json.error?.message ?? `HTTP ${response.status}`);
        return;
      }
      setLifecycle(json.lifecycle ?? null);
      setComments(json.comments ?? []);
      setVersions(json.versions ?? []);
      if (!selectedVersionId) {
        setCompareData(json.compare ?? null);
      }
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : 'Could not load governance data');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadReviewData();
  }, [bracketId]);

  useEffect(() => {
    if (!selectedVersionId) {
      setCompareData(null);
      return;
    }
    void (async () => {
      try {
        await loadCompare(selectedVersionId);
      } catch (compareError) {
        setError(compareError instanceof Error ? compareError.message : 'Compare failed');
      }
    })();
  }, [selectedVersionId, bracketId]);

  async function handleAddComment() {
    if (comment.trim().length < 3) return;
    setSubmitting(true);
    setError(null);
    try {
      const response = await fetch('/api/governance/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bracketId, action: 'comment', comment }),
      });
      const json = await response.json() as { error?: { message?: string } };
      if (!response.ok) {
        setError(json.error?.message ?? `HTTP ${response.status}`);
        return;
      }
      setComment('');
      await loadReviewData();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Comment failed');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSnapshot() {
    setSnapshotting(true);
    setError(null);
    try {
      const response = await fetch('/api/governance/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bracketId, action: 'snapshot', note: 'Manual registry snapshot' }),
      });
      const json = await response.json() as { error?: { message?: string } };
      if (!response.ok) {
        setError(json.error?.message ?? `HTTP ${response.status}`);
        return;
      }
      await loadReviewData();
    } catch (snapshotError) {
      setError(snapshotError instanceof Error ? snapshotError.message : 'Snapshot failed');
    } finally {
      setSnapshotting(false);
    }
  }

  async function handleLifecycle(action: ApprovalAction) {
    setTransitioning(action);
    setError(null);
    try {
      const response = await fetch('/api/governance/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bracketId,
          action,
          justification: justification.trim() || `Lifecycle transition: ${action}`,
        }),
      });
      const json = await response.json() as { error?: { message?: string } };
      if (!response.ok) {
        setError(json.error?.message ?? `HTTP ${response.status}`);
        return;
      }
      setJustification('');
      await loadReviewData();
    } catch (transitionError) {
      setError(transitionError instanceof Error ? transitionError.message : 'Lifecycle action failed');
    } finally {
      setTransitioning(null);
    }
  }

  async function handleRestore(versionId: string) {
    setRestoringVersionId(versionId);
    setError(null);
    try {
      const response = await fetch('/api/governance/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bracketId, action: 'restore', versionId, note: 'Restored from governance panel' }),
      });
      const json = await response.json() as { error?: { message?: string } };
      if (!response.ok) {
        setError(json.error?.message ?? `HTTP ${response.status}`);
        return;
      }
      await loadReviewData();
      if (selectedVersionId === versionId) {
        await loadCompare(versionId);
      }
    } catch (restoreError) {
      setError(restoreError instanceof Error ? restoreError.message : 'Restore failed');
    } finally {
      setRestoringVersionId(null);
    }
  }

  const availableActions: ApprovalAction[] = lifecycle?.status === 'draft'
    ? ['submit']
    : lifecycle?.status === 'review'
      ? ['approve', 'reject']
      : lifecycle?.status === 'approved'
        ? ['deprecate', 'reopen']
        : ['reopen'];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-2)', marginTop: 'var(--sp-2)' }}>
      <div style={{ padding: 'var(--sp-2)', backgroundColor: 'var(--slate-900)', borderRadius: 'var(--radius-md)', border: '1px solid var(--slate-700)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-1-5)' }}>
          <p style={{ margin: 0, fontSize: '0.6875rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Review</p>
          {lifecycle && <ApprovalBadge status={lifecycle.status} />}
        </div>
        {loading ? (
          <p style={{ margin: 0, fontSize: '0.8125rem', lineHeight: 1.5, color: 'var(--slate-500)' }}>Loading review context...</p>
        ) : (
          <>
            <StudioTextarea
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              placeholder="Add review comment"
              style={{ backgroundColor: 'var(--slate-950)', fontSize: '0.8125rem' }}
            />
            <div style={{ display: 'flex', gap: '8px', marginTop: 'var(--sp-1)' }}>
              <StudioButton
                onClick={handleAddComment}
                disabled={submitting || comment.trim().length < 3}
                tone="info"
                variant="primary"
                style={{
                  padding: '6px 10px',
                  fontSize: '0.6875rem',
                }}
              >
                {submitting ? 'Saving...' : 'Add comment'}
              </StudioButton>
              <StudioButton
                onClick={handleSnapshot}
                disabled={snapshotting}
                variant="ghost"
                style={{
                  padding: '6px 10px',
                  fontSize: '0.6875rem',
                }}
              >
                {snapshotting ? 'Snapshot...' : 'Create snapshot'}
              </StudioButton>
            </div>
            <div style={{ marginTop: 'var(--sp-2)', paddingTop: 'var(--sp-1-5)', borderTop: '1px solid var(--slate-800)' }}>
              <p style={{ margin: '0 0 8px', fontSize: '0.6875rem', color: 'var(--slate-500)' }}>Lifecycle action</p>
              <StudioTextarea
                value={justification}
                onChange={(event) => setJustification(event.target.value)}
                placeholder="Justification for lifecycle change"
                style={{ minHeight: '64px', backgroundColor: 'var(--slate-950)', fontSize: '0.8125rem' }}
              />
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: 'var(--sp-1)' }}>
                {availableActions.map((action) => (
                  <StudioButton
                    key={action}
                    onClick={() => void handleLifecycle(action)}
                    disabled={transitioning !== null}
                    variant="ghost"
                    style={{
                      padding: '5px 9px',
                      fontSize: '0.6875rem',
                      textTransform: 'capitalize',
                    }}
                  >
                    {transitioning === action ? `${action}...` : action}
                  </StudioButton>
                ))}
              </div>
            </div>
            {error && <p style={{ margin: 'var(--sp-1) 0 0', fontSize: '0.75rem', lineHeight: 1.5, color: 'var(--danger)' }}>{error}</p>}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: 'var(--sp-1-5)' }}>
              {comments.length === 0 ? (
                <StudioEmptyState title="No review comments yet" description="Add the first review note to capture governance context for this bracket." />
              ) : comments.map((entry) => (
                <div key={entry.id} style={{ padding: 'var(--sp-1-5)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--slate-950)', border: '1px solid var(--slate-800)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.625rem', color: 'var(--info)' }}>{entry.actor}</span>
                    <span style={{ fontSize: '0.625rem', color: 'var(--slate-500)' }}>{entry.created_at}</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--slate-200)', lineHeight: 1.6 }}>{entry.comment}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
      <div style={{ padding: 'var(--sp-2)', backgroundColor: 'var(--slate-900)', borderRadius: 'var(--radius-md)', border: '1px solid var(--slate-700)' }}>
        <p style={{ margin: '0 0 var(--sp-1-5)', fontSize: '0.6875rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Versions</p>
        {loading ? (
          <p style={{ margin: 0, fontSize: '0.8125rem', lineHeight: 1.5, color: 'var(--slate-500)' }}>Loading snapshots...</p>
        ) : versions.length === 0 ? (
          <StudioEmptyState title="No snapshots yet" description="Create a manual snapshot from the review panel to compare and restore governed states." />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {versions.map((version) => (
              <div key={version.id} style={{ padding: 'var(--sp-1-5)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--slate-950)', border: '1px solid var(--slate-800)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--slate-100)', fontWeight: 600 }}>{version.label}</span>
                  <span style={{ fontSize: '0.625rem', color: 'var(--slate-500)' }}>{version.created_at}</span>
                </div>
                <p style={{ margin: '4px 0 0', fontSize: '0.625rem', color: 'var(--slate-400)' }}>by {version.created_by}</p>
                {version.note && <p style={{ margin: '6px 0 0', fontSize: '0.75rem', lineHeight: 1.55, color: 'var(--slate-300)' }}>{version.note}</p>}
                <div style={{ display: 'flex', gap: '6px', marginTop: 'var(--sp-1)' }}>
                  <StudioButton
                    onClick={() => setSelectedVersionId(version.id)}
                    tone={selectedVersionId === version.id ? 'info' : 'default'}
                    variant={selectedVersionId === version.id ? 'secondary' : 'ghost'}
                    style={{ padding: '4px 8px', fontSize: '0.625rem' }}
                  >
                    Compare
                  </StudioButton>
                  <StudioButton
                    onClick={() => void handleRestore(version.id)}
                    disabled={restoringVersionId !== null}
                    tone="warning"
                    variant="ghost"
                    style={{ padding: '4px 8px', fontSize: '0.625rem' }}
                  >
                    {restoringVersionId === version.id ? 'Restoring...' : 'Restore'}
                  </StudioButton>
                </div>
              </div>
            ))}
          </div>
        )}
        {compareData && (
          <div style={{ marginTop: 'var(--sp-2)', paddingTop: 'var(--sp-1-5)', borderTop: '1px solid var(--slate-800)' }}>
            <p style={{ margin: '0 0 8px', fontSize: '0.6875rem', color: 'var(--slate-500)' }}>Current vs snapshot</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <p style={{ margin: '0 0 6px', fontSize: '0.625rem', color: 'var(--slate-400)' }}>Current</p>
                <pre style={{ margin: 0, padding: 'var(--sp-1-5)', minHeight: '160px', maxHeight: '220px', overflow: 'auto', backgroundColor: 'var(--slate-950)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--slate-800)', color: 'var(--slate-300)', fontSize: '0.6875rem', lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>{compareData.currentYaml}</pre>
              </div>
              <div>
                <p style={{ margin: '0 0 6px', fontSize: '0.625rem', color: 'var(--slate-400)' }}>{compareData.version.label}</p>
                <pre style={{ margin: 0, padding: 'var(--sp-1-5)', minHeight: '160px', maxHeight: '220px', overflow: 'auto', backgroundColor: 'var(--slate-950)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--slate-800)', color: 'var(--slate-300)', fontSize: '0.6875rem', lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>{compareData.version.yaml_content}</pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}