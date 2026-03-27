/**
 * Design System Tokens - ActionReady Studio
 *
 * Single source for all design constants used across components.
 * Mirrors CSS custom properties for use in JS/TS (Framer Motion, computed styles).
 */

export const colors = {
  mint: {
    DEFAULT: '#00D4AA',
    light: '#33DDBB',
    dark: '#00A888',
  },
  gold: {
    DEFAULT: '#FFB800',
    light: '#FFC833',
    dark: '#CC9300',
  },
  slate: {
    950: '#020617',
    900: '#0F172A',
    800: '#1E293B',
    700: '#334155',
    600: '#475569',
    500: '#64748B',
    400: '#94A3B8',
    300: '#CBD5E1',
    200: '#E2E8F0',
    100: '#F1F5F9',
    50: '#F8FAFC',
  },
  semantic: {
    success: '#00D4AA',
    warning: '#FFB800',
    danger: '#EF4444',
    info: '#3B82F6',
  },
} as const;

export const spacing = {
  0: '0rem',
  0.5: '0.25rem',
  1: '0.5rem',
  1.5: '0.75rem',
  2: '1rem',
  3: '1.5rem',
  4: '2rem',
  5: '2.5rem',
  6: '3rem',
  8: '4rem',
} as const;

export const radii = {
  sm: '0.375rem',
  md: '0.5rem',
  lg: '0.75rem',
  xl: '1rem',
} as const;

export const fonts = {
  sans: "'Inter', ui-sans-serif, system-ui, sans-serif",
  mono: "'JetBrains Mono', ui-monospace, monospace",
} as const;

export const transitions = {
  easeOut: 'cubic-bezier(0.16, 1, 0.3, 1)',
  fast: 150,
  normal: 250,
  slow: 400,
} as const;

/** RAG status colors for KPI cards */
export const ragColors = {
  red: colors.semantic.danger,
  amber: colors.gold.DEFAULT,
  green: colors.mint.DEFAULT,
} as const;
