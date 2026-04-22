'use client';

/**
 * ProjectSwitcher — tenant project selection widget for the Studio header.
 *
 * Persists the active project in the cookie `studio.project` (30-day expiry)
 * so the selection survives page refreshes without a round-trip to the server.
 *
 * All tenant-scoped navigation links read the active projectId from the
 * Zustand store, which is hydrated from the cookie on mount.
 */

import { useState, useEffect, useCallback } from 'react';
import { useProjectStore } from '@/lib/store/project-store';
import { StudioButton, StudioPanel } from '@/components/ui/studio-page';
import { StudioInput } from '@/components/ui/studio-data';

const COOKIE_NAME = 'studio.project';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

function readProjectCookie(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${COOKIE_NAME}=`));
  return match ? decodeURIComponent(match.split('=')[1]) : null;
}

function writeProjectCookie(projectId: string) {
  if (typeof document === 'undefined') return;
  document.cookie = `${COOKIE_NAME}=${encodeURIComponent(projectId)}; path=/; max-age=${COOKIE_MAX_AGE}; SameSite=Lax`;
}

interface ProjectItem {
  id: string;
  name: string;
  strategy_anchor: string;
  updated_at: string;
}

export function ProjectSwitcher() {
  const projectId = useProjectStore((s) => s.projectId);
  const projectName = useProjectStore((s) => s.projectName);
  const setProjectId = useProjectStore((s) => s.setProjectId);
  const setProjectName = useProjectStore((s) => s.setProjectName);
  const setStrategyAnchor = useProjectStore((s) => s.setStrategyAnchor);

  const [isOpen, setIsOpen] = useState(false);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');

  // Hydrate from cookie on first mount (handles page refresh).
  useEffect(() => {
    const savedId = readProjectCookie();
    if (savedId && savedId !== projectId) {
      // Fetch the project details so the store name is correct.
      fetch('/api/project/list')
        .then((r) => (r.ok ? r.json() : null))
        .then((data: { projects: ProjectItem[] } | null) => {
          if (!data) return;
          const saved = data.projects.find((p) => p.id === savedId);
          if (saved) {
            setProjectId(saved.id);
            setProjectName(saved.name);
            setStrategyAnchor(saved.strategy_anchor);
          }
        })
        .catch(() => null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once on mount only.

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
    writeProjectCookie(proj.id);
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
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--sp-1)',
          fontSize: '0.8125rem',
          padding: '4px var(--sp-1-5)',
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: 'var(--mint)',
            flexShrink: 0,
          }}
        />
        <span style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {projectName}
        </span>
        <span style={{ color: 'var(--slate-500)', fontSize: '0.6875rem' }}>▾</span>
      </StudioButton>

      {isOpen && (
        <StudioPanel
          style={{
            position: 'absolute',
            top: '100%',
            right: 0,
            marginTop: 4,
            width: 300,
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
            zIndex: 50,
            overflow: 'hidden',
            padding: 0,
          }}
        >
          <div
            style={{
              padding: 'var(--sp-1) var(--sp-2)',
              borderBottom: '1px solid var(--slate-800)',
            }}
          >
            <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', margin: 0 }}>
              SWITCH PROJECT
            </p>
          </div>

          <div style={{ maxHeight: 220, overflow: 'auto', padding: 'var(--sp-1)' }}>
            {projects.length === 0 && (
              <p
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--slate-500)',
                  padding: 'var(--sp-1)',
                  margin: 0,
                }}
              >
                Loading…
              </p>
            )}
            {projects.map((p) => (
              <StudioButton
                key={p.id}
                onClick={() => switchProject(p)}
                variant="ghost"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  width: '100%',
                  textAlign: 'left',
                  padding: 'var(--sp-1)',
                  gap: 'var(--sp-1)',
                  backgroundColor: p.id === projectId ? 'var(--slate-700)' : 'transparent',
                  color: 'var(--slate-100)',
                  fontSize: '0.8125rem',
                  justifyContent: 'flex-start',
                }}
              >
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    backgroundColor: p.id === projectId ? 'var(--mint)' : 'var(--slate-600)',
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontWeight: p.id === projectId ? 600 : 400, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {p.name}
                </span>
                {p.id === projectId && (
                  <span style={{ color: 'var(--mint)', fontSize: '0.6875rem', flexShrink: 0 }}>
                    active
                  </span>
                )}
              </StudioButton>
            ))}
          </div>

          <div style={{ borderTop: '1px solid var(--slate-700)', padding: 'var(--sp-1)' }}>
            {showCreate ? (
              <div style={{ display: 'flex', gap: '4px' }}>
                <StudioInput
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                  placeholder="Project name..."
                  autoFocus
                  style={{
                    flex: 1,
                    padding: '4px var(--sp-1)',
                    fontSize: '0.75rem',
                    borderRadius: 'var(--radius-sm)',
                  }}
                />
                <StudioButton
                  onClick={handleCreate}
                  tone="success"
                  variant="primary"
                  style={{ padding: '4px var(--sp-1)', fontSize: '0.75rem', borderRadius: 'var(--radius-sm)' }}
                >
                  Add
                </StudioButton>
                <StudioButton
                  onClick={() => { setShowCreate(false); setNewName(''); }}
                  variant="ghost"
                  style={{ padding: '4px', fontSize: '0.75rem', borderRadius: 'var(--radius-sm)' }}
                >
                  ✕
                </StudioButton>
              </div>
            ) : (
              <StudioButton
                onClick={() => setShowCreate(true)}
                variant="ghost"
                style={{
                  width: '100%',
                  padding: '4px',
                  fontSize: '0.75rem',
                  textAlign: 'left',
                  justifyContent: 'flex-start',
                }}
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
