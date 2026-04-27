// Token mirror for TypeScript / runtime access.
// CSS is the source of truth; this file gives us type-safe names for the same tokens.

export const CANVAS = {
  DEFAULT_W: 1280,
  DEFAULT_H: 720,
  PRESETS: {
    hd: { w: 1280, h: 720 },
    fhd: { w: 1920, h: 1080 },
    wuxga: { w: 1920, h: 1200 },
    qhd: { w: 2560, h: 1440 },
    uhd: { w: 3840, h: 2160 },
    a3_landscape: { w: 1684, h: 1191 },
    a4_landscape: { w: 1190, h: 842 },
  },
} as const;

export const GRID = {
  COLS: 12,
  ROWS: 12,
} as const;

export type DensityMode = "dense" | "balanced" | "airy";
export const DENSITY_FACTORS: Record<DensityMode, number> = {
  dense: 0.8,
  balanced: 1.0,
  airy: 1.2,
};

export type ThemeMode = "light" | "dark";

export const FONT_SIZES = [
  "xs",
  "sm",
  "md",
  "lg",
  "xl",
  "2xl",
  "display",
] as const;
export type FontSize = (typeof FONT_SIZES)[number];

export const SPACING_STEPS = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12] as const;
export type SpacingStep = (typeof SPACING_STEPS)[number];

/** Typed CSS-variable reference helpers. Use instead of raw strings. */
export const cssVar = {
  fs: (step: FontSize): string => `var(--fs-${step})`,
  sp: (step: SpacingStep): string => `var(--sp-${step})`,
  color: (name: string): string => `var(--c-${name})`,
  radius: (size: "sm" | "md" | "lg" | "xl" | "pill"): string =>
    `var(--r-${size})`,
  shadow: (size: "sm" | "md" | "lg" | "xl"): string => `var(--shadow-${size})`,
  motion: (speed: "fast" | "base" | "slow"): string => `var(--motion-${speed})`,
  grid: {
    luW: "var(--lu-w)",
    luH: "var(--lu-h)",
    outer: "var(--outer)",
    gutter: "var(--gutter)",
  },
} as const;

/** Runtime controller — updates root CSS custom properties. */
export const tokensController = {
  setCanvasSize(w: number, h: number): void {
    const root = document.documentElement;
    root.style.setProperty("--canvas-w", String(w));
    root.style.setProperty("--canvas-h", String(h));
  },
  setCanvasPreset(preset: keyof typeof CANVAS.PRESETS): void {
    const p = CANVAS.PRESETS[preset];
    this.setCanvasSize(p.w, p.h);
  },
  setDensity(mode: DensityMode): void {
    document.documentElement.dataset.density = mode;
  },
  setTheme(mode: ThemeMode): void {
    document.documentElement.dataset.theme = mode;
  },
  setScale(scale: number): void {
    document.documentElement.style.setProperty("--scale", String(scale));
  },
  setAccent(hue: number, chroma = 0.13, lightness = 0.5): void {
    const root = document.documentElement;
    root.style.setProperty("--accent-h", String(hue));
    root.style.setProperty("--accent-c", String(chroma));
    root.style.setProperty("--accent-l", String(lightness));
  },
} as const;
