'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { ForgeBootstrapPayload } from '@/lib/core/forge-bootstrap';

const STORAGE_KEY = 'aluca-forge-bootstrap-v1';
const CLIENT_TTL_MS = 60_000;

interface StoredBootstrap {
  fetchedAt: number;
  payload: ForgeBootstrapPayload;
}

let inflight: Promise<ForgeBootstrapPayload> | null = null;

function readSessionCache(): ForgeBootstrapPayload | null {
  if (typeof window === 'undefined') return null;

  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw) as StoredBootstrap;
    if (Date.now() - parsed.fetchedAt > CLIENT_TTL_MS) {
      return null;
    }

    return parsed.payload;
  } catch {
    return null;
  }
}

function writeSessionCache(payload: ForgeBootstrapPayload): void {
  if (typeof window === 'undefined') return;

  try {
    const stored: StoredBootstrap = { fetchedAt: Date.now(), payload };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
  } catch {
    // sessionStorage may be unavailable (private mode quota)
  }
}

async function fetchForgeBootstrap(): Promise<ForgeBootstrapPayload> {
  if (inflight) return inflight;

  inflight = fetch('/api/core/forge-bootstrap', { credentials: 'include' })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`Forge bootstrap failed (${response.status})`);
      }
      return response.json() as Promise<ForgeBootstrapPayload>;
    })
    .finally(() => {
      inflight = null;
    });

  return inflight;
}

export interface UseForgeBootstrapResult {
  data: ForgeBootstrapPayload | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useForgeBootstrap(initialPayload?: ForgeBootstrapPayload): UseForgeBootstrapResult {
  const hydratedFromServer = useRef(Boolean(initialPayload));
  const [data, setData] = useState<ForgeBootstrapPayload | null>(
    () => initialPayload ?? readSessionCache(),
  );
  const [loading, setLoading] = useState(
    () => !initialPayload && readSessionCache() === null,
  );
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    setLoading(true);

    try {
      const payload = await fetchForgeBootstrap();
      writeSessionCache(payload);
      setData(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load forge data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialPayload) {
      writeSessionCache(initialPayload);
      setData(initialPayload);
      setLoading(false);
      setError(null);
      hydratedFromServer.current = true;
      return;
    }

    if (hydratedFromServer.current || readSessionCache()) {
      setLoading(false);
      return;
    }

    void refresh();
  }, [initialPayload, refresh]);

  return { data, loading, error, refresh };
}
