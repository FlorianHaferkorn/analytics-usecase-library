'use client';

import { useEffect } from 'react';
import { useProjectStore } from '@/lib/store/project-store';
import type { AuroraBootstrapData } from '@/lib/aurora/bootstrap-data';

/**
 * Publishes the server-loaded Aurora snapshot into the project store.
 *
 * Renders nothing — it is mounted as a sibling of the shell content, not as a wrapper, so
 * it is a one-way bootstrap rather than a context. The snapshot is read from disk on the
 * server (`node:fs`), and client surfaces read it from the store, which stays the single
 * source of truth for client state.
 */
export function AuroraBootstrap({ data }: { data: AuroraBootstrapData }) {
  const setAurora = useProjectStore((state) => state.setAurora);

  useEffect(() => {
    setAurora(data);
  }, [data, setAurora]);

  return null;
}
