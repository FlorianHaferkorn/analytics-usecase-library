const EMPTY_DATE = '—';

function isCalendarDate(year: number, month: number, day: number): boolean {
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year
    && date.getUTCMonth() === month - 1
    && date.getUTCDate() === day;
}

/** Format governed metadata dates without locale- or timezone-dependent parsing. */
export function formatReviewDate(value: unknown): string {
  if (typeof value !== 'string' || value.trim() === '') return EMPTY_DATE;

  const source = value.trim();
  const iso = /^(\d{4})-(\d{2})-(\d{2})$/.exec(source);
  const german = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(source);

  if (iso) {
    const [, year, month, day] = iso;
    return isCalendarDate(Number(year), Number(month), Number(day)) ? source : EMPTY_DATE;
  }

  if (german) {
    const [, day, month, year] = german;
    return isCalendarDate(Number(year), Number(month), Number(day))
      ? `${year}-${month}-${day}`
      : EMPTY_DATE;
  }

  return EMPTY_DATE;
}
