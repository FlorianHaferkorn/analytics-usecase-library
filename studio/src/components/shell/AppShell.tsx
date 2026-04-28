'use client';

import { useState, useEffect, Suspense } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { CommandPalette } from './CommandPalette';
import { Settings } from './Settings';
import { Wizard } from './Wizard';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [commandOpen, setCommandOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // ⌘K / Ctrl+K: Command Palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandOpen(true);
      }

      // N: Wizard (not if typing in input/textarea)
      if (
        e.key === 'n' &&
        !(e.target instanceof HTMLInputElement) &&
        !(e.target instanceof HTMLTextAreaElement)
      ) {
        e.preventDefault();
        setWizardOpen(true);
      }

      // Esc: Close any open modal
      if (e.key === 'Escape') {
        setCommandOpen(false);
        setSettingsOpen(false);
        setWizardOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      <Suspense fallback={<aside className="w-[248px] border-r border-border" />}>
        <Sidebar
          onNew={() => setWizardOpen(true)}
          onCommand={() => setCommandOpen(true)}
        />
      </Suspense>

      <div className="flex flex-col flex-1 min-w-0">
        <Topbar onSettings={() => setSettingsOpen(true)} />

        <main className="flex-1 overflow-auto bg-background p-6">
          <div className="w-full max-w-7xl mx-auto">{children}</div>
        </main>
      </div>

      <CommandPalette
        isOpen={commandOpen}
        onClose={() => setCommandOpen(false)}
        onNew={() => {
          setCommandOpen(false);
          setWizardOpen(true);
        }}
      />

      <Settings isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />

      <Wizard isOpen={wizardOpen} onClose={() => setWizardOpen(false)} />
    </div>
  );
}
