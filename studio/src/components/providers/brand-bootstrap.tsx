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
  useEffect(() => {
    // Loading governed defaults is not a user edit or an unsaved project draft.
    useProjectStore.setState(state => ({ theme: { ...state.theme, ...theme } }));
  }, [theme]);

  return null;
}
