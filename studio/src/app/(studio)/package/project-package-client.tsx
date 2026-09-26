'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { StudioTextarea } from '@/components/ui/studio-data';
import {
  StudioButton,
  StudioEmptyState,
  StudioMetric,
  StudioMetricBar,
  StudioPage,
  StudioPageHeader,
  StudioPanel,
} from '@/components/ui/studio-page';
import type {
  PackageRevisionSummary,
  PackageSnapshot,
  PackageStructuralDiff,
} from '@/lib/bridge/project-package-repository';
import type { PackageFile } from '@/lib/project-package/package-files';
import { useProjectStore } from '@/lib/store/project-store';
import { ProjectReleasePanel } from '@/components/delivery/project-release-panel';
import { AiPolicyReviewPanel } from '@/components/delivery/ai-policy-review-panel';
import { ExternalHandoffPanel } from '@/components/delivery/external-handoff-panel';

type LoadState = 'loading' | 'ready' | 'missing' | 'error';

interface ApiErrorBody {
  error?: { message?: string };
}

const TEXT_FILE = /\.(?:ya?ml|json|md|txt|csv|sql|py|ts|tsx|js|jsx|toml)$/i;

async function responseMessage(response: Response): Promise<string> {
  try {
    const body = await response.json() as ApiErrorBody;
    return body.error?.message || `${response.status} ${response.statusText}`;
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

function decodeText(file: PackageFile): string | null {
  if (!TEXT_FILE.test(file.path)) return null;
  try {
    const binary = atob(file.contentBase64);
    const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
    return new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  } catch {
    return null;
  }
}

async function encodeText(path: string, value: string): Promise<PackageFile> {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  const sha256 = [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('');
  let binary = '';
  const stride = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += stride) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + stride));
  }
  return {
    path,
    sha256,
    size: bytes.byteLength,
    encoding: 'base64',
    contentBase64: btoa(binary),
  };
}

function shortHash(value: string | null | undefined): string {
  return value ? value.slice(0, 12) : 'none';
}

export function ProjectPackageClient() {
  const projectId = useProjectStore((state) => state.projectId);
  const projectName = useProjectStore((state) => state.projectName);
  const packageRevisionHash = useProjectStore((state) => state.packageRevisionHash);
  const setPackageRevisionHash = useProjectStore((state) => state.setPackageRevisionHash);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [snapshot, setSnapshot] = useState<PackageSnapshot | null>(null);
  const [draftTexts, setDraftTexts] = useState<Record<string, string>>({});
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [message, setMessage] = useState('Loading the saved project version…');
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [diff, setDiff] = useState<PackageStructuralDiff | null>(null);
  const importInput = useRef<HTMLInputElement>(null);
  const loadRequest = useRef(0);

  const load = useCallback(async (latest = false) => {
    const request = ++loadRequest.current;
    setLoadState('loading');
    setErrorStatus(null);
    setSnapshot(null);
    setDraftTexts({});
    setDiff(null);
    setMessage('Loading the saved project version…');
    try {
    const revisionQuery = !latest && packageRevisionHash ? `?revision=${packageRevisionHash}` : '';
    const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/package${revisionQuery}`, { cache: 'no-store' });
    if (request !== loadRequest.current) return;
    if (response.status === 404) {
      setSnapshot(null);
      setDraftTexts({});
      setSelectedPath(null);
      setLoadState('missing');
      setMessage('No Project Package history exists for this project yet.');
      return;
    }
    if (!response.ok) {
      const detail = await responseMessage(response);
      if (request !== loadRequest.current) return;
      setLoadState('error');
      setErrorStatus(response.status);
      setMessage(response.status === 401
        ? 'Sign in to view the saved files and revision history for this project.'
        : response.status === 403
          ? 'Your account does not have access to this project package. Select a project you can access, or ask your project administrator for access.'
          : `The package could not be loaded. ${detail}`);
      return;
    }
    const value = await response.json() as PackageSnapshot;
    if (request !== loadRequest.current) return;
    if (value.revision.project_ref !== projectId) throw new Error('Package project identity does not match this project');
    setPackageRevisionHash(value.revision.revision_hash);
    const textFiles = Object.fromEntries(
      value.files.flatMap((file) => {
        if (/^handoff\/[a-z][a-z0-9_]{0,63}\.json$/.test(file.path)) return [];
        const text = decodeText(file);
        return text === null ? [] : [[file.path, text]];
      }),
    );
    setSnapshot(value);
    setDraftTexts(textFiles);
    setSelectedPath((current) => (
      current && Object.hasOwn(textFiles, current) ? current : Object.keys(textFiles)[0] || null
    ));
    setDiff(null);
    setLoadState('ready');
    setMessage(`Loaded revision ${value.revision.revision}.`);
    } catch {
      if (request !== loadRequest.current) return;
      setLoadState('error');
      setMessage('The package could not be loaded. Check your connection and try again.');
    }
  }, [projectId, packageRevisionHash, setPackageRevisionHash]);

  useEffect(() => { void load(); return () => { loadRequest.current += 1; }; }, [load]);

  const dirtyPaths = useMemo(() => {
    if (!snapshot) return [];
    return snapshot.files.flatMap((file) => {
      const draft = draftTexts[file.path];
      if (draft === undefined) return [];
      return draft === decodeText(file) ? [] : [file.path];
    });
  }, [draftTexts, snapshot]);

  const save = useCallback(async () => {
    if (!snapshot || dirtyPaths.length === 0) return;
    const requestedLoad = loadRequest.current;
    setSaving(true);
    setMessage('Validating and saving the complete package…');
    try {
      const dirtySet = new Set(dirtyPaths);
      const files = await Promise.all(snapshot.files.map((file) => (
        dirtySet.has(file.path) ? encodeText(file.path, draftTexts[file.path]) : file
      )));
      const previousHash = snapshot.revision.revision_hash;
      const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/package`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ expectedHeadRevisionHash: previousHash, files }),
      });
      if (requestedLoad !== loadRequest.current) return;
      if (!response.ok) {
        setMessage(response.status === 409
          ? 'A newer version has been saved. Copy your unsaved edits before reloading the saved version, then apply them again.'
          : await responseMessage(response));
        return;
      }
      const body = await response.json() as { revision: PackageRevisionSummary };
      if (requestedLoad !== loadRequest.current) return;
      setSnapshot({ revision: body.revision, files });
      setPackageRevisionHash(body.revision.revision_hash);
      setMessage(`Saved revision ${body.revision.revision}.`);
      setDiff(null);
      try {
        const diffResponse = await fetch(
          `/api/projects/${encodeURIComponent(projectId)}/package/diff?from=${previousHash}&to=${body.revision.revision_hash}`,
        );
        if (requestedLoad !== loadRequest.current) return;
        if (diffResponse.ok) setDiff(await diffResponse.json() as PackageStructuralDiff);
        else setMessage(`Saved revision ${body.revision.revision}. The change summary is currently unavailable.`);
      } catch {
        setMessage(`Saved revision ${body.revision.revision}. The change summary is currently unavailable.`);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Your changes could not be saved. Your draft is still available here.');
    } finally {
      setSaving(false);
    }
  }, [dirtyPaths, draftTexts, projectId, snapshot, setPackageRevisionHash]);

  const exportHistory = useCallback(async () => {
    try {
    const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/package/export`);
    if (!response.ok) {
      setMessage(await responseMessage(response));
      return;
    }
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${projectId}-project-package-history.zip`;
    anchor.click();
    URL.revokeObjectURL(url);
    setMessage('Exported the complete verified revision history.');
    } catch {
      setMessage('The history could not be exported. Check your connection and try again.');
    }
  }, [projectId]);

  const importHistory = useCallback(async (file: File) => {
    setSaving(true);
    setMessage('Verifying and importing package history…');
    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/package/import`, {
        method: 'POST',
        headers: { 'content-type': 'application/zip' },
        body: file,
      });
      if (!response.ok) {
        setMessage(await responseMessage(response));
        return;
      }
      await load(true);
    } catch {
      setMessage('The history could not be imported. Check your connection and try again.');
    } finally {
      setSaving(false);
      if (importInput.current) importInput.current.value = '';
    }
  }, [load, projectId]);

  const selectedText = selectedPath ? draftTexts[selectedPath] : undefined;
  const totalBytes = snapshot?.files.reduce((sum, file) => sum + file.size, 0) ?? 0;
  const ready = loadState === 'ready' && snapshot !== null;

  return (
    <StudioPage>
      <StudioPageHeader
        eyebrow="Authority / Project"
        title="Project Package"
        description="Review project files, edit a draft, and save a validated version with a traceable history."
        badge={ready ? `Revision ${snapshot.revision.revision}` : loadState === 'error' ? 'Unavailable' : loadState}
        tone={loadState === 'ready' ? 'success' : loadState === 'error' ? 'warning' : 'info'}
        compact
        actions={(
          <>
            <StudioButton onClick={() => void load(true)} disabled={saving || loadState === 'loading'}>Load latest saved version</StudioButton>
            <StudioButton onClick={() => void exportHistory()} disabled={!ready || saving}>Export history</StudioButton>
            <StudioButton variant="accent" onClick={() => void save()} disabled={!ready || dirtyPaths.length === 0 || saving}>
              {saving ? 'Working…' : `Save ${dirtyPaths.length || ''} change${dirtyPaths.length === 1 ? '' : 's'}`}
            </StudioButton>
          </>
        )}
      />

      <StudioMetricBar>
        <StudioMetric label="Project" value={projectName} meta={projectId} />
        <StudioMetric label="Revision" value={ready ? snapshot.revision.revision : '—'} meta={ready ? `Version ${shortHash(snapshot.revision.revision_hash)}` : 'Not loaded'} />
        <StudioMetric label="Package files" value={ready ? snapshot.files.length : '—'} meta={ready ? `${(totalBytes / 1024).toFixed(1)} KiB total` : 'Not loaded'} />
        <StudioMetric label="Unsaved changes" value={ready ? dirtyPaths.length : '—'} meta={ready ? dirtyPaths.length ? 'edited text files' : 'Matches saved version' : 'Not checked'} tone={ready ? dirtyPaths.length ? 'warning' : 'success' : 'default'} />
      </StudioMetricBar>

      {ready && <ExternalHandoffPanel snapshot={snapshot} />}

      {loadState === 'missing' ? (
        <StudioEmptyState
          title="No package history"
          description={(
            <span>
              Import a repository ZIP exported by Studio to establish the first verified history.
              <input
                ref={importInput}
                type="file"
                accept=".zip,application/zip"
                style={{ display: 'block', margin: '18px auto 0' }}
                disabled={saving}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void importHistory(file);
                }}
              />
            </span>
          )}
        />
      ) : loadState === 'ready' && snapshot ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 0.36fr) minmax(0, 1fr)', gap: 'var(--gap)', minHeight: 520 }}>
          <StudioPanel
            title="Complete snapshot"
            description="Select a UTF-8 text file. Binary files remain part of every revision but cannot be edited here."
            compactHeader
            bare
          >
            <div style={{ overflow: 'auto', maxHeight: 600 }}>
              {snapshot.files.map((file) => {
                const editable = Object.hasOwn(draftTexts, file.path);
                const changed = dirtyPaths.includes(file.path);
                return (
                  <button
                    key={file.path}
                    type="button"
                    title={file.path}
                    disabled={!editable}
                    onClick={() => setSelectedPath(file.path)}
                    style={{
                      width: '100%', padding: '10px 14px', border: 0,
                      borderBottom: '1px solid var(--line-2)', textAlign: 'left',
                      background: selectedPath === file.path ? 'var(--accent-soft)' : 'transparent',
                      color: editable ? 'var(--ink)' : 'var(--ink-4)', cursor: editable ? 'pointer' : 'default',
                    }}
                  >
                    <span style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {changed ? '● ' : ''}{file.path}
                    </span>
                    <span style={{ display: 'block', marginTop: 'var(--space-1)', fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>
                      {file.size.toLocaleString()} bytes · {shortHash(file.sha256)}
                    </span>
                  </button>
                );
              })}
            </div>
          </StudioPanel>

          <StudioPanel
            title={selectedPath || 'Package file'}
            description={selectedPath ? 'Edit your draft below. Saving validates the complete package and creates a new version; previous versions are retained.' : 'Select an editable UTF-8 file.'}
            compactHeader
            style={{ minWidth: 0 }}
          >
            {selectedPath && selectedText !== undefined ? (
              <StudioTextarea
                aria-label={`Edit ${selectedPath}`}
                spellCheck={false}
                value={selectedText}
                onChange={(event) => setDraftTexts((current) => ({ ...current, [selectedPath]: event.target.value }))}
                style={{ minHeight: 440, resize: 'vertical', fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.55 }}
              />
            ) : (
              <StudioEmptyState title="No editable file selected" description="Choose a YAML, JSON, Markdown, SQL, Python, or text file from the snapshot." />
            )}
            {diff && (
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', padding: '10px 12px', borderRadius: 'var(--radius)', background: 'var(--bg-2)', fontSize: 12, color: 'var(--ink-3)' }}>
                <strong style={{ color: 'var(--ink)' }}>Last saved version</strong>
                <span>{diff.added_files.length} added</span>
                <span>{diff.removed_files.length} removed</span>
                <span>{diff.changed_files.length} changed</span>
              </div>
            )}
          </StudioPanel>
        </div>
      ) : (
        <div role={loadState === 'error' ? 'alert' : 'status'}>
          <StudioEmptyState
            title={loadState === 'loading' ? 'Loading Project Package' : errorStatus === 401 ? 'Sign in required' : errorStatus === 403 ? 'Project access required' : 'Project Package unavailable'}
            description={(
              <div style={{ display: 'grid', gap: 'var(--gap)' }}>
                <span>{message}</span>
                {errorStatus === 401 && <a href="/login?callbackUrl=%2Fpackage">Sign in</a>}
                {loadState === 'error' && errorStatus !== 401 && <StudioButton onClick={() => void load()}>Try again</StudioButton>}
              </div>
            )}
          />
        </div>
      )}

      {ready && <AiPolicyReviewPanel key={`ai:${projectId}:${snapshot.revision.revision_hash}`} projectId={projectId} snapshot={snapshot} dirty={dirtyPaths.length > 0} />}
      {ready && <ProjectReleasePanel key={`${projectId}:${snapshot.revision.revision_hash}`} projectId={projectId} revisionHash={snapshot.revision.revision_hash} dirty={dirtyPaths.length > 0} />}
      {(loadState === 'ready' || loadState === 'missing') && <div role="status" aria-live="polite" style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>{message}</div>}
    </StudioPage>
  );
}
