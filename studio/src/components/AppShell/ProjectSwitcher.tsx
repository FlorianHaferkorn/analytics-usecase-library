'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useProjectStore } from '@/lib/store/project-store';
import { StudioButton } from '@/components/ui/studio-page';
import { StudioInput } from '@/components/ui/studio-data';
import styles from './ProjectSwitcher.module.css';

const COOKIE_NAME = 'studio.project';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30;

function readProjectCookie(): string | null {
  const match = document.cookie.split('; ').find((row) => row.startsWith(`${COOKIE_NAME}=`));
  try { return match ? decodeURIComponent(match.split('=')[1] ?? '') : null; } catch { return null; }
}

function writeProjectCookie(projectId: string) {
  document.cookie = `${COOKIE_NAME}=${encodeURIComponent(projectId)}; path=/; max-age=${COOKIE_MAX_AGE}; SameSite=Lax`;
}

interface ProjectItem {
  id: string;
  name: string;
  strategy_anchor: string;
  updated_at: string;
}

export function ProjectSwitcher() {
  const projectId = useProjectStore((state) => state.projectId);
  const projectName = useProjectStore((state) => state.projectName);
  const setProjectId = useProjectStore((state) => state.setProjectId);
  const setProjectName = useProjectStore((state) => state.setProjectName);
  const setStrategyAnchor = useProjectStore((state) => state.setStrategyAnchor);
  const setScope = useProjectStore(state => state.setDataScope);
  const restored = useRef(false);
  const dirtyDiscovery = useRef(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const applyProject = useCallback((project: ProjectItem) => {
    if (project.id !== useProjectStore.getState().projectId && (dirtyDiscovery.current || useProjectStore.getState().isDirty)
      && !window.confirm('There are unsaved changes. Save them before switching if you need to retain them. Switch project?')) return;
    setProjectId(project.id);
    setProjectName(project.name);
    setStrategyAnchor(project.strategy_anchor);
    setScope('project');
    useProjectStore.getState().markClean();
    writeProjectCookie(project.id);
    setIsOpen(false);
  }, [setProjectId, setProjectName, setStrategyAnchor, setScope]);

  useEffect(() => {
    if (restored.current) return;
    restored.current = true;
    const savedId = readProjectCookie();
    let selection: {projectId?: string; scope?: string; hash?: string} = {};
    try { selection = JSON.parse(sessionStorage.getItem('studio.view.selection') ?? '{}'); } catch { /* invalid selection is not restored */ }
    if (!savedId) return;
    fetch('/api/project/list')
      .then((response) => response.ok ? response.json() : null)
      .then((data: { projects: ProjectItem[] } | null) => {
        const saved = data?.projects.find((project) => project.id === savedId);
        if (saved) {
          applyProject(saved);
          if (selection.projectId === saved.id) {
            setScope(selection.scope === 'project' ? 'project' : 'library');
            if (selection.hash && /^[a-f0-9]{64}$/.test(selection.hash)) useProjectStore.getState().setPackageRevisionHash(selection.hash);
          }
        }
      })
      .catch(() => null);
  }, [applyProject, projectId, setScope]);

  useEffect(() => {
    const update = (event: Event) => {
      const detail = (event as CustomEvent<{projectId: string; dirty: boolean}>).detail;
      if (detail.projectId === useProjectStore.getState().projectId) dirtyDiscovery.current = detail.dirty;
    };
    window.addEventListener('studio:unsaved-discovery', update);
    return () => window.removeEventListener('studio:unsaved-discovery', update);
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    const close = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setIsOpen(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsOpen(false);
    };
    document.addEventListener('mousedown', close);
    document.addEventListener('keydown', escape);
    return () => {
      document.removeEventListener('mousedown', close);
      document.removeEventListener('keydown', escape);
    };
  }, [isOpen]);

  const loadProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/project/list');
      if (response.ok) {
        const data = await response.json() as { projects: ProjectItem[] };
        setProjects(data.projects);
      } else throw new Error(`Project list unavailable (${response.status})`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load projects');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) void loadProjects();
  }, [isOpen, loadProjects]);

  const createProject = async () => {
    if (!newName.trim() || creating) return;
    setCreating(true);
    setError(null);
    try {
    const response = await fetch('/api/project', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName.trim() }),
    });
    if (!response.ok) throw new Error(`Project could not be created (${response.status})`);
    const { project } = await response.json() as { project: ProjectItem };
    applyProject(project);
    setNewName('');
    setShowCreate(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to create project');
    } finally { setCreating(false); }
  };

  return (
    <div ref={rootRef} className={styles.root}>
      <button
        type="button"
        className={styles.trigger}
        aria-haspopup="dialog"
        aria-label={`Switch project. Current project: ${projectName}`}
        aria-expanded={isOpen}
        onClick={() => setIsOpen((open) => !open)}
      >
        <span className={styles.projectDot} aria-hidden="true" />
        <span className={styles.projectName}>{projectName}</span>
        <span className={styles.chevron} aria-hidden="true">⌄</span>
      </button>

      {isOpen && (
        <section className={styles.popover} role="dialog" aria-label="Switch project">
          <header><div><span>Project context</span><strong>Switch project</strong></div><button type="button" onClick={() => setIsOpen(false)} aria-label="Close project switcher">×</button></header>
          <div className={styles.projectList}>
            {error && <p role="alert">{error} <StudioButton onClick={() => void loadProjects()}>Retry list</StudioButton></p>}
            {loading && projects.length === 0 && <p className={styles.loading}>Loading projects…</p>}
            {!loading && projects.length === 0 && <p className={styles.loading}>No projects available.</p>}
            {projects.map((project) => (
              <button key={project.id} type="button" className={styles.projectOption} data-active={project.id === projectId} onClick={() => applyProject(project)}>
                <span className={styles.optionDot} aria-hidden="true" />
                <span><strong>{project.name}</strong><small>{project.id === projectId ? 'Current project' : 'Switch context'}</small></span>
                {project.id === projectId && <span className={styles.activeMark} aria-hidden="true">✓</span>}
              </button>
            ))}
          </div>
          <footer>
            {showCreate ? (
              <div className={styles.createRow}>
                <StudioInput aria-label="Project name" value={newName} onChange={(event) => setNewName(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && void createProject()} placeholder="Project name" autoFocus />
                <StudioButton onClick={() => void createProject()} disabled={!newName.trim() || creating} variant="primary">{creating ? 'Creating…' : 'Create'}</StudioButton>
                <StudioButton onClick={() => { setShowCreate(false); setNewName(''); }} variant="ghost">Cancel</StudioButton>
              </div>
            ) : (
              <StudioButton onClick={() => setShowCreate(true)} variant="ghost">New project</StudioButton>
            )}
          </footer>
        </section>
      )}
    </div>
  );
}
