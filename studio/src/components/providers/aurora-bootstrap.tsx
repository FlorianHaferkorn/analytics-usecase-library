'use client';

import { useEffect } from 'react';
import { useProjectStore } from '@/lib/store/project-store';
import type { AuroraBootstrapData } from '@/lib/aurora/bootstrap-data';

/** Hydrates Zustand with Aurora showcase linkage (server-provided summary). */
export function AuroraBootstrap({ data }: { data: AuroraBootstrapData }) {
  const setAuroraBootstrap = useProjectStore((s) => s.setAuroraBootstrap);

  useEffect(() => {
    setAuroraBootstrap(data);
  }, [data, setAuroraBootstrap]);

  return null;
}
