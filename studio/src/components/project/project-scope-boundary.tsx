'use client';
import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { useProjectStore } from '@/lib/store/project-store';
import { surfaceScope } from '@/lib/project-package/view-policy';
import { ProjectRevisionView } from './project-revision-view';
import styles from './project-scope.module.css';

export function ScopeIndicator() {
  const path = usePathname();
  const scope = useProjectStore(s => s.dataScope);
  const setScope = useProjectStore(s => s.setDataScope);
  const name = useProjectStore(s => s.projectName);
  const id = useProjectStore(s => s.projectId);
  const hash = useProjectStore(s => s.packageRevisionHash);
  const effective = surfaceScope(path, scope);
  const fixed = surfaceScope(path, 'library') === surfaceScope(path, 'project');
  useEffect(() => {
    // Entering an explicit project tool makes subsequent workflow links project-scoped.
    // Visiting Library reference tools does not erase that project intent.
    if (fixed && effective === 'project' && scope !== 'project') setScope('project');
  }, [fixed, effective, scope, setScope]);
  useEffect(() => {
    // Only selection metadata, never customer content or authorization, is persisted.
    try { sessionStorage.setItem('studio.view.selection', JSON.stringify({ projectId: id, scope, hash })); } catch { /* Storage is optional; authorization is server-side. */ }
  }, [id, scope, hash]);
  if (path === '/automation/reference') return <div className={styles.scope} aria-label="Data origin"><strong>Local reference lab · synthetic data only</strong><span>The selected customer project is not read or changed.</span></div>;
  return <div className={styles.scope} aria-label="Data origin">
    <label htmlFor="studio-data-scope">Working view </label>
    <select id="studio-data-scope" disabled={fixed} value={effective === 'project' ? 'project' : 'library'} onChange={e => setScope(e.target.value as 'library' | 'project')}><option value="library">Library examples</option><option value="project">Selected project</option></select>
    <strong>{effective === 'library' ? 'Library · reusable definitions, not project evidence' : effective === 'administration' ? 'Administration · explicit target required' : `Project · ${name}`}</strong>
    {effective === 'project' && hash && <span title={hash}>Version {hash.slice(0, 12)}</span>}
  </div>;
}

export function ProjectScopeBoundary({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const scope = useProjectStore(s => s.dataScope);
  const id = useProjectStore(s => s.projectId);
  const ownProjectSurface = /^\/(discover|discovery|package|generate|delivery|architecture|engagement|automation)(\/|$)/.test(pathname);
  if (surfaceScope(pathname, scope) === 'project' && !ownProjectSurface) return <ProjectRevisionView key={id} pathname={pathname} />;
  if (ownProjectSurface) return <>{children}</>;
  return <div key={`${id}:${scope}`}>{children}</div>;
}
