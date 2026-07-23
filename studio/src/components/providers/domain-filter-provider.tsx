'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useTransition,
  type ReactNode,
} from 'react';
import { usePathname } from 'next/navigation';
import { useProjectStore } from '@/lib/store/project-store';

function readDomainFromUrl(): string | null {
  if (typeof window === 'undefined') return null;
  return new URLSearchParams(window.location.search).get('domain');
}

function urlWithQuery(pathname: string, params: URLSearchParams): string {
  const qs = params.toString();
  return `${pathname}${qs ? `?${qs}` : ''}`;
}

interface DomainFilterContextValue {
  domainFilter: string | null;
  isPending: boolean;
  setDomainFilter: (name: string | null) => void;
  toggleDomainFilter: (name: string) => void;
  clearDomainFilter: () => void;
}

const DomainFilterContext = createContext<DomainFilterContextValue | null>(null);

/** Single popstate listener + non-blocking domain updates for the whole shell. */
export function DomainFilterProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const domainFilter = useProjectStore((s) => s.domainFilter);
  const setDomainFilterStore = useProjectStore((s) => s.setDomainFilter);
  const [isPending, startTransition] = useTransition();

  useLayoutEffect(() => {
    const fromUrl = readDomainFromUrl();
    if (fromUrl) setDomainFilterStore(fromUrl);
  }, [pathname, setDomainFilterStore]);

  useEffect(() => {
    const onPop = () => {
      startTransition(() => {
        setDomainFilterStore(readDomainFromUrl());
      });
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, [setDomainFilterStore]);

  const setDomainFilter = useCallback(
    (name: string | null) => {
      setDomainFilterStore(name);
      const params = new URLSearchParams(window.location.search);
      if (name) params.set('domain', name);
      else params.delete('domain');
      window.history.replaceState(null, '', urlWithQuery(pathname, params));
    },
    [pathname, setDomainFilterStore],
  );

  const toggleDomainFilter = useCallback(
    (name: string) => {
      setDomainFilter(domainFilter === name ? null : name);
    },
    [domainFilter, setDomainFilter],
  );

  const clearDomainFilter = useCallback(() => {
    setDomainFilter(null);
  }, [setDomainFilter]);

  const value = useMemo(
    () => ({
      domainFilter,
      isPending,
      setDomainFilter,
      toggleDomainFilter,
      clearDomainFilter,
    }),
    [domainFilter, isPending, setDomainFilter, toggleDomainFilter, clearDomainFilter],
  );

  return (
    <DomainFilterContext.Provider value={value}>{children}</DomainFilterContext.Provider>
  );
}

export function useDomainFilterContext(): DomainFilterContextValue {
  const ctx = useContext(DomainFilterContext);
  if (!ctx) {
    throw new Error('useDomainFilterContext must be used within DomainFilterProvider');
  }
  return ctx;
}
