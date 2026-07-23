/** Locale-aware display for simulator / compose driver values. */

function deNum(value: number, fractionDigits: number): string {
  return value.toLocaleString('de-DE', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

function isPercentKpi(kpiId: string): boolean {
  return kpiId.includes('.pct') || kpiId.includes('_pct');
}

export function formatKpiDelta(delta: number, kpiId: string): string {
  const sign = delta >= 0 ? '+' : '−';
  const abs = Math.abs(delta);
  if (isPercentKpi(kpiId)) return `${sign}${deNum(abs, 1)} pp`;
  if (kpiId.includes('.amount')) return `${sign}${formatKpiAmount(abs).replace(/^€/, '€')}`;
  if (kpiId.includes('.days')) return `${sign}${deNum(abs, 1)} d`;
  if (kpiId.includes('.hours')) return `${sign}${deNum(abs, 1)} h`;
  if (kpiId.includes('.minutes')) return `${sign}${deNum(abs, 0)} min`;
  return `${sign}${deNum(abs, 1)}`;
}

export function formatKpiAmount(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `€${deNum(value / 1_000_000, 1)}M`;
  if (abs >= 1_000) return `€${deNum(value / 1_000, 1)}K`;
  return `€${deNum(value, 0)}`;
}

/** Primary readout for a driver slider or impact row. */
export function formatKpiValue(value: number, kpiId: string): string {
  if (isPercentKpi(kpiId)) return `${deNum(value, 1)} %`;
  if (kpiId.includes('.amount')) return formatKpiAmount(value);
  if (kpiId.includes('.days')) return `${deNum(value, 1)} d`;
  if (kpiId.includes('.hours')) return `${deNum(value, 1)} h`;
  if (kpiId.includes('.minutes')) return `${deNum(value, 0)} min`;
  if (kpiId.includes('.units') || kpiId.includes('.count')) return deNum(value, 0);
  return deNum(value, 1);
}
