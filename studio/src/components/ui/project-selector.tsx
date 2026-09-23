'use client';

import { useState, useEffect, useCallback } from 'react';
import { useProjectStore } from '@/lib/store/project-store';
import { StudioButton, StudioPanel } from '@/components/ui/studio-page';
import { StudioInput } from '@/components/ui/studio-data';

interface ProjectItem {
  id: string;
  name: string;
  strategy_anchor: string;
  updated_at: string;
}

const PROJECT_CONTEXT_KEY = 'aluca-studio-project-context';

interface PersistedProjectContext {
  id: string;
  name: string;
  strategyAnchor: string;
  revisionHash: string | null;
  dataScope: 'library' | 'project';
}

export function ProjectSelector() {
  const projectId = useProjectStore((s) => s.projectId);
  const projectName = useProjectStore((s) => s.projectName);
  const strategyAnchor = useProjectStore((s) => s.strategyAnchor);
  const packageRevisionHash = useProjectStore((s) => s.packageRevisionHash);
  const dataScope = useProjectStore((s) => s.dataScope);
  const setProjectId = useProjectStore((s) => s.setProjectId);
  const setProjectName = useProjectStore((s) => s.setProjectName);
  const setStrategyAnchor = useProjectStore((s) => s.setStrategyAnchor);
  const setPackageRevisionHash = useProjectStore((s) => s.setPackageRevisionHash);
  const setDataScope = useProjectStore((s) => s.setDataScope);

  const [isOpen, setIsOpen] = useState(false);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [selectionHydrated, setSelectionHydrated] = useState(false);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(PROJECT_CONTEXT_KEY);
      if (saved) {
        const context = JSON.parse(saved) as Partial<PersistedProjectContext>;
        if (typeof context.id === 'string' && context.id.length > 0) {
          setProjectId(context.id);
          if (typeof context.name === 'string') setProjectName(context.name);
          if (typeof context.strategyAnchor === 'string') setStrategyAnchor(context.strategyAnchor);
          setPackageRevisionHash(typeof context.revisionHash === 'string' ? context.revisionHash : null);
          setDataScope(context.dataScope === 'library' ? 'library' : 'project');
        }
      }
    } catch {
      window.localStorage.removeItem(PROJECT_CONTEXT_KEY);
    } finally {
      setSelectionHydrated(true);
    }
  }, [setDataScope, setPackageRevisionHash, setProjectId, setProjectName, setStrategyAnchor]);

  useEffect(() => {
    if (!selectionHydrated) return;
    const context: PersistedProjectContext = {
      id: projectId,
      name: projectName,
      strategyAnchor,
      revisionHash: packageRevisionHash,
      dataScope,
    };
    window.localStorage.setItem(PROJECT_CONTEXT_KEY, JSON.stringify(context));
  }, [dataScope, packageRevisionHash, projectId, projectName, selectionHydrated, strategyAnchor]);

  const loadProjects = useCallback(async () => {
    const res = await fetch('/api/project/list');
    if (res.ok) {
      const data = await res.json();
      setProjects(data.projects);
    }
  }, []);

  useEffect(() => {
    if (isOpen) loadProjects();
  }, [isOpen, loadProjects]);

  const switchProject = (proj: ProjectItem) => {
    const context: PersistedProjectContext = {
      id: proj.id,
      name: proj.name,
      strategyAnchor: proj.strategy_anchor,
      revisionHash: null,
      dataScope: 'project',
    };
    window.localStorage.setItem(PROJECT_CONTEXT_KEY, JSON.stringify(context));
    setProjectId(proj.id);
    setProjectName(proj.name);
    setStrategyAnchor(proj.strategy_anchor);
    setIsOpen(false);
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    const res = await fetch('/api/project', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName.trim() }),
    });
    if (res.ok) {
      const { project } = await res.json();
      switchProject(project);
      setNewName('');
      setShowCreate(false);
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <StudioButton
        onClick={() => setIsOpen(!isOpen)}
        variant="secondary"
        tone="info"
        style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8125rem', padding: '4px 12px' }}
      >
        <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--accent)' }} />
        {projectName}
        <span style={{ color: 'var(--ink-4)', fontSize: 'var(--text-xs)' }}>▾</span>
      </StudioButton>

      {isOpen && (
        <StudioPanel style={{
          position: 'absolute', top: '100%', right: 0, marginTop: 4,
          width: 280,
          boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
          zIndex: 50,
          overflow: 'hidden',
          padding: 0,
        }}>
          <div style={{ padding: '8px', maxHeight: 200, overflow: 'auto' }}>
            {projects.map((p) => (
              <StudioButton
                key={p.id}
                onClick={() => switchProject(p)}
                variant="ghost"
                style={{
                  display: 'block', width: '100%', textAlign: 'left',
                  padding: '8px',
                  backgroundColor: p.id === projectId ? 'var(--bg-2)' : 'transparent',
                  color: 'var(--ink)', fontSize: '0.8125rem',
                  justifyContent: 'flex-start',
                }}
              >
                <span style={{ fontWeight: p.id === projectId ? 600 : 400 }}>{p.name}</span>
                {p.id === projectId && <span style={{ color: 'var(--accent)', marginLeft: '8px', fontSize: 'var(--text-xs)' }}>active</span>}
              </StudioButton>
            ))}
          </div>

          <div style={{ borderTop: '1px solid var(--line)', padding: '8px' }}>
            {showCreate ? (
              <div style={{ display: 'flex', gap: '4px' }}>
                <StudioInput
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                  placeholder="Project name..."
                  autoFocus
                  style={{ flex: 1, padding: '4px 8px', fontSize: '0.75rem', borderRadius: 'var(--radius-sm)' }}
                />
                <StudioButton
                  onClick={handleCreate}
                  tone="success"
                  variant="primary"
                  style={{ padding: '4px 8px', fontSize: '0.75rem', borderRadius: 'var(--radius-sm)' }}
                >
                  Add
                </StudioButton>
              </div>
            ) : (
              <StudioButton
                onClick={() => setShowCreate(true)}
                variant="ghost"
                style={{ width: '100%', padding: '4px', fontSize: '0.75rem', textAlign: 'left', justifyContent: 'flex-start' }}
              >
                + New Project
              </StudioButton>
            )}
          </div>
        </StudioPanel>
      )}
    </div>
  );
}
