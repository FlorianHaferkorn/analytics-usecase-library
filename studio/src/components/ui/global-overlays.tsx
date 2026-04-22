'use client';

import { useState, useEffect } from 'react';
import { CommandPalette } from './command-palette';
import { Wizard } from './wizard';

export function GlobalOverlays() {
  const [wizardOpen, setWizardOpen] = useState(false);

  useEffect(() => {
    const handler = () => setWizardOpen(true);
    window.addEventListener('studio:open-wizard', handler);
    return () => window.removeEventListener('studio:open-wizard', handler);
  }, []);

  return (
    <>
      <CommandPalette onNavigate={(path) => { window.location.href = path; }} />
      <Wizard open={wizardOpen} onClose={() => setWizardOpen(false)} />
    </>
  );
}
