/**
 * Volume Guard — suppresses alerts on negligible KPI volumes.
 *
 * Prevents firing alerts when the underlying metric is too small
 * to be meaningful (e.g., margin alert on 3 transactions).
 *
 * TODO: not yet wired into production — currently only used in tests.
 */

/** Default minimum thresholds by KPI type suffix. */
const MIN_THRESHOLDS: Record<string, number> = {
  '.count': 10,
  '.amount': 100,
  '.units': 5,
  '.hours': 1,
  '.days': 1,
};

/**
 * Check if a KPI value is above the minimum volume threshold.
 * Returns true if the value is significant enough to trigger alerts.
 */
export function isSignificantVolume(
  kpiId: string,
  value: number,
  customThreshold?: number,
): boolean {
  if (customThreshold !== undefined) {
    return Math.abs(value) >= customThreshold;
  }

  // Check against known type thresholds
  for (const [suffix, minVal] of Object.entries(MIN_THRESHOLDS)) {
    if (kpiId.includes(suffix)) {
      return Math.abs(value) >= minVal;
    }
  }

  // Default: any non-zero value is significant
  return Math.abs(value) > 0;
}
