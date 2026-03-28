/**
 * JSON Theme Config Generator — Converts ThemeConfig to a portable JSON format.
 *
 * Compatible with Evidence.dev, custom dashboard apps, and Power BI theme imports.
 */

import type { ThemeConfig } from '@/lib/store/project-store';

export interface ExportedThemeJson {
  name: string;
  version: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    status: { red: string; amber: string; green: string };
  };
  typography: {
    fontFamily: string;
  };
  layout: {
    borderRadius: number;
    borderRadiusSm: number;
    borderRadiusLg: number;
  };
}

export function generateJsonConfig(theme: ThemeConfig): string {
  const exported: ExportedThemeJson = {
    name: 'ActionReady Theme',
    version: '1.0.0',
    colors: {
      primary: theme.primary,
      secondary: theme.secondary,
      accent: theme.accent,
      background: theme.background,
      surface: theme.surface,
      text: theme.text,
      status: { red: '#EF4444', amber: '#FFB800', green: '#10B981' },
    },
    typography: {
      fontFamily: theme.fontFamily,
    },
    layout: {
      borderRadius: theme.borderRadius,
      borderRadiusSm: Math.max(0, theme.borderRadius - 4),
      borderRadiusLg: theme.borderRadius + 4,
    },
  };

  return JSON.stringify(exported, null, 2) + '\n';
}
