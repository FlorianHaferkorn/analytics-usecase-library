'use client';

import { useEffect, useRef } from 'react';
import { useProjectStore } from '@/lib/store/project-store';
import type { ThemeConfig } from '@/lib/store/project-store';

/** Applies governed brand_spec theme once on boot; Brand Lab overrides remain in store. */
export function BrandBootstrap({ theme }: { theme: Partial<ThemeConfig> | null }) {
  const setTheme = useProjectStore((s) => s.setTheme);
  const applied = useRef(false);

  useEffect(() => {
    if (!theme || applied.current) return;
    setTheme(theme);
    applied.current = true;
  }, [theme, setTheme]);

  return null;
}
