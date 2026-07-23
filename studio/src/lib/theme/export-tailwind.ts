/**
 * Tailwind Config Generator — Converts ThemeConfig to a Tailwind CSS config snippet.
 */

import type { ThemeConfig } from '@/lib/store/project-store';

/** Parse hex to RGB string for Tailwind opacity support. */
function hexToRgbString(hex: string): string {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return '0 0 0';
  return `${parseInt(result[1], 16)} ${parseInt(result[2], 16)} ${parseInt(result[3], 16)}`;
}

export function generateTailwindConfig(theme: ThemeConfig): string {
  const escapedFont = theme.fontFamily.includes(' ')
    ? `"${theme.fontFamily}"`
    : theme.fontFamily;

  const lines = [
    '// ALUCA Theme — Auto-generated Tailwind config',
    '// Do not edit manually. Re-export from Brand Lab to update.',
    '',
    'import type { Config } from "tailwindcss";',
    '',
    'const config: Partial<Config> = {',
    '  theme: {',
    '    extend: {',
    '      colors: {',
    '        ar: {',
    `          primary: "rgb(${hexToRgbString(theme.primary)} / <alpha-value>)",`,
    `          secondary: "rgb(${hexToRgbString(theme.secondary)} / <alpha-value>)",`,
    `          accent: "rgb(${hexToRgbString(theme.accent)} / <alpha-value>)",`,
    `          background: "${theme.background}",`,
    `          surface: "${theme.surface}",`,
    `          text: "${theme.text}",`,
    '          status: {',
    '            red: "#EF4444",',
    '            amber: "#FFB800",',
    '            green: "#10B981",',
    '          },',
    '        },',
    '      },',
    '      fontFamily: {',
    `        sans: [${escapedFont}, "sans-serif"],`,
    '      },',
    '      borderRadius: {',
    `        ar: "${theme.borderRadius}px",`,
    `        "ar-sm": "${Math.max(0, theme.borderRadius - 4)}px",`,
    `        "ar-lg": "${theme.borderRadius + 4}px",`,
    '      },',
    '    },',
    '  },',
    '};',
    '',
    'export default config;',
    '',
  ];

  return lines.join('\n');
}
