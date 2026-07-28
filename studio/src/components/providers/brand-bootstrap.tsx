'use client';

import { useEffect } from 'react';
import { useProjectStore, type ThemeConfig } from '@/lib/store/project-store';

/**
 * Applies the governed brand (`core/brand/`) to the store's theme on mount.
 *
 * Renders nothing — mounted as a sibling of the shell content, so it bootstraps once
 * rather than wrapping the tree. Merges via `setTheme`, so any field the BrandSpec does
 * not define keeps its default instead of being blanked.
 */
export function BrandBootstrap({ theme }: { theme: Partial<ThemeConfig> }) {
  const setTheme = useProjectStore((state) => state.setTheme);

  useEffect(() => {
    setTheme(theme);
  }, [theme, setTheme]);

  return null;
}
