'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { CommandPalette, type SerializablePaletteItem, type PaletteItem } from './command-palette';
import { Wizard } from './wizard';
import { useProjectStore, type WizardDraftKind } from '@/lib/store/project-store';

export interface GlobalOverlaysProps {
  paletteItems?: SerializablePaletteItem[];
}

export function GlobalOverlays({ paletteItems = [] }: GlobalOverlaysProps) {
  const [wizardOpen, setWizardOpen] = useState(false);
  const router = useRouter();
  const setPendingWizardDraft = useProjectStore((s) => s.setPendingWizardDraft);

  useEffect(() => {
    const handler = () => setWizardOpen(true);
    window.addEventListener('studio:open-wizard', handler);
    return () => window.removeEventListener('studio:open-wizard', handler);
  }, []);

  const handleSaveDraft = useCallback(
    (kind: WizardDraftKind, draft: { name: string; ref: string; domain: string; type: string; grain: string; description: string; sql?: string }) => {
      setPendingWizardDraft({
        kind,
        name: draft.name,
        ref: draft.ref,
        domain: draft.domain,
        type: draft.type,
        grain: draft.grain,
        description: draft.description,
        sql: draft.sql,
        createdAt: new Date().toISOString(),
      });
      setWizardOpen(false);
      router.push(kind === 'bracket' ? '/compose' : '/catalog');
    },
    [setPendingWizardDraft, router],
  );

  // Reconstruct full PaletteItem[] from serializable items by adding onSelect handlers
  const fullItems: PaletteItem[] = paletteItems.map((item) => ({
    ...item,
    onSelect: item.sub ? () => router.push(item.sub!) : undefined,
  }));

  return (
    <>
      <CommandPalette items={fullItems} onNavigate={(path) => { window.location.href = path; }} />
      <Wizard open={wizardOpen} onClose={() => setWizardOpen(false)} onSave={handleSaveDraft} />
    </>
  );
}
