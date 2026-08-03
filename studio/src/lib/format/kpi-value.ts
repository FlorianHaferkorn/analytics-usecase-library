/**
 * Formatting a KPI value together with the unit implied by its `kpi_id`.
 *
 * The unit lives in the id suffix by convention (`…​.pct`, `…​.days`, `…​.amount`, …),
 * so a value and its id are enough — no catalog lookup, which keeps this usable from
 * client components that only received ids as props.
 */

/** Suffix → unit. Order matters only in that every key is checked as a substring. */
const UNIT_BY_SUFFIX: ReadonlyArray<readonly [string, string]> = [
  ['.pct', '%'],
  ['.days', 'd'],
  ['.hours', 'h'],
  ['.minutes', 'min'],
  ['.amount', '€'],
  ['.units', ''],
  ['.count', ''],
];

/** The unit implied by a `kpi_id`, or '' when the id carries no unit suffix. */
export function kpiUnit(kpiId: string): string {
  const match = UNIT_BY_SUFFIX.find(([suffix]) => kpiId.includes(suffix));
  return match ? match[1] : '';
}

/** Decimals that read naturally for the unit — currency and counts stay whole. */
function precisionFor(unit: string): number {
  if (unit === '€') return 0;
  if (unit === '') return 0;
  return 1;
}

/**
 * Format `value` for display next to the KPI identified by `kpiId`.
 *
 * `%` binds directly to the number (`42.3%`); every other unit is separated by a
 * non-breaking space so it never wraps away from its value.
 */
export function formatKpiValue(value: number, kpiId: string): string {
  if (!Number.isFinite(value)) return '—';

  const unit = kpiUnit(kpiId);
  const formatted = value.toLocaleString('de-DE', {
    minimumFractionDigits: precisionFor(unit),
    maximumFractionDigits: precisionFor(unit),
  });

  if (!unit) return formatted;
  if (unit === '%') return `${formatted}%`;
  return `${formatted} ${unit}`;
}
