/**
 * CSS Custom Properties Generator — Converts ThemeConfig to deployable CSS.
 */

import type { ThemeConfig } from '@/lib/store/project-store';

/** Parse a hex color to RGB components. */
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return null;
  return {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16),
  };
}

/** Generate an rgba string at a given opacity. */
function withOpacity(hex: string, opacity: number): string {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${opacity})`;
}

export function generateCssCustomProperties(theme: ThemeConfig): string {
  const escapedFont = theme.fontFamily.includes(' ')
    ? `"${theme.fontFamily}", sans-serif`
    : `${theme.fontFamily}, sans-serif`;

  const lines = [
    '/* ActionReady Theme — Auto-generated CSS Custom Properties */',
    '/* Do not edit manually. Re-export from Brand Lab to update. */',
    '',
    ':root {',
    '  /* Brand Colors */',
    `  --ar-primary: ${theme.primary};`,
    `  --ar-primary-10: ${withOpacity(theme.primary, 0.1)};`,
    `  --ar-primary-20: ${withOpacity(theme.primary, 0.2)};`,
    `  --ar-secondary: ${theme.secondary};`,
    `  --ar-secondary-10: ${withOpacity(theme.secondary, 0.1)};`,
    `  --ar-secondary-20: ${withOpacity(theme.secondary, 0.2)};`,
    `  --ar-accent: ${theme.accent};`,
    `  --ar-accent-10: ${withOpacity(theme.accent, 0.1)};`,
    `  --ar-accent-20: ${withOpacity(theme.accent, 0.2)};`,
    '',
    '  /* Surfaces */',
    `  --ar-background: ${theme.background};`,
    `  --ar-surface: ${theme.surface};`,
    `  --ar-text: ${theme.text};`,
    '',
    '  /* Typography */',
    `  --ar-font-family: ${escapedFont};`,
    '',
    '  /* Layout */',
    `  --ar-border-radius: ${theme.borderRadius}px;`,
    `  --ar-border-radius-sm: ${Math.max(0, theme.borderRadius - 4)}px;`,
    `  --ar-border-radius-lg: ${theme.borderRadius + 4}px;`,
    '',
    '  /* Semantic (RAG) */',
    '  --ar-status-red: #EF4444;',
    '  --ar-status-amber: #FFB800;',
    '  --ar-status-green: #10B981;',
    '}',
    '',
  ];

  return lines.join('\n');
}
