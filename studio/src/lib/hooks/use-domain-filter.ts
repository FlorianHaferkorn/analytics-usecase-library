'use client';

import { useCallback } from 'react';
import { usePathname } from 'next/navigation';
import { useDomainFilterContext } from '@/components/providers/domain-filter-provider';

/** Instant domain filter — store + replaceState, no RSC navigation. */
export function useDomainFilter() {
  return useDomainFilterContext();
}

/** Shallow query update without RSC refetch (Library tabs, etc.). */
export function useShallowQueryParam(param: string) {
  const pathname = usePathname();

  const setParam = useCallback(
    (value: string | null) => {
      const params = new URLSearchParams(window.location.search);
      if (value) params.set(param, value);
      else params.delete(param);
      window.history.replaceState(
        null,
        '',
        `${pathname}${params.toString() ? `?${params.toString()}` : ''}`,
      );
      window.dispatchEvent(new PopStateEvent('popstate'));
    },
    [param, pathname],
  );

  const value =
    typeof window !== 'undefined'
      ? new URLSearchParams(window.location.search).get(param)
      : null;

  return { value, setParam };
}
