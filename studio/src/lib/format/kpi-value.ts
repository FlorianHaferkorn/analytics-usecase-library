/**
 * Formatting a KPI value together with its display unit.
 *
 * Until D-594 the unit was read from the id suffix (`…​.pct`, `…​.days`). A numbered ID
 * (`KPI-COM-013`) carries no meaning, so the unit comes from the catalog field
 * `business.unit_format` (`percent_1`, `eur_0`, `days_0`, …) — the server passes it along.
 */

/** unit_format prefix → display unit. Currency is left to the data (`AuroraKpiValue.unit`). */
const UNIT_BY_FORMAT: ReadonlyArray<readonly [string, string]> = [
  ['percent', '%'],
  ['days', 'd'],
  ['hours', 'h'],
  ['minutes', 'min'],
];

/** The display unit implied by a catalog `unit_format`, or '' when it carries none. */
export function unitFromFormat(unitFormat?: string | null): string {
  const format = (unitFormat ?? '').toLowerCase();
  const match = UNIT_BY_FORMAT.find(([prefix]) => format.startsWith(prefix));
  return match ? match[1] : '';
}

/** Durations and counts cannot fall below zero (slider floor). */
export function isTimeOrCountFormat(unitFormat?: string | null): boolean {
  return /^(days|hours|minutes|units|count|defects)/.test((unitFormat ?? '').toLowerCase());
}

/** Decimals that read naturally for the unit — currency and counts stay whole. */
function precisionFor(unit: string): number {
  if (unit === '€') return 0;
  if (unit === '') return 0;
  return 1;
}

/**
 * Format `value` with its display `unit` (see `unitFromFormat`).
 *
 * `%` binds directly to the number (`42.3%`); every other unit is separated by a
 * non-breaking space so it never wraps away from its value.
 */
export function formatKpiValue(value: number, suppliedUnit = ''): string {
  if (!Number.isFinite(value)) return '—';

  const unit = suppliedUnit.toUpperCase() === 'EUR' ? '€' : suppliedUnit;
  const formatted = value.toLocaleString('de-DE', {
    minimumFractionDigits: precisionFor(unit),
    maximumFractionDigits: precisionFor(unit),
  });

  if (!unit) return formatted;
  if (unit === '%') return `${formatted}%`;
  return `${formatted} ${unit}`;
}
