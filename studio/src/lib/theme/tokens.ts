/**
 * Design System Tokens - ALUCA Studio
 *
 * Mirrors CSS custom properties for use in JS/TS (Framer Motion, computed styles).
 * Accent uses oklch parametric model — default Aurora cyan h=215, matching tokens.css.
 */

export const colors = {
  /** Accent — Aurora Group brand primary #2ECDE7 */
  accent: 'oklch(0.78 0.10 215)',
  accentSoft: 'oklch(0.78 0.10 215 / 0.16)',
  accentInk: 'oklch(0.18 0.04 215)',

  /** Legacy brand aliases — kept for backward-compat */
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

  /** Surface palette (dark) */
  bg:    '#0b0b0c',
  bg2:   '#101012',
  panel: '#131316',
  ink:   '#f4f4f2',
  ink2:  '#c9c9cd',
  ink3:  '#8a8a90',
  ink4:  '#5a5a60',

  semantic: {
    success: 'oklch(0.72 0.15 150)',
    warning: '#FFB800',
    danger:  '#F44336',
    info:    '#42A5F5',
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
  ui:      "'Geist', 'Inter', ui-sans-serif, system-ui, sans-serif",
  sans:    "'Geist', 'Inter', ui-sans-serif, system-ui, sans-serif",
  mono:    "'Geist Mono', 'JetBrains Mono', ui-monospace, monospace",
  display: "'Geist', 'Inter', system-ui, sans-serif",
} as const;

export const transitions = {
  easeOut: 'cubic-bezier(0.16, 1, 0.3, 1)',
  fast:    150,
  normal:  250,
  slow:    400,
} as const;

export const fontWeights = {
  light:    300,
  normal:   400,
  medium:   500,
  semibold: 600,
  bold:     700,
} as const;

export const lineHeights = {
  tight:   1.25,
  normal:  1.5,
  relaxed: 1.75,
} as const;

export const letterSpacings = {
  tight:  '-0.025em',
  normal: '0em',
  wide:   '0.025em',
  wider:  '0.05em',
} as const;

export const shadows = {
  none: 'none',
  sm:   '0 1px 0 rgba(0,0,0,0.4)',
  md:   '0 4px 16px rgba(0,0,0,0.4)',
  lg:   '0 24px 48px -16px rgba(0,0,0,0.6), 0 8px 16px rgba(0,0,0,0.3)',
} as const;

/** RAG status colors for KPI cards */
export const ragColors = {
  red:   colors.semantic.danger,
  amber: colors.gold.DEFAULT,
  green: colors.semantic.success,
} as const;

/** Accent hue presets (matching Tweaks panel in BI Framework) */
export const accentPresets = [
  { name: 'Indigo',   h: 250, c: 0.13, l: 0.72 },
  { name: 'Emerald',  h: 150, c: 0.13, l: 0.72 },
  { name: 'Amber',    h:  75, c: 0.13, l: 0.72 },
  { name: 'Rose',     h:  20, c: 0.13, l: 0.72 },
  { name: 'Violet',   h: 290, c: 0.13, l: 0.72 },
  { name: 'Teal',     h: 190, c: 0.13, l: 0.72 },
  { name: 'Graphite', h: 250, c: 0.01, l: 0.55 },
] as const;
