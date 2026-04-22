'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { CommandPalette, type SerializablePaletteItem, type PaletteItem } from './command-palette';
import { Wizard } from './wizard';

export interface GlobalOverlaysProps {
  paletteItems?: SerializablePaletteItem[];
}

export function GlobalOverlays({ paletteItems = [] }: GlobalOverlaysProps) {
  const [wizardOpen, setWizardOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const handler = () => setWizardOpen(true);
    window.addEventListener('studio:open-wizard', handler);
    return () => window.removeEventListener('studio:open-wizard', handler);
  }, []);

  // Reconstruct full PaletteItem[] from serializable items by adding onSelect handlers
  const fullItems: PaletteItem[] = paletteItems.map((item) => ({
    ...item,
    onSelect: item.sub ? () => router.push(item.sub!) : undefined,
  }));

  return (
    <>
      <CommandPalette items={fullItems} onNavigate={(path) => { window.location.href = path; }} />
      <Wizard open={wizardOpen} onClose={() => setWizardOpen(false)} />
    </>
  );
}
