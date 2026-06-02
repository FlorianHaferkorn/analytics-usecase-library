'use client';

import { useState, useEffect, Suspense, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { CommandPalette } from './CommandPalette';
import { Settings } from './Settings';
import { Wizard } from '@/components/ui/wizard';
import { useWizardSave } from '@/hooks/use-wizard-save';
import { ChatPanel } from '@/components/ui/global-overlays';
import type { ShellPaletteItem } from '@/lib/studio/build-palette-items';

interface EntityContext {
  entityType: 'kpi' | 'bracket' | 'use_case' | 'general';
  entityId?: string;
}

export interface StudioAppShellProps {
  children: React.ReactNode;
  paletteItems?: ShellPaletteItem[];
}

export function StudioAppShell({ children, paletteItems = [] }: StudioAppShellProps) {
  const router = useRouter();
  const [commandOpen, setCommandOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [chatContext, setChatContext] = useState<EntityContext | null>(null);
  const { saveDraft, saving: wizardSaving, error: wizardSaveError, clearError: clearWizardError } = useWizardSave();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandOpen(true);
      }
      if (
        e.key === 'n' &&
        !(e.target instanceof HTMLInputElement) &&
        !(e.target instanceof HTMLTextAreaElement)
      ) {
        e.preventDefault();
        setWizardOpen(true);
      }
      if (e.key === 'Escape') {
        setCommandOpen(false);
        setSettingsOpen(false);
        setWizardOpen(false);
        setChatContext(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    const onChat = (e: Event) => {
      const detail = (e as CustomEvent<{ entityContext?: EntityContext }>).detail;
      const ctx = detail?.entityContext ?? { entityType: 'general' as const };
      setChatContext(ctx);
    };
    window.addEventListener('studio:open-chat', onChat);
    return () => window.removeEventListener('studio:open-chat', onChat);
  }, []);

  const entityCommands = useMemo(
    () =>
      paletteItems.map((item) => ({
        id: `entity-${item.kind}-${item.id}`,
        label: item.label,
        category: item.sub,
        action: () => router.push(item.href),
      })),
    [paletteItems, router],
  );

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      <Suspense fallback={<aside className="w-[248px] border-r border-border" />}>
        <Sidebar
          onNew={() => setWizardOpen(true)}
          onCommand={() => setCommandOpen(true)}
        />
      </Suspense>

      <div className="flex flex-col flex-1 min-w-0">
        <Topbar
          onSettings={() => setSettingsOpen(true)}
          onAskStudio={() =>
            setChatContext({ entityType: 'general' })
          }
        />

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
        extraCommands={entityCommands}
      />

      <Settings isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />

      <Wizard
        open={wizardOpen}
        onClose={() => {
          setWizardOpen(false);
          clearWizardError();
        }}
        saving={wizardSaving}
        saveError={wizardSaveError}
        onSave={async (kind, draft) => {
          const ok = await saveDraft(kind, draft);
          if (ok) setWizardOpen(false);
        }}
      />

      {chatContext && (
        <ChatPanel
          entityContext={chatContext}
          onClose={() => setChatContext(null)}
        />
      )}
    </div>
  );
}
