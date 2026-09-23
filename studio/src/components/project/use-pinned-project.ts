'use client';

import { useEffect, useState } from 'react';
import { useProjectStore } from '@/lib/store/project-store';
import type { ProjectProjection } from '@/lib/project-package/projection';

/** Display only; repository validation and business readiness remain Python-owned. */
export function usePinnedProject() {
  const projectId = useProjectStore(s => s.projectId);
  const projectName = useProjectStore(s => s.projectName);
  const revision = useProjectStore(s => s.packageRevisionHash);
  const [result, setResult] = useState<{key: string; value?: ProjectProjection; error?: string} | null>(null);
  const [attempt, setAttempt] = useState(0);
  const key = `${projectId}:${revision ?? 'HEAD'}`;
  useEffect(() => {
    const controller = new AbortController();
    void fetch(`/api/projects/${encodeURIComponent(projectId)}/view${revision ? `?revision=${revision}` : ''}`, {cache:'no-store', signal:controller.signal})
      .then(async response => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error?.message ?? `Project version unavailable (${response.status})`);
        const value = data as ProjectProjection;
        if (value.projectId !== projectId || (revision && value.revision.revision_hash !== revision)) throw new Error('Project version mismatch');
        const selected = useProjectStore.getState();
        if (controller.signal.aborted || selected.projectId !== projectId || selected.packageRevisionHash !== revision) return;
        setResult({key:`${projectId}:${value.revision.revision_hash}`,value});
        useProjectStore.getState().setPackageRevisionHash(value.revision.revision_hash);
      }).catch(error => { if (!controller.signal.aborted) setResult({key,error:error instanceof Error ? error.message : 'Unable to load project'}); });
    return () => controller.abort();
  }, [projectId, revision, key, attempt]);
  return {projectId,projectName,revision,value:result?.key === key ? result.value : undefined,error:result?.key === key ? result.error : undefined,
    retry:() => setAttempt(n => n + 1), latest:() => {useProjectStore.getState().setPackageRevisionHash(null);setAttempt(n => n + 1);}};
}
