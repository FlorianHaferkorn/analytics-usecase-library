/**
 * Design System Tokens - ActionReady Studio
 *
 * Single source for all design constants used across components.
 * Mirrors CSS custom properties for use in JS/TS (Framer Motion, computed styles).
 */

export const colors = {
  /** --accent / mint */
  mint: {
    DEFAULT: '#00D4AA',
    light: '#33DDBB',
    dark: '#00A888',
  },
  /** --accent-gold / gold */
  gold: {
    DEFAULT: '#FFB800',
    light: '#FFC833',
    dark: '#CC9300',
  },
  /** Light design system base tokens */
  ink:   '#0b0b0c',
  bg:    '#fafaf9',
  panel: '#ffffff',
  accent: '#00D4AA',
  accentGold: '#FFB800',
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

export const fontWeights = {
  light: 300,
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

export const lineHeights = {
  tight: 1.25,
  normal: 1.5,
  relaxed: 1.75,
} as const;

export const letterSpacings = {
  tight: '-0.025em',
  normal: '0em',
  wide: '0.025em',
  wider: '0.05em',
} as const;

export const shadows = {
  none: 'none',
  sm: '0 1px 2px rgba(0,0,0,0.06)',
  md: '0 4px 6px rgba(0,0,0,0.08)',
  lg: '0 10px 15px rgba(0,0,0,0.10)',
  xl: '0 20px 25px rgba(0,0,0,0.12)',
} as const;

/** RAG status colors for KPI cards */
export const ragColors = {
  red: colors.semantic.danger,
  amber: colors.gold.DEFAULT,
  green: colors.mint.DEFAULT,
} as const;
