/** The canonical Golden-20 KPI IDs used across the Blueprint page and Excel export. */
export const GOLDEN_20_IDS = [
  'sales.net_sales.amount',
  'cost.cogs.amount',
  'crm.clv.amount',
  'crm.retention.pct',
  'crm.nps.index',
  'crm.revenue_at_risk.amount',
  'ops.otif.pct',
  'ops.performance.pct',
  'quality.fpy.pct',
  'quality.copq.amount',
  'supply.otif.pct',
  'inv.dio.days',
  'inv.stockout.pct',
  'plan.forecast.accuracy.pct',
  'plan.forecast.bias.pct',
  'margin.gm.amount',
  'margin.gm.pct',
  'svc.nps.index',
  'svc.fcr.pct',
  'svc.escalation.pct',
] as const;

export const GOLDEN_20_IDS_SET: Set<string> = new Set(GOLDEN_20_IDS);
