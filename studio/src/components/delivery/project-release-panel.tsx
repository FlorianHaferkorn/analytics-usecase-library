'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { StudioButton, StudioPanel } from '@/components/ui/studio-page';
import { StudioTextarea } from '@/components/ui/studio-data';
import styles from './project-release-panel.module.css';

export function ProjectReleasePanel({ projectId, revisionHash, dirty }: { projectId: string; revisionHash: string; dirty: boolean }) {
  const [rationale, setRationale] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('No release is implied by saving a revision.');
  const identity = `${projectId}:${revisionHash}`;
  const currentIdentity = useRef(identity);
  useEffect(() => {
    currentIdentity.current = identity;
    return () => { currentIdentity.current = ''; };
  }, [identity]);

  async function release(attest: boolean) {
    const requestedIdentity = identity;
    setBusy(true);
    try {
      const endpoint = `/api/projects/${encodeURIComponent(projectId)}/package/release`;
      const response = await fetch(attest ? endpoint : `${endpoint}?revision=${revisionHash}`, attest ? {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ revisionHash, rationale, confirmInputBundleRelease: confirmed }),
      } : { cache: 'no-store' });
      if (currentIdentity.current !== requestedIdentity) return;
      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.error?.message || 'Release unavailable');
      }
      const blob = await response.blob();
      if (currentIdentity.current !== requestedIdentity) return;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${projectId}-approved-input-${revisionHash.slice(0, 12)}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      setMessage('Downloaded the approved input bundle with immutable revision, compiler input and release record hashes. Not a deployment package.');
    } catch (error) {
      if (currentIdentity.current === requestedIdentity) setMessage(error instanceof Error ? error.message : 'Release failed');
    } finally { if (currentIdentity.current === requestedIdentity) setBusy(false); }
  }

  return <StudioPanel title="Release approved project inputs" description="The bundle includes the exact saved files, validated compiler input and a named release attestation. No Fabric deployment artifacts, tenant approval or customer acceptance are implied." compactHeader>
    <div className={styles.content}>
    <p className={styles.copy}>Version {revisionHash.slice(0, 12)}. The package and its decisions must already be approved; a stale revision is blocked. Only a project administrator may attest a release.</p>
    <StudioTextarea aria-label="Input release rationale" value={rationale} maxLength={2000} placeholder="Explain why this exact version may be released (at least 20 characters)." onChange={(event) => setRationale(event.target.value)} />
    <label className={styles.confirmation}><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} /> I explicitly attest this saved input bundle for release, not target deployment.</label>
    <div className={styles.actions}>
      <StudioButton disabled={dirty || busy || !confirmed || rationale.trim().length < 20} onClick={() => void release(true)}>Attest and download inputs</StudioButton>
      <StudioButton disabled={dirty || busy} onClick={() => void release(false)}>Download existing release</StudioButton>
    </div>
    <p className={styles.copy} role="status">{dirty ? 'Save and review your changes before releasing.' : message}</p>
    <Link href="/architecture">Next: inspect Architecture and generate supported build outputs</Link>
    </div>
  </StudioPanel>;
}
