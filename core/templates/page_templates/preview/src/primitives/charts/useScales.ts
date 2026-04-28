// ============================================================================
// Scale helpers — pure math, no React. Shared across Line/Bar/Column/Scatter.
// ============================================================================

export interface LinearScale {
  domain: [number, number];
  range: [number, number];
  (v: number): number;
  invert: (pixel: number) => number;
  ticks: (count?: number) => number[];
}

export function linearScale(
  domain: [number, number],
  range: [number, number],
): LinearScale {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const span = d1 - d0 || 1;
  const rspan = r1 - r0;
  const fn = ((v: number) => r0 + ((v - d0) / span) * rspan) as LinearScale;
  fn.domain = domain;
  fn.range = range;
  fn.invert = (pixel: number): number => d0 + ((pixel - r0) / rspan) * span;
  fn.ticks = (count = 5): number[] => niceTicks(d0, d1, count);
  return fn;
}

export interface BandScale {
  domain: string[];
  range: [number, number];
  (key: string): number;
  bandwidth: () => number;
  step: () => number;
}

export function bandScale(
  domain: string[],
  range: [number, number],
  padding = 0.2,
): BandScale {
  const [r0, r1] = range;
  const n = domain.length;
  const step = (r1 - r0) / Math.max(n, 1);
  const band = step * (1 - padding);
  const offset = (step - band) / 2;
  const indexMap = new Map(domain.map((k, i) => [k, i] as const));
  const fn = ((key: string): number => {
    const i = indexMap.get(key);
    if (i === undefined) return NaN;
    return r0 + i * step + offset;
  }) as BandScale;
  fn.domain = domain;
  fn.range = range;
  fn.bandwidth = (): number => band;
  fn.step = (): number => step;
  return fn;
}

// ---- Nice tick algorithm --------------------------------------------------

export function niceTicks(min: number, max: number, count = 5): number[] {
  if (min === max) return [min];
  const span = max - min;
  const raw = span / count;
  const pow = Math.pow(10, Math.floor(Math.log10(raw)));
  const err = raw / pow;
  let stepMult: number;
  if (err >= 7.5) stepMult = 10;
  else if (err >= 3.5) stepMult = 5;
  else if (err >= 1.5) stepMult = 2;
  else stepMult = 1;
  const step = stepMult * pow;
  const start = Math.ceil(min / step) * step;
  const ticks: number[] = [];
  for (let v = start; v <= max + step * 0.0001; v += step) {
    ticks.push(Number(v.toFixed(10)));
  }
  return ticks;
}

// ---- Chart sizing ---------------------------------------------------------
// We render into a virtual viewBox so everything scales with the container.
// Choosing a 320×180 virtual canvas keeps line widths + text sizes readable
// across typical chart slot sizes. Consumers override via viewBox if needed.

export const CHART = {
  VW: 320,
  VH: 180,
  PAD_LEFT: 36,
  PAD_RIGHT: 8,
  PAD_TOP: 10,
  PAD_BOTTOM: 22,
} as const;

export interface ChartBox {
  vw: number;
  vh: number;
  x0: number;
  x1: number;
  y0: number;
  y1: number;
  innerW: number;
  innerH: number;
}

export function chartBox(
  vw: number = CHART.VW,
  vh: number = CHART.VH,
  pad: Partial<typeof CHART> = {},
): ChartBox {
  const padLeft = pad.PAD_LEFT ?? CHART.PAD_LEFT;
  const padRight = pad.PAD_RIGHT ?? CHART.PAD_RIGHT;
  const padTop = pad.PAD_TOP ?? CHART.PAD_TOP;
  const padBottom = pad.PAD_BOTTOM ?? CHART.PAD_BOTTOM;
  return {
    vw,
    vh,
    x0: padLeft,
    x1: vw - padRight,
    y0: padTop,
    y1: vh - padBottom,
    innerW: vw - padLeft - padRight,
    innerH: vh - padTop - padBottom,
  };
}
