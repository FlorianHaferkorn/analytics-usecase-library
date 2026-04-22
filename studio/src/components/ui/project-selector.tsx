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

export function ProjectSelector() {
  const projectId = useProjectStore((s) => s.projectId);
  const projectName = useProjectStore((s) => s.projectName);
  const setProjectId = useProjectStore((s) => s.setProjectId);
  const setProjectName = useProjectStore((s) => s.setProjectName);
  const setStrategyAnchor = useProjectStore((s) => s.setStrategyAnchor);

  const [isOpen, setIsOpen] = useState(false);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');

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
        <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--mint)' }} />
        {projectName}
        <span style={{ color: 'var(--ink-4)', fontSize: '0.6875rem' }}>▾</span>
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
                {p.id === projectId && <span style={{ color: 'var(--mint)', marginLeft: '8px', fontSize: '0.6875rem' }}>active</span>}
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
