import { NextResponse } from 'next/server';

interface RangeValue {
  min: number;
  likely: number;
  max: number;
  unit: string;
}

interface Preset {
  kpi_id: string;
  label: string;
  baseline_range: RangeValue;
  target_range: RangeValue;
  time_horizon_months: number;
  driver_notes: string[];
}

/**
 * PRESETS — Golden 20 KPI presets for ROI analysis.
 * All amounts in EUR, percentages as 0-100, days as numbers.
 */
const PRESETS: Record<string, Preset> = {
  'sales.net_sales.amount': {
    kpi_id: 'sales.net_sales.amount',
    label: 'Net Sales',
    baseline_range: { min: 80e6, likely: 100e6, max: 120e6, unit: 'EUR' },
    target_range: { min: 110e6, likely: 125e6, max: 140e6, unit: 'EUR' },
    time_horizon_months: 12,
    driver_notes: ['Pricing discipline on top accounts', 'Cross-sell penetration', 'Forecast accuracy'],
  },
  'cost.cogs.amount': {
    kpi_id: 'cost.cogs.amount',
    label: 'Cost of Goods Sold',
    baseline_range: { min: 55e6, likely: 62e6, max: 70e6, unit: 'EUR' },
    target_range: { min: 50e6, likely: 56e6, max: 62e6, unit: 'EUR' },
    time_horizon_months: 12,
    driver_notes: ['Supplier consolidation', 'Yield improvement', 'Scrap reduction'],
  },
  'crm.clv.amount': {
    kpi_id: 'crm.clv.amount',
    label: 'Customer Lifetime Value',
    baseline_range: { min: 18000, likely: 24000, max: 32000, unit: 'EUR' },
    target_range: { min: 28000, likely: 34000, max: 42000, unit: 'EUR' },
    time_horizon_months: 18,
    driver_notes: ['Retention rate', 'ARPU uplift', 'Churn reduction'],
  },
  'crm.retention.pct': {
    kpi_id: 'crm.retention.pct',
    label: 'Customer Retention',
    baseline_range: { min: 82, likely: 86, max: 90, unit: '%' },
    target_range: { min: 90, likely: 93, max: 96, unit: '%' },
    time_horizon_months: 12,
    driver_notes: ['Proactive success motions', 'Escalation SLA', 'Renewal nudges'],
  },
  'crm.nps.index': {
    kpi_id: 'crm.nps.index',
    label: 'Net Promoter Score',
    baseline_range: { min: 20, likely: 32, max: 45, unit: 'index' },
    target_range: { min: 45, likely: 55, max: 65, unit: 'index' },
    time_horizon_months: 12,
    driver_notes: ['Onboarding quality', 'OTIF reliability', 'Escalation rate'],
  },
  'crm.revenue_at_risk.amount': {
    kpi_id: 'crm.revenue_at_risk.amount',
    label: 'Revenue at Risk',
    baseline_range: { min: 6e6, likely: 10e6, max: 15e6, unit: 'EUR' },
    target_range: { min: 2e6, likely: 4e6, max: 7e6, unit: 'EUR' },
    time_horizon_months: 12,
    driver_notes: ['OTIF recovery', 'Complaint resolution speed', 'Quality incident rate'],
  },
  'ops.otif.pct': {
    kpi_id: 'ops.otif.pct',
    label: 'On-Time In-Full (Ops)',
    baseline_range: { min: 88, likely: 92, max: 95, unit: '%' },
    target_range: { min: 95, likely: 97, max: 99, unit: '%' },
    time_horizon_months: 9,
    driver_notes: ['Schedule adherence', 'Changeover time', 'Raw material availability'],
  },
  'ops.performance.pct': {
    kpi_id: 'ops.performance.pct',
    label: 'OEE Performance',
    baseline_range: { min: 65, likely: 72, max: 80, unit: '%' },
    target_range: { min: 80, likely: 85, max: 90, unit: '%' },
    time_horizon_months: 12,
    driver_notes: ['Availability', 'Performance rate', 'Quality rate'],
  },
  'quality.fpy.pct': {
    kpi_id: 'quality.fpy.pct',
    label: 'First Pass Yield',
    baseline_range: { min: 85, likely: 90, max: 94, unit: '%' },
    target_range: { min: 94, likely: 97, max: 99, unit: '%' },
    time_horizon_months: 12,
    driver_notes: ['Process SPC', 'Operator training', 'Component quality'],
  },
  'quality.copq.amount': {
    kpi_id: 'quality.copq.amount',
    label: 'Cost of Poor Quality',
    baseline_range: { min: 3.5e6, likely: 5e6, max: 7e6, unit: 'EUR' },
    target_range: { min: 1.5e6, likely: 2.5e6, max: 3.5e6, unit: 'EUR' },
    time_horizon_months: 12,
    driver_notes: ['Scrap reduction', 'Warranty claims', 'Rework hours'],
  },
  'supply.otif.pct': {
    kpi_id: 'supply.otif.pct',
    label: 'Supplier OTIF',
    baseline_range: { min: 85, likely: 90, max: 94, unit: '%' },
    target_range: { min: 94, likely: 97, max: 99, unit: '%' },
    time_horizon_months: 9,
    driver_notes: ['Vendor scorecards', 'Buffer stock', 'Forecast sharing'],
  },
  'inv.dio.days': {
    kpi_id: 'inv.dio.days',
    label: 'Days Inventory Outstanding',
    baseline_range: { min: 60, likely: 75, max: 95, unit: 'days' },
    target_range: { min: 40, likely: 50, max: 60, unit: 'days' },
    time_horizon_months: 12,
    driver_notes: ['SKU rationalisation', 'Safety stock sizing', 'Forecast accuracy'],
  },
  'inv.stockout.pct': {
    kpi_id: 'inv.stockout.pct',
    label: 'Stockout Rate',
    baseline_range: { min: 3, likely: 5, max: 8, unit: '%' },
    target_range: { min: 0.5, likely: 1.5, max: 2.5, unit: '%' },
    time_horizon_months: 9,
    driver_notes: ['Replenishment cadence', 'ABC policy', 'Lead-time reduction'],
  },
  'plan.forecast.accuracy.pct': {
    kpi_id: 'plan.forecast.accuracy.pct',
    label: 'Forecast Accuracy',
    baseline_range: { min: 60, likely: 68, max: 75, unit: '%' },
    target_range: { min: 75, likely: 82, max: 88, unit: '%' },
    time_horizon_months: 12,
    driver_notes: ['Demand sensing', 'Statistical baseline', 'Commercial input quality'],
  },
  'plan.forecast.bias.pct': {
    kpi_id: 'plan.forecast.bias.pct',
    label: 'Forecast Bias',
    baseline_range: { min: -15, likely: -8, max: 5, unit: '%' },
    target_range: { min: -3, likely: 0, max: 3, unit: '%' },
    time_horizon_months: 12,
    driver_notes: ['Bias monitoring', 'Overlays review', 'Sales incentive alignment'],
  },
  'margin.gm.amount': {
    kpi_id: 'margin.gm.amount',
    label: 'Gross Margin Amount',
    baseline_range: { min: 25e6, likely: 35e6, max: 45e6, unit: 'EUR' },
    target_range: { min: 45e6, likely: 55e6, max: 65e6, unit: 'EUR' },
    time_horizon_months: 12,
    driver_notes: ['Price realisation', 'COGS programme', 'Mix shift to premium'],
  },
  'margin.gm.pct': {
    kpi_id: 'margin.gm.pct',
    label: 'Gross Margin %',
    baseline_range: { min: 28, likely: 33, max: 38, unit: '%' },
    target_range: { min: 38, likely: 42, max: 46, unit: '%' },
    time_horizon_months: 12,
    driver_notes: ['Price discipline', 'Productivity savings', 'Scrap reduction'],
  },
  'svc.nps.index': {
    kpi_id: 'svc.nps.index',
    label: 'Service NPS',
    baseline_range: { min: 15, likely: 25, max: 35, unit: 'index' },
    target_range: { min: 40, likely: 50, max: 60, unit: 'index' },
    time_horizon_months: 12,
    driver_notes: ['First contact resolution', 'Response time', 'Agent enablement'],
  },
  'svc.fcr.pct': {
    kpi_id: 'svc.fcr.pct',
    label: 'First Contact Resolution',
    baseline_range: { min: 60, likely: 70, max: 78, unit: '%' },
    target_range: { min: 80, likely: 86, max: 92, unit: '%' },
    time_horizon_months: 9,
    driver_notes: ['Knowledge base quality', 'Routing logic', 'Agent training'],
  },
  'svc.escalation.pct': {
    kpi_id: 'svc.escalation.pct',
    label: 'Escalation Rate',
    baseline_range: { min: 8, likely: 12, max: 18, unit: '%' },
    target_range: { min: 2, likely: 4, max: 6, unit: '%' },
    time_horizon_months: 9,
    driver_notes: ['Root cause action', 'Skill tier coverage', 'Preventive outreach'],
  },
};

/**
 * GET /api/core/presets/[kpiId]
 *
 * Returns a preset for a given KPI ID (Golden 20).
 * Response: { preset: Preset }
 * On 404: { error: { code: 'NOT_FOUND', message: '...' } }
 */
export async function GET(_request: Request, { params }: { params: Promise<{ kpiId: string }> }) {
  const { kpiId } = await params;
  const key = decodeURIComponent(kpiId);

  const preset = PRESETS[key];

  if (!preset) {
    return NextResponse.json(
      { error: { code: 'NOT_FOUND', message: `No preset found for KPI: ${key}` } },
      { status: 404 },
    );
  }

  // Return the preset directly at the top level (not wrapped in 'data')
  return NextResponse.json({ preset }, { status: 200 });
}
