/** Display ranges only: does not change the baseline or impose business constraints. */
export function driverSliderRange(base: number, unit: string, timeOrCount = false) {
  const radius = unit === '%' ? 15 : Math.max(Math.abs(base) * (timeOrCount ? 0.5 : 0.3), 1);
  return {
    minRange: timeOrCount && base >= 0 ? Math.max(0, base - radius) : base - radius,
    maxRange: base + radius,
  };
}

/** Keep a native range valid even if a caller supplies reversed/equal endpoints. */
export function normalizeSliderRange(base: number, min?: number, max?: number) {
  const radius = Math.max(Math.abs(base) * 0.3, 1);
  const low = Number.isFinite(min) ? min! : base - radius;
  const high = Number.isFinite(max) ? max! : base + radius;
  const lower = Math.min(low, high, base);
  const upper = Math.max(low, high, base);
  return lower === upper ? { min: base - radius, max: base + radius } : { min: lower, max: upper };
}
