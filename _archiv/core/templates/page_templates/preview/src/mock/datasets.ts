// ============================================================================
// Mock datasets — realistic demo data for T1–T4 page templates.
// ============================================================================
// These are intentionally deterministic (no Math.random) so that visual
// regression tests are stable. All values are plausible but fictional —
// modelled loosely on an industrial / B2B commercial context.
// ============================================================================

// ---- Shared types ---------------------------------------------------------

export type TrendDirection = "up" | "down" | "flat";
export type SeverityTone = "ok" | "watch" | "warn" | "critical";

export interface KpiDatum {
  id: string;
  label: string;
  unit: string;
  value: number;
  valueFormatted: string;
  deltaPct: number;              // vs prior period, e.g. -0.042 = -4.2%
  deltaAbs: number;
  direction: TrendDirection;
  tone: SeverityTone;
  target?: number;
  sparkline: number[];           // 12 trailing points
}

export interface TimePoint {
  t: string;                     // "2026-01", "W12", "Day 14"
  v: number;
}

export interface TimeSeries {
  id: string;
  label: string;
  unit: string;
  points: TimePoint[];
  threshold?: { lower: number; upper: number };
  annotations?: { t: string; label: string }[];
}

export interface VarianceBridge {
  anchorLabel: string;
  anchorValue: number;
  steps: {
    id: string;
    label: string;
    delta: number;               // signed
    tone: SeverityTone;
  }[];
  endLabel: string;
  unit: string;
}

export interface DriverRow {
  id: string;
  name: string;
  actual: number;
  plan: number;
  varianceAbs: number;
  variancePct: number;
  tone: SeverityTone;
  owner: string;
}

export interface ScatterPoint {
  id: string;
  label: string;
  x: number;
  y: number;
  size: number;                  // e.g. revenue impact
  tone: SeverityTone;
}

export interface ActionItem {
  id: string;
  title: string;
  impact: "high" | "medium" | "low";
  effort: "high" | "medium" | "low";
  eta: string;                   // "2026-05-03"
  owner: string;
  tone: SeverityTone;
}

// ---- T1 Strategic Overview ------------------------------------------------

export const T1_KPIS: KpiDatum[] = [
  {
    id: "revenue_ytd",
    label: "Revenue YTD",
    unit: "€M",
    value: 142.8,
    valueFormatted: "€142.8M",
    deltaPct: 0.081,
    deltaAbs: 10.7,
    direction: "up",
    tone: "ok",
    target: 150,
    sparkline: [108, 114, 117, 119, 122, 126, 128, 131, 135, 138, 140, 142.8],
  },
  {
    id: "gross_margin",
    label: "Gross margin",
    unit: "%",
    value: 38.4,
    valueFormatted: "38.4%",
    deltaPct: -0.012,
    deltaAbs: -0.5,
    direction: "down",
    tone: "watch",
    target: 40,
    sparkline: [39.2, 39.0, 38.9, 38.8, 38.9, 38.7, 38.6, 38.5, 38.6, 38.5, 38.4, 38.4],
  },
  {
    id: "nps",
    label: "NPS",
    unit: "",
    value: 48,
    valueFormatted: "48",
    deltaPct: 0.043,
    deltaAbs: 2,
    direction: "up",
    tone: "ok",
    target: 50,
    sparkline: [41, 42, 43, 44, 45, 45, 46, 46, 47, 47, 48, 48],
  },
  {
    id: "churn_rate",
    label: "Churn (ARR)",
    unit: "%",
    value: 6.8,
    valueFormatted: "6.8%",
    deltaPct: 0.058,
    deltaAbs: 0.4,
    direction: "up",
    tone: "warn",
    target: 5,
    sparkline: [5.6, 5.8, 6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.7, 6.8],
  },
  {
    id: "pipeline_coverage",
    label: "Pipeline coverage",
    unit: "×",
    value: 3.1,
    valueFormatted: "3.1×",
    deltaPct: -0.086,
    deltaAbs: -0.3,
    direction: "down",
    tone: "watch",
    target: 3.5,
    sparkline: [3.8, 3.7, 3.7, 3.6, 3.5, 3.4, 3.4, 3.3, 3.2, 3.2, 3.1, 3.1],
  },
];

export const T1_REVENUE_TREND: TimeSeries = {
  id: "revenue_trend",
  label: "Revenue by month",
  unit: "€M",
  points: [
    { t: "2025-05", v: 10.8 },
    { t: "2025-06", v: 11.2 },
    { t: "2025-07", v: 10.5 },
    { t: "2025-08", v: 9.9 },
    { t: "2025-09", v: 11.7 },
    { t: "2025-10", v: 12.4 },
    { t: "2025-11", v: 12.8 },
    { t: "2025-12", v: 13.6 },
    { t: "2026-01", v: 11.4 },
    { t: "2026-02", v: 11.9 },
    { t: "2026-03", v: 12.6 },
    { t: "2026-04", v: 12.0 },
  ],
  threshold: { lower: 10, upper: 13.5 },
  annotations: [
    { t: "2025-09", label: "Pricing uplift" },
    { t: "2026-01", label: "Q1 soft-start" },
  ],
};

export const T1_DRIVER_ROWS: DriverRow[] = [
  { id: "d1", name: "Enterprise – EMEA",   actual: 48.2, plan: 46.0, varianceAbs: 2.2,  variancePct: 0.048,  tone: "ok",       owner: "A. Keller" },
  { id: "d2", name: "Enterprise – NA",     actual: 39.1, plan: 42.5, varianceAbs: -3.4, variancePct: -0.080, tone: "warn",     owner: "M. Okonkwo" },
  { id: "d3", name: "Mid-market – EMEA",   actual: 28.6, plan: 27.0, varianceAbs: 1.6,  variancePct: 0.059,  tone: "ok",       owner: "S. Vrábel" },
  { id: "d4", name: "Mid-market – APAC",   actual: 14.2, plan: 16.0, varianceAbs: -1.8, variancePct: -0.113, tone: "warn",     owner: "T. Sato" },
  { id: "d5", name: "SMB – Global",        actual: 12.7, plan: 12.0, varianceAbs: 0.7,  variancePct: 0.058,  tone: "ok",       owner: "R. Leclerc" },
];

// ---- T2 Tactical Variance -------------------------------------------------

export const T2_KPIS: KpiDatum[] = [
  {
    id: "ebitda_q",
    label: "EBITDA – Q",
    unit: "€M",
    value: 17.3,
    valueFormatted: "€17.3M",
    deltaPct: -0.063,
    deltaAbs: -1.16,
    direction: "down",
    tone: "warn",
    target: 19.8,
    sparkline: [19.2, 18.9, 18.6, 18.4, 18.1, 17.9, 17.8, 17.6, 17.5, 17.4, 17.3, 17.3],
  },
  {
    id: "plan_actual_gap",
    label: "Actual vs Plan",
    unit: "%",
    value: -12.6,
    valueFormatted: "-12.6%",
    deltaPct: -0.031,
    deltaAbs: -0.4,
    direction: "down",
    tone: "critical",
    sparkline: [-6.1, -7.2, -8.0, -8.9, -9.4, -10.1, -10.7, -11.2, -11.7, -12.1, -12.4, -12.6],
  },
  {
    id: "forecast_accuracy",
    label: "Forecast accuracy",
    unit: "%",
    value: 82.7,
    valueFormatted: "82.7%",
    deltaPct: 0.012,
    deltaAbs: 1.0,
    direction: "up",
    tone: "ok",
    target: 85,
    sparkline: [79.0, 79.4, 80.1, 80.5, 80.9, 81.2, 81.6, 81.9, 82.1, 82.4, 82.6, 82.7],
  },
];

export const T2_VARIANCE_BRIDGE: VarianceBridge = {
  anchorLabel: "Plan EBITDA",
  anchorValue: 19.8,
  unit: "€M",
  steps: [
    { id: "s1", label: "Volume mix",        delta: -1.3, tone: "warn" },
    { id: "s2", label: "Price realisation", delta:  0.6, tone: "ok" },
    { id: "s3", label: "Raw materials",     delta: -1.1, tone: "critical" },
    { id: "s4", label: "Labour",            delta: -0.5, tone: "warn" },
    { id: "s5", label: "OpEx discipline",   delta:  0.4, tone: "ok" },
    { id: "s6", label: "One-offs",          delta: -0.6, tone: "warn" },
  ],
  endLabel: "Actual EBITDA",
};

export const T2_DRIVER_ROWS: DriverRow[] = [
  { id: "t2d1", name: "Steel input cost",       actual: 6.80, plan: 5.70, varianceAbs:  1.10, variancePct:  0.193, tone: "critical", owner: "COO office" },
  { id: "t2d2", name: "Contract labour hrs",    actual: 13200, plan: 12000, varianceAbs: 1200, variancePct: 0.100, tone: "warn",     owner: "Ops" },
  { id: "t2d3", name: "Freight – maritime",     actual: 2.10, plan: 1.95, varianceAbs:  0.15, variancePct:  0.077, tone: "watch",    owner: "Logistics" },
  { id: "t2d4", name: "Price discipline",       actual: 96.8, plan: 95.0, varianceAbs:  1.8,  variancePct:  0.019, tone: "ok",       owner: "Commercial" },
  { id: "t2d5", name: "SG&A discipline",        actual: 14.4, plan: 14.8, varianceAbs: -0.4,  variancePct: -0.027, tone: "ok",       owner: "CFO office" },
];

// ---- T3 Operational Monitoring --------------------------------------------

export const T3_STATUS_TILES: KpiDatum[] = [
  {
    id: "oee",
    label: "OEE – Plant A",
    unit: "%",
    value: 84.1,
    valueFormatted: "84.1%",
    deltaPct: -0.009,
    deltaAbs: -0.8,
    direction: "down",
    tone: "watch",
    target: 87,
    sparkline: [85.9, 85.6, 85.3, 84.9, 84.8, 84.6, 84.5, 84.4, 84.3, 84.2, 84.1, 84.1],
  },
  {
    id: "otd",
    label: "On-time delivery",
    unit: "%",
    value: 92.4,
    valueFormatted: "92.4%",
    deltaPct: 0.018,
    deltaAbs: 1.6,
    direction: "up",
    tone: "ok",
    target: 95,
    sparkline: [89.8, 90.0, 90.3, 90.7, 91.0, 91.3, 91.6, 91.9, 92.1, 92.2, 92.3, 92.4],
  },
  {
    id: "scrap_rate",
    label: "Scrap rate",
    unit: "%",
    value: 3.2,
    valueFormatted: "3.2%",
    deltaPct: 0.067,
    deltaAbs: 0.2,
    direction: "up",
    tone: "warn",
    target: 2.5,
    sparkline: [2.8, 2.9, 2.9, 3.0, 3.0, 3.1, 3.1, 3.1, 3.2, 3.2, 3.2, 3.2],
  },
  {
    id: "downtime_hrs",
    label: "Unplanned downtime",
    unit: "h",
    value: 17.6,
    valueFormatted: "17.6 h",
    deltaPct: 0.12,
    deltaAbs: 1.9,
    direction: "up",
    tone: "critical",
    target: 12,
    sparkline: [13.1, 13.5, 14.0, 14.4, 14.9, 15.3, 15.8, 16.3, 16.7, 17.1, 17.4, 17.6],
  },
];

export const T3_THROUGHPUT_SERIES: TimeSeries = {
  id: "plant_throughput",
  label: "Throughput – last 14 days",
  unit: "units/h",
  points: Array.from({ length: 14 }, (_, i) => ({
    t: `Day ${i + 1}`,
    v: [612, 618, 608, 594, 601, 615, 622, 609, 588, 575, 602, 618, 611, 604][i]!,
  })),
  threshold: { lower: 580, upper: 640 },
  annotations: [
    { t: "Day 9", label: "Tool change" },
    { t: "Day 10", label: "Material lot switch" },
  ],
};

export const T3_DETAIL_ROWS: DriverRow[] = [
  { id: "m1",  name: "Line 1 – EU01", actual: 612, plan: 620, varianceAbs: -8,  variancePct: -0.013, tone: "ok",       owner: "Shift A" },
  { id: "m2",  name: "Line 2 – EU01", actual: 594, plan: 620, varianceAbs: -26, variancePct: -0.042, tone: "watch",    owner: "Shift A" },
  { id: "m3",  name: "Line 3 – EU01", actual: 578, plan: 620, varianceAbs: -42, variancePct: -0.068, tone: "warn",     owner: "Shift B" },
  { id: "m4",  name: "Line 4 – EU02", actual: 632, plan: 620, varianceAbs:  12, variancePct:  0.019, tone: "ok",       owner: "Shift A" },
  { id: "m5",  name: "Line 5 – EU02", actual: 540, plan: 620, varianceAbs: -80, variancePct: -0.129, tone: "critical", owner: "Shift C" },
  { id: "m6",  name: "Line 6 – US01", actual: 608, plan: 620, varianceAbs: -12, variancePct: -0.019, tone: "ok",       owner: "Shift A" },
];

// ---- T4 Prescriptive Recommendation ---------------------------------------

export const T4_KPIS: KpiDatum[] = [
  {
    id: "expected_uplift",
    label: "Expected uplift",
    unit: "€M",
    value: 4.6,
    valueFormatted: "€4.6M",
    deltaPct: 0.0,
    deltaAbs: 0,
    direction: "flat",
    tone: "ok",
    sparkline: [2.8, 3.1, 3.3, 3.5, 3.7, 3.9, 4.0, 4.1, 4.3, 4.4, 4.5, 4.6],
  },
  {
    id: "confidence",
    label: "Confidence",
    unit: "%",
    value: 78,
    valueFormatted: "78%",
    deltaPct: 0.04,
    deltaAbs: 3,
    direction: "up",
    tone: "ok",
    sparkline: [62, 64, 66, 68, 70, 71, 73, 74, 75, 76, 77, 78],
  },
  {
    id: "time_to_value",
    label: "Time to value",
    unit: "wk",
    value: 6,
    valueFormatted: "6 wk",
    deltaPct: 0.0,
    deltaAbs: 0,
    direction: "flat",
    tone: "watch",
    sparkline: [8, 8, 8, 7, 7, 7, 7, 7, 6, 6, 6, 6],
  },
];

export const T4_IMPACT_SCATTER: ScatterPoint[] = [
  { id: "a1", label: "Repricing SKU cluster 3",  x: 3, y: 4.2, size: 1.8, tone: "ok" },
  { id: "a2", label: "Automate QA line 5",       x: 4, y: 3.6, size: 1.3, tone: "ok" },
  { id: "a3", label: "Renegotiate freight APAC", x: 5, y: 3.1, size: 1.1, tone: "watch" },
  { id: "a4", label: "Rework supplier contract", x: 6, y: 2.8, size: 0.9, tone: "watch" },
  { id: "a5", label: "Shift labour mix plant A", x: 2, y: 2.5, size: 0.7, tone: "ok" },
  { id: "a6", label: "Exit low-margin SKUs",     x: 7, y: 4.9, size: 2.0, tone: "warn" },
  { id: "a7", label: "Deploy predictive maint.", x: 8, y: 3.4, size: 1.2, tone: "watch" },
  { id: "a8", label: "Upskill shift C",          x: 3, y: 1.8, size: 0.6, tone: "ok" },
];

export const T4_ACTION_QUEUE: ActionItem[] = [
  { id: "q1", title: "Approve repricing SKU cluster 3",  impact: "high",   effort: "low",    eta: "2026-05-03", owner: "Commercial", tone: "ok" },
  { id: "q2", title: "Fund predictive maint. pilot",     impact: "high",   effort: "medium", eta: "2026-05-17", owner: "Ops",        tone: "watch" },
  { id: "q3", title: "Greenlight SKU exit – review",     impact: "high",   effort: "high",   eta: "2026-06-02", owner: "CFO",        tone: "warn" },
  { id: "q4", title: "Upskill Shift C operators",        impact: "medium", effort: "low",    eta: "2026-05-10", owner: "HR",         tone: "ok" },
];
