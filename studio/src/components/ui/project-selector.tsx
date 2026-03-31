'use client';

import { useState, useEffect, useCallback } from 'react';
import { useProjectStore } from '@/lib/store/project-store';

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
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex', alignItems: 'center', gap: 'var(--sp-1)',
          padding: '4px var(--sp-1-5)',
          backgroundColor: 'var(--slate-800)',
          border: '1px solid var(--slate-600)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--slate-100)',
          fontSize: '0.8125rem',
          cursor: 'pointer',
        }}
      >
        <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--mint)' }} />
        {projectName}
        <span style={{ color: 'var(--slate-500)', fontSize: '0.6875rem' }}>▾</span>
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute', top: '100%', right: 0, marginTop: 4,
          width: 280,
          backgroundColor: 'var(--slate-800)',
          border: '1px solid var(--slate-600)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
          zIndex: 50,
          overflow: 'hidden',
        }}>
          <div style={{ padding: 'var(--sp-1)', maxHeight: 200, overflow: 'auto' }}>
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => switchProject(p)}
                style={{
                  display: 'block', width: '100%', textAlign: 'left',
                  padding: 'var(--sp-1)',
                  backgroundColor: p.id === projectId ? 'var(--slate-700)' : 'transparent',
                  border: 'none', borderRadius: 'var(--radius-sm)',
                  color: 'var(--slate-100)', fontSize: '0.8125rem',
                  cursor: 'pointer',
                }}
              >
                <span style={{ fontWeight: p.id === projectId ? 600 : 400 }}>{p.name}</span>
                {p.id === projectId && <span style={{ color: 'var(--mint)', marginLeft: 'var(--sp-1)', fontSize: '0.6875rem' }}>active</span>}
              </button>
            ))}
          </div>

          <div style={{ borderTop: '1px solid var(--slate-700)', padding: 'var(--sp-1)' }}>
            {showCreate ? (
              <div style={{ display: 'flex', gap: '4px' }}>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                  placeholder="Project name..."
                  autoFocus
                  style={{
                    flex: 1, padding: '4px var(--sp-1)',
                    backgroundColor: 'var(--slate-900)',
                    border: '1px solid var(--slate-600)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--slate-100)', fontSize: '0.75rem',
                  }}
                />
                <button
                  onClick={handleCreate}
                  style={{
                    padding: '4px var(--sp-1)',
                    backgroundColor: 'var(--mint)', border: 'none',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--slate-950)', fontSize: '0.75rem', fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Add
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowCreate(true)}
                style={{
                  width: '100%', padding: '4px',
                  backgroundColor: 'transparent', border: 'none',
                  color: 'var(--mint)', fontSize: '0.75rem',
                  cursor: 'pointer', textAlign: 'left',
                }}
              >
                + New Project
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
