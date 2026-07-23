'use client';

import { createContext, useContext } from 'react';
import {
  useForgeBootstrap,
  type UseForgeBootstrapResult,
} from '@/lib/hooks/use-forge-bootstrap';
import type { ForgeBootstrapPayload } from '@/lib/core/forge-bootstrap';

const ForgeBootstrapContext = createContext<UseForgeBootstrapResult | null>(null);

export function ForgeBootstrapProvider({
  children,
  initialPayload,
}: {
  children: React.ReactNode;
  initialPayload?: ForgeBootstrapPayload;
}) {
  const value = useForgeBootstrap(initialPayload);

  return (
    <ForgeBootstrapContext.Provider value={value}>{children}</ForgeBootstrapContext.Provider>
  );
}

export function useForgeBootstrapContext(): UseForgeBootstrapResult {
  const context = useContext(ForgeBootstrapContext);
  if (!context) {
    throw new Error('useForgeBootstrapContext must be used within ForgeBootstrapProvider');
  }
  return context;
}
