'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { SourcePanel } from '@/components/discovery/source-panel';
import { DiscoveryChat } from '@/components/discovery/discovery-chat';
import { ProjectCandidatePanel } from '@/components/discovery/project-candidate-panel';
import { DiscoveryTransferPanel } from '@/components/discovery/discovery-transfer-panel';
import { StudioButton, StudioEmptyState, StudioPage, StudioPageHeader } from '@/components/ui/studio-page';
import { useProjectStore } from '@/lib/store/project-store';
import { emptyDiscovery, extractDiscoveryCandidates, mergeDiscoveryCandidates, detachRemovedSources, validateDiscovery, type DiscoveryDocument } from '@/lib/discovery/document';
import type { DiscoverySnapshot } from '@/lib/db/discovery-repo';
import styles from './discovery-client.module.css';

interface LocalDraft { document: DiscoveryDocument; revision: string | null }
type DraftCache = Map<string, LocalDraft>;

export function DiscoveryClient() {
  const projectId = useProjectStore((state) => state.projectId);
  const projectName = useProjectStore((state) => state.projectName);
  const [drafts] = useState<DraftCache>(() => new Map());
  if (!projectId) return <StudioEmptyState title="Select a project" description="Discovery evidence must belong to a project. No shared or default fallback is used." />;
  return <ProjectDiscovery key={projectId} projectId={projectId} projectName={projectName} drafts={drafts} />;
}

function ProjectDiscovery({ projectId, projectName, drafts }: { projectId: string; projectName: string; drafts: DraftCache }) {
  const [snapshot, setSnapshot] = useState<DiscoverySnapshot | null>(null);
  const [document, setDocument] = useState<DiscoveryDocument>(emptyDiscovery);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busy, setBusy] = useState(false);
  const [canEdit, setCanEdit] = useState(false);
  const [error, setError] = useState('');
  const [loadError, setLoadError] = useState('');
  const [reload, setReload] = useState(0);
  const alive = useRef(true);
  const dirty = snapshot !== null && JSON.stringify(snapshot.document) !== JSON.stringify(document);
  const endpoint = `/api/projects/${encodeURIComponent(projectId)}/discovery`;

  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const response = await fetch(endpoint, { signal: controller.signal, cache: 'no-store' });
        const body = await response.json();
        if (!response.ok) throw new Error(response.status === 403 ? 'Project access required. Ask the project administrator for a role; no evidence has been loaded.' : response.status === 401 ? 'Sign in to access this project’s discovery evidence.' : body.error?.message ?? 'Discovery could not be loaded.');
        if (body.projectId !== projectId || !validateDiscovery(body.document).document) throw new Error('The returned discovery draft does not match this project or schema.');
        if (controller.signal.aborted) return;
        const next = body as DiscoverySnapshot;
        setCanEdit(body.canEdit === true);
        setSnapshot(next);
        const local = drafts.get(projectId);
        setDocument(local?.document ?? next.document);
        if (local && local.revision !== next.revision) setError('The server draft changed while you were away. Download your local evidence before reloading; saving is blocked until the conflict is resolved.');
        if (local) setSnapshot({ ...next, revision: local.revision });
      } catch (cause) { if (!controller.signal.aborted) setLoadError(cause instanceof Error ? cause.message : 'Discovery could not be loaded.'); }
      finally { if (!controller.signal.aborted) setLoading(false); }
    })();
    return () => controller.abort();
  }, [endpoint, projectId, reload, drafts]);

  useEffect(() => {
    if (dirty && snapshot) drafts.set(projectId, { document, revision: snapshot.revision });
    else if (snapshot) drafts.delete(projectId);
    window.dispatchEvent(new CustomEvent('studio:unsaved-discovery', { detail: { projectId, dirty } }));
    const guard = (event: BeforeUnloadEvent) => { if (dirty || busy) event.preventDefault(); };
    window.addEventListener('beforeunload', guard);
    return () => { window.removeEventListener('beforeunload', guard); window.dispatchEvent(new CustomEvent('studio:unsaved-discovery', { detail: { projectId, dirty: false } })); };
  }, [dirty, busy, projectId, document, snapshot, drafts]);

  const updateDocument = useCallback((update: (previous: DiscoveryDocument) => DiscoveryDocument) => {
    setDocument((previous) => update(previous));
  }, []);

  const save = async () => {
    if (!snapshot || saving || busy || !dirty || !canEdit) return;
    setSaving(true); setError('');
    try {
      const response = await fetch(endpoint, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ document, expectedRevision: snapshot.revision }) });
      const body = await response.json();
      if (!response.ok) throw new Error(response.status === 403 ? 'An editor role is required to save. Your local draft remains available for download.' : [body.error?.message ?? 'Could not save. Your local draft has been retained.', ...(Array.isArray(body.error?.details) ? body.error.details.slice(0, 3) : [])].join(' '));
      if (body.projectId !== projectId || !validateDiscovery(body.document).document) throw new Error('Unexpected save response. Download your local evidence and reload.');
      if (alive.current) setSnapshot(body as DiscoverySnapshot);
    } catch (cause) { if (alive.current) setError(cause instanceof Error ? cause.message : 'Save failed.'); }
    finally { if (alive.current) setSaving(false); }
  };
  const download = () => {
    const blob = new Blob([JSON.stringify({ projectId, status: 'draft', exportedAt: new Date().toISOString(), savedRevision: snapshot?.revision ?? null, hasUnsavedChanges: dirty, document }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = window.document.createElement('a'); link.href = url; link.download = `discovery_${projectId.replace(/[^a-z0-9_-]/gi, '_')}_draft.json`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const retry = () => {
    if (dirty && !window.confirm('Reloading replaces this local draft. Download it first if you need to keep it. Continue?')) return;
    drafts.delete(projectId); setLoading(true); setLoadError(''); setError(''); setReload((value) => value + 1);
  };
  const candidates = document.candidates;
  const steps = [
    { title: 'Evidence', meta: `${document.sources.length} sources in this project`, complete: document.sources.length > 0 },
    { title: 'Extract', meta: candidates.length ? `${candidates.length} draft candidate${candidates.length === 1 ? '' : 's'}` : document.lastResponse ? 'No candidates yet; refine your question' : 'Sources ready for extraction', complete: candidates.length > 0 },
    { title: 'Govern', meta: 'Verify evidence and approve through the project package', complete: false },
  ];
  return <StudioPage width="wide">
    <StudioPageHeader eyebrow="Project / Intake" title="Discovery" description={`Evidence and draft candidates for ${projectName}. Saved drafts do not change governed definitions.`} badge={`${document.sources.length} sources`} tone="info" />
    {loading ? <StudioEmptyState title="Loading project evidence" description="Checking project access and the saved Discovery draft." /> : loadError ? <StudioEmptyState title="Discovery unavailable" description={<><span>{loadError}</span><StudioButton onClick={retry}>Try again</StudioButton></>} /> : <>
      <div className={styles.draftBar}>
        <span role="status">{!canEdit ? 'Read-only project access · an editor role is required to change evidence' : saving ? 'Saving draft…' : busy ? 'Extracting; save when the response is complete' : dirty ? 'Unsaved draft · save before leaving' : snapshot?.revision ? 'Draft saved in this project' : 'No draft saved yet'}</span>
        <div className={styles.draftActions}><StudioButton onClick={download} disabled={busy}>Download draft evidence</StudioButton><StudioButton onClick={retry} disabled={saving || busy}>Reload</StudioButton><StudioButton onClick={() => void save()} disabled={!canEdit || !dirty || saving || busy} variant="primary">Save draft</StudioButton></div>
      </div>
      {error && <p role="alert" className={styles.draftError}>{error}</p>}
      <div className={styles.progress} aria-label="Discovery workflow">{steps.map((step, index) => <div key={step.title} aria-current={index === (candidates.length ? 2 : document.sources.length || document.lastResponse ? 1 : 0) ? 'step' : undefined} className={`${styles.step}${step.complete ? ` ${styles.stepComplete}` : ''}`}><span className={styles.stepNumber}>{`0${index + 1}`}</span><div><div className={styles.stepTitle}>{step.title}</div><div className={styles.stepMeta}>{step.meta}</div></div></div>)}</div>
      <div className={styles.workspace}>
        <div className={styles.pane}><SourcePanel readOnly={!canEdit || busy || saving} sources={document.sources} onAddSource={(source) => updateDocument((previous) => ({ ...previous, sources: [...previous.sources, source] }))} onRemoveSource={(id) => updateDocument((previous) => {
          const sources = previous.sources.filter((source) => source.id !== id);
          return { ...previous, sources, candidates: detachRemovedSources(previous.candidates, sources) };
        })} /></div>
        <div className={styles.pane}><DiscoveryChat key={`${projectId}:${reload}`} readOnly={!canEdit || saving} projectId={projectId} sources={document.sources} initialMessages={document.messages} context={document.sources.map((source) => source.content).join('\n\n')} onBusyChange={setBusy} onExtract={(content) => updateDocument((previous) => ({ ...previous, lastResponse: content, candidates: mergeDiscoveryCandidates(previous.candidates, extractDiscoveryCandidates(content, previous.sources)) }))} onMessagesChange={(messages) => updateDocument((previous) => ({ ...previous, messages }))} /></div>
        <div className={styles.pane}><ProjectCandidatePanel candidates={candidates} review={<DiscoveryTransferPanel key={snapshot?.revision ?? 'unsaved'} projectId={projectId} revision={snapshot?.revision ?? null} candidates={candidates} disabled={!canEdit || dirty || saving || busy} />} /></div>
      </div>
    </>}
  </StudioPage>;
}
