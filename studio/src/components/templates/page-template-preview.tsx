'use client';

import { PulseCard } from '@/components/dashboard/pulse-card';
import { Investigator } from '@/components/dashboard/investigator';
import { ActionMatrix } from '@/components/dashboard/action-matrix';
import {
  SAMPLE_KPIS,
  SAMPLE_TREND,
  SAMPLE_WATERFALL,
  SAMPLE_EVIDENCE,
  type KpiSnapshot,
} from '@/lib/dashboard/sample-data';
import type { ThemeConfig } from '@/lib/store/project-store';

export type PageTemplateId = 'T1' | 'T2' | 'T3' | 'T4';

interface Props {
  templateId: PageTemplateId;
  theme: ThemeConfig;
}

const T1_KPIS: KpiSnapshot[] = SAMPLE_KPIS;

const T2_KPIS: KpiSnapshot[] = [
  { kpiId: 'sales.net', label: 'Net Sales YTD', value: 42.3, previousValue: 46.5, target: 46.5, unit: '€M', status: 'off-track' },
  { kpiId: 'sales.vol', label: 'Volume', value: 182, previousValue: 194, target: 194, unit: 'K u', status: 'off-track' },
  { kpiId: 'sales.asp', label: 'ASP', value: 232, previousValue: 236, target: 236, unit: '€', status: 'off-track' },
  { kpiId: 'sales.promo', label: 'Promo Depth', value: 14.2, previousValue: 12.1, target: 12, unit: '%', status: 'at-risk' },
];

const T3_KPIS: KpiSnapshot[] = [
  { kpiId: 'exc.open', label: 'Open Exceptions', value: 14, previousValue: 11, target: 10, unit: '', status: 'off-track' },
  { kpiId: 'exc.crit', label: 'Critical', value: 3, previousValue: 2, target: 2, unit: '', status: 'off-track' },
  { kpiId: 'ops.otif', label: 'OTIF (7d)', value: 91.4, previousValue: 94.0, target: 95, unit: '%', status: 'at-risk' },
  { kpiId: 'exc.age', label: 'Avg Age (open)', value: 4.2, previousValue: 3.4, target: 3, unit: 'd', status: 'off-track' },
];

const TEMPLATE_META: Record<
  PageTemplateId,
  { breadcrumb: string; pageType: string; title: string; decision: string; pageKind: 'overview' | 'detail' }
> = {
  T1: {
    breadcrumb: 'XD · EXECUTIVE · OVERVIEW',
    pageType: 'T1 · STRATEGIC OVERVIEW',
    title: 'Executive KPI Overview',
    decision: 'Are we on track against our strategic objectives?',
    pageKind: 'overview',
  },
  T2: {
    breadcrumb: 'COM · SALES · OVERVIEW',
    pageType: 'T2 · TACTICAL VARIANCE',
    title: 'Sales Performance — Variance Analysis',
    decision: 'Why are we off target, and which levers explain the gap?',
    pageKind: 'overview',
  },
  T3: {
    breadcrumb: 'OPS · OTIF · OVERVIEW',
    pageType: 'T3 · OPERATIONAL MONITORING',
    title: 'Delivery Reliability — Exception Monitor',
    decision: 'Where are we outside threshold, and who needs to act now?',
    pageKind: 'overview',
  },
  T4: {
    breadcrumb: 'COM · MARGIN · DETAIL',
    pageType: 'T4 · PRESCRIPTIVE · DETAIL',
    title: 'DACH Margin Recovery — Recommended Actions',
    decision: 'What action, for which entity, with what expected impact?',
    pageKind: 'detail',
  },
};

export function PageTemplatePreview({ templateId, theme }: Props) {
  const meta = TEMPLATE_META[templateId];
  const themeProps = {
    primary: theme.primary,
    secondary: theme.secondary,
    accent: theme.accent,
    background: theme.background,
    surface: theme.surface,
    text: theme.text,
    borderRadius: theme.borderRadius,
  };

  return (
    <div
      className="flex flex-col h-full overflow-hidden"
      style={{
        backgroundColor: theme.background,
        color: theme.text,
        fontFamily: theme.fontFamily || 'inherit',
      }}
    >
      <PageHeader meta={meta} theme={theme} />

      {meta.pageKind === 'overview' && templateId === 'T1' && (
        <OverviewBody
          kpis={T1_KPIS}
          kpiCols={5}
          themeProps={themeProps}
          main1Title="Net Sales vs Plan (12 months)"
          main2Title="Strategic units on / off track"
          main3Title="Revenue mix across portfolio"
        />
      )}

      {meta.pageKind === 'overview' && templateId === 'T2' && (
        <OverviewBody
          kpis={T2_KPIS}
          kpiCols={4}
          themeProps={themeProps}
          main1Title="Net Sales trend vs Plan"
          main2Title="Variance bridge — Plan to Actual"
          main3Title="Top drivers by region"
          varianceFocus
        />
      )}

      {meta.pageKind === 'overview' && templateId === 'T3' && (
        <T3OverviewBody themeProps={themeProps} />
      )}

      {meta.pageKind === 'detail' && templateId === 'T4' && (
        <T4DetailBody theme={theme} themeProps={themeProps} />
      )}
    </div>
  );
}

function PageHeader({
  meta,
  theme,
}: {
  meta: (typeof TEMPLATE_META)[PageTemplateId];
  theme: ThemeConfig;
}) {
  return (
    <div
      className="shrink-0 px-4 py-3 border-b"
      style={{ borderColor: `color-mix(in srgb, ${theme.text} 12%, transparent)` }}
    >
      <div className="text-[10px] font-mono uppercase tracking-wider opacity-60">{meta.breadcrumb}</div>
      <div className="flex flex-wrap items-baseline gap-2 mt-1">
        <span className="text-[11px] font-semibold px-2 py-0.5 rounded" style={{ background: theme.primary, color: theme.surface }}>
          {meta.pageType}
        </span>
        <h3 className="text-[15px] font-medium m-0">{meta.title}</h3>
      </div>
      <p className="text-[12px] mt-2 opacity-75 m-0">{meta.decision}</p>
    </div>
  );
}

function SlicerBar({ theme }: { theme: ReturnType<typeof themeSlice> }) {
  return (
    <div
      className="flex flex-wrap gap-2 px-4 py-2 shrink-0"
      style={{ background: theme.surface, borderBottom: `1px solid color-mix(in srgb, ${theme.text} 10%, transparent)` }}
    >
      {['Period: YTD 2026', 'Region: All', 'Channel: All'].map((s) => (
        <span
          key={s}
          className="text-[11px] px-2 py-1 rounded border"
          style={{ borderColor: `color-mix(in srgb, ${theme.text} 20%, transparent)` }}
        >
          {s}
        </span>
      ))}
    </div>
  );
}

function themeSlice(theme: ThemeConfig) {
  return {
    primary: theme.primary,
    secondary: theme.secondary,
    surface: theme.surface,
    text: theme.text,
    background: theme.background,
    borderRadius: theme.borderRadius,
  };
}

function OverviewBody({
  kpis,
  kpiCols,
  themeProps,
  main1Title,
  main2Title,
  main3Title,
  varianceFocus = false,
}: {
  kpis: KpiSnapshot[];
  kpiCols: number;
  themeProps: ReturnType<typeof themeSlice>;
  main1Title: string;
  main2Title: string;
  main3Title: string;
  varianceFocus?: boolean;
}) {
  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-auto">
      <div className="px-4 pt-3 pb-2 shrink-0">
        <ZoneLabel>Zone 1 · 3s KPI band</ZoneLabel>
        <div
          className="grid gap-2"
          style={{ gridTemplateColumns: `repeat(${kpiCols}, minmax(0, 1fr))` }}
        >
          {kpis.map((kpi) => (
            <PulseCard key={kpi.kpiId} kpi={kpi} theme={themeProps} />
          ))}
        </div>
      </div>

      <SlicerBar theme={themeProps} />

      <div className="px-4 py-3 flex-1 grid gap-2 min-h-0" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
        <ZoneLabel className="col-span-3">Zone 3 · 30s diagnostics</ZoneLabel>
        <Panel title={main1Title} theme={themeProps}>
          <Investigator
            label={varianceFocus ? 'Net Sales' : 'Net Sales'}
            trendData={SAMPLE_TREND}
            waterfallData={SAMPLE_WATERFALL}
            theme={themeProps}
          />
        </Panel>
        <Panel title={main2Title} theme={themeProps}>
          <div className="text-[11px] opacity-70 h-full flex items-center justify-center">
            {varianceFocus ? 'Variance waterfall / bridge' : 'Ranking vs target'}
          </div>
        </Panel>
        <Panel title={main3Title} theme={themeProps}>
          <div className="text-[11px] opacity-70 h-full flex items-center justify-center">
            Mix / composition chart
          </div>
        </Panel>
      </div>
    </div>
  );
}

function T3OverviewBody({ themeProps }: { themeProps: ReturnType<typeof themeSlice> }) {
  const exceptions = [
    { entity: 'Plant DE-North', metric: 'OTIF', value: '82%', severity: 'Critical', owner: 'Logistics' },
    { entity: 'SKU-4421', metric: 'Fill rate', value: '71%', severity: 'High', owner: 'Supply' },
    { entity: 'Customer Müller AG', metric: 'SLA breach', value: '3d', severity: 'High', owner: 'CS' },
    { entity: 'Route DACH-12', metric: 'Late %', value: '18%', severity: 'Medium', owner: 'Transport' },
  ];

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-auto">
      <div className="px-4 pt-3 pb-2 shrink-0">
        <ZoneLabel>Zone 1 · control panel (exception counts)</ZoneLabel>
        <div className="grid gap-2 grid-cols-4">
          {T3_KPIS.map((kpi) => (
            <PulseCard key={kpi.kpiId} kpi={kpi} theme={themeProps} />
          ))}
        </div>
      </div>

      <SlicerBar theme={themeProps} />

      <div className="px-4 py-3 flex-1 flex gap-3 min-h-0">
        <div className="flex-[2] min-w-0 flex flex-col">
          <ZoneLabel>Zone 3 · exception list (F-pattern)</ZoneLabel>
          <div
            className="flex-1 rounded border overflow-hidden text-[11px]"
            style={{ borderColor: `color-mix(in srgb, ${themeProps.text} 15%, transparent)`, background: themeProps.surface }}
          >
            <div
              className="grid grid-cols-5 gap-2 px-3 py-2 font-medium opacity-60 border-b"
              style={{ borderColor: `color-mix(in srgb, ${themeProps.text} 10%, transparent)` }}
            >
              {['Entity', 'Metric', 'Value', 'Severity', 'Owner'].map((h) => (
                <span key={h}>{h}</span>
              ))}
            </div>
            {exceptions.map((row) => (
              <div
                key={row.entity}
                className="grid grid-cols-5 gap-2 px-3 py-2 border-b"
                style={{
                  borderColor: `color-mix(in srgb, ${themeProps.text} 8%, transparent)`,
                  background:
                    row.severity === 'Critical'
                      ? `color-mix(in srgb, ${themeProps.secondary} 12%, transparent)`
                      : undefined,
                }}
              >
                <span className="font-medium">{row.entity}</span>
                <span>{row.metric}</span>
                <span className="font-mono">{row.value}</span>
                <span style={{ color: row.severity === 'Critical' ? themeProps.secondary : themeProps.primary }}>
                  {row.severity}
                </span>
                <span className="opacity-70">{row.owner}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <ZoneLabel>Spark / trend (support)</ZoneLabel>
          <Panel title="OTIF trend (7d)" theme={themeProps}>
            <Investigator label="OTIF" trendData={SAMPLE_TREND} waterfallData={SAMPLE_WATERFALL} theme={themeProps} />
          </Panel>
        </div>
      </div>
    </div>
  );
}

function T4DetailBody({
  theme,
  themeProps,
}: {
  theme: ThemeConfig;
  themeProps: ReturnType<typeof themeSlice>;
}) {
  return (
    <div className="flex flex-1 min-h-0 overflow-hidden">
      <aside
        className="w-[140px] shrink-0 border-r p-3 overflow-auto text-[11px]"
        style={{
          borderColor: `color-mix(in srgb, ${theme.text} 12%, transparent)`,
          background: theme.surface,
        }}
      >
        <ZoneLabel>Slicer pane</ZoneLabel>
        {['Period', 'Region', 'Segment', 'Priority'].map((group) => (
          <div key={group} className="mb-3">
            <div className="font-semibold opacity-60 mb-1">{group}</div>
            {['YTD 2026', 'DACH', 'Core', 'High'].map((item) => (
              <div key={item} className="py-0.5 opacity-80">
                • {item}
              </div>
            ))}
          </div>
        ))}
      </aside>

      <div className="flex-1 flex flex-col min-w-0 overflow-auto p-3 gap-2">
        <Panel title="Smart narrative" theme={themeProps}>
          <p className="text-[12px] leading-relaxed m-0 opacity-90">
            GM% in DACH has been below the 18% threshold for 3 consecutive months. Promotional depth
            increased +2.1pp YoY; 6 accounts account for 72% of the margin gap. Recommended: reduce
            promo depth by 15%.
          </p>
        </Panel>

        <div className="flex-1 min-h-[200px]">
          <ZoneLabel>Detail matrix (300s)</ZoneLabel>
          <ActionMatrix rows={SAMPLE_EVIDENCE} theme={themeProps} />
        </div>

        <Panel title="Action panel · C-M1.1" theme={themeProps}>
          <div className="text-[11px] space-y-1 opacity-85">
            <div>
              <strong>Trigger:</strong> GM% &lt; 18% for 3 months
            </div>
            <div>
              <strong>Owner:</strong> Pricing lead · <strong>Due:</strong> EOM
            </div>
            <div>
              <strong>Expected impact:</strong> +0.8pp GM% by month-end
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}

function ZoneLabel({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`text-[10px] uppercase tracking-wider opacity-50 mb-2 ${className}`}>{children}</div>
  );
}

function Panel({
  title,
  theme,
  children,
}: {
  title: string;
  theme: ReturnType<typeof themeSlice>;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded border flex flex-col min-h-[120px] overflow-hidden"
      style={{
        borderColor: `color-mix(in srgb, ${theme.text} 12%, transparent)`,
        background: theme.surface,
      }}
    >
      <div
        className="px-2 py-1.5 text-[11px] font-medium border-b shrink-0"
        style={{ borderColor: `color-mix(in srgb, ${theme.text} 10%, transparent)` }}
      >
        {title}
      </div>
      <div className="flex-1 p-2 min-h-0 overflow-hidden">{children}</div>
    </div>
  );
}
