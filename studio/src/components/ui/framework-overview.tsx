'use client';

import type { CSSProperties } from 'react';
import Link from 'next/link';
import { StudioMetric, StudioMetricBar } from './studio-page';
import styles from './framework-overview.module.css';

interface DomainEntry { name: string; count: number }
interface TopKpi {
  id: string;
  name: string;
  ref: string;
  unit: string;
  domain: string;
  completeness: number;
  auroraValue?: string;
  auroraLabel?: string;
}

export interface ActivityItem {
  role_title: string;
  initials: string;
  action: string;
  target_id: string;
  time: string;
}

export interface FrameworkOverviewProps {
  stats: {
    kpiCount: number;
    bracketCount: number;
    actionCount: number;
    pendingReviews: number;
    certified: number;
    inReview: number;
    totalDomains: number;
    golden20Present: number;
    golden20Total: number;
    orphanActions: number;
  };
  domains: DomainEntry[];
  topKpis: TopKpi[];
  activity?: ActivityItem[];
  auditSparkline?: number[];
  drift?: {
    errorCount: number;
    warningCount: number;
    topIssues: Array<{ artifactId: string; message: string; severity: string }>;
  };
}

const DOMAIN_COLORS = [
  'oklch(0.72 0.07 215)',
  'oklch(0.62 0.06 195)',
  'oklch(0.55 0.05 245)',
  'oklch(0.68 0.05 165)',
  'oklch(0.50 0.04 270)',
  'oklch(0.78 0.04 80)',
  'oklch(0.45 0.04 220)',
  'oklch(0.65 0.05 140)',
];

function domainColor(index: number) {
  return DOMAIN_COLORS[index % DOMAIN_COLORS.length];
}

function Sparkline({ data }: { data: number[] }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const width = 152;
  const height = 36;
  const points = data.map((value, index) => [
    (index / Math.max(data.length - 1, 1)) * width,
    height - ((value - min) / range) * (height - 4) - 2,
  ] as [number, number]);
  const path = `M${points.map((point) => point.join(',')).join(' L')}`;
  const area = `${path} L${width},${height} L0,${height} Z`;

  return (
    <svg className={styles.sparkline} viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Audit activity over the last 14 days">
      <path d={area} fill="var(--accent)" opacity="0.08" />
      <path d={path} fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={points.at(-1)?.[0] ?? 0} cy={points.at(-1)?.[1] ?? 0} r="2.5" fill="var(--accent)" />
    </svg>
  );
}

function DonutChart({ percent }: { percent: number }) {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  return (
    <svg className={styles.donut} viewBox="0 0 96 96" role="img" aria-label={`${percent}% of library KPIs certified`}>
      <circle cx="48" cy="48" r={radius} stroke="var(--line)" strokeWidth="6" fill="none" />
      <circle
        cx="48" cy="48" r={radius} stroke="var(--accent)" strokeWidth="6" fill="none"
        strokeLinecap="round" strokeDasharray={circumference}
        strokeDashoffset={circumference * (1 - percent / 100)} transform="rotate(-90 48 48)"
      />
      <text x="48" y="52" textAnchor="middle">{percent}%</text>
    </svg>
  );
}

function StatGrid({ stats }: { stats: FrameworkOverviewProps['stats'] }) {
  const goldenPercent = stats.golden20Total > 0
    ? Math.round((stats.golden20Present / stats.golden20Total) * 100)
    : 0;
  const items: Array<{ label: string; value: number; meta: string; tone: 'info' | 'success' | 'warning' | 'default' }> = [
    { label: 'KPIs', value: stats.kpiCount, meta: `${stats.certified} certified · Golden 20 ${goldenPercent}%`, tone: 'info' },
    { label: 'Use cases', value: stats.bracketCount, meta: `${stats.totalDomains} governed domains`, tone: 'default' },
    { label: 'Actions', value: stats.actionCount, meta: stats.orphanActions > 0 ? `${stats.orphanActions} unreferenced` : 'All connected to use cases', tone: stats.orphanActions > 0 ? 'warning' : 'success' },
    { label: 'Review queue', value: stats.pendingReviews, meta: 'Definitions and drift findings', tone: stats.pendingReviews > 0 ? 'warning' : 'success' },
  ];

  return <StudioMetricBar>{items.map((item) => <StudioMetric key={item.label} {...item} />)}</StudioMetricBar>;
}

function nextAction(stats: FrameworkOverviewProps['stats'], drift?: FrameworkOverviewProps['drift']) {
  if ((drift?.errorCount ?? 0) > 0) {
    return { eyebrow: 'Recommended library task', title: 'Review framework drift', description: `${drift!.errorCount} error${drift!.errorCount === 1 ? '' : 's'} were reported in the library checks. Review the affected definitions and rerun the checks before reusing them.`, href: '/drift', action: 'Open drift report' };
  }
  if (stats.pendingReviews > 0) {
    return { eyebrow: 'Recommended library task', title: 'Review pending definitions', description: `${stats.pendingReviews} item${stats.pendingReviews === 1 ? '' : 's'} await review. Check their evidence and record an approval or a requested change.`, href: '/approvals', action: 'Open review queue' };
  }
  if (stats.bracketCount === 0) {
    return { eyebrow: 'Start here', title: 'Capture the first use case', description: 'Add source evidence and derive a governed use-case draft.', href: '/discover', action: 'Start discovery' };
  }
  return { eyebrow: 'Recommended starting point', title: 'Explore a use-case blueprint', description: 'Choose a reusable use case and inspect its KPI-to-action chain. Project scope, customer decisions and delivery readiness still need to be verified in the project package.', href: '/blueprint', action: 'Open blueprint' };
}

function PriorityCard({ stats, drift }: { stats: FrameworkOverviewProps['stats']; drift?: FrameworkOverviewProps['drift'] }) {
  const next = nextAction(stats, drift);
  return (
    <section className={styles.priorityCard}>
      <div><p className={styles.overline}>{next.eyebrow}</p><h2>{next.title}</h2><p>{next.description}</p></div>
      <Link className={styles.primaryLink} href={next.href}>{next.action}<span aria-hidden="true">→</span></Link>
    </section>
  );
}

function CompositionCard({ stats, domains }: { stats: FrameworkOverviewProps['stats']; domains: DomainEntry[] }) {
  const total = domains.reduce((sum, domain) => sum + domain.count, 0) || 1;
  const coverage = stats.kpiCount > 0 ? Math.round((stats.certified / stats.kpiCount) * 100) : 0;

  return (
    <section className={styles.card}>
      <header className={styles.cardHeader}>
        <div><h2>Framework composition</h2><p>Use cases by governed domain</p></div>
        <Link className={styles.textLink} href="/library?tab=usecases">View library</Link>
      </header>
      <div className={styles.compositionBody}>
        <div className={styles.coverage}><DonutChart percent={coverage} /><span>Certified KPIs<br />in the library</span></div>
        <div className={styles.domainSummary}>
          <div className={styles.domainBar} aria-hidden="true">
            {domains.map((domain, index) => (
              <span key={domain.name} style={{ '--segment-grow': domain.count, '--segment-color': domainColor(index) } as CSSProperties} />
            ))}
          </div>
          <div className={styles.domainList}>
            {domains.map((domain, index) => (
              <div key={domain.name} className={styles.domainRow}>
                <span className={styles.domainDot} style={{ '--segment-color': domainColor(index) } as CSSProperties} />
                <span>{domain.name}</span><span>{Math.round((domain.count / total) * 100)}%</span><strong>{domain.count}</strong>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function ActivityFeed({ items }: { items: ActivityItem[] }) {
  return (
    <section className={styles.card}>
      <header className={styles.cardHeader}><div><h2>Recent activity</h2><p>Recorded governance events</p></div></header>
      {items.length === 0 ? (
        <div className={styles.emptyCopy}>No audit events yet. Reviewed definitions and approvals will appear here.</div>
      ) : (
        <div className={styles.activityList}>
          {items.map((item, index) => (
            <div key={`${item.target_id}-${index}`} className={styles.activityRow}>
              <span className={styles.avatar} style={{ '--segment-color': domainColor(index) } as CSSProperties}>{item.initials}</span>
              <div><p><strong>{item.role_title}</strong> {item.action} <span className={styles.mono}>{item.target_id}</span></p><time>{item.time}</time></div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function AttentionCard({ drift, auditSparkline }: { drift: NonNullable<FrameworkOverviewProps['drift']>; auditSparkline: number[] }) {
  const total = drift.errorCount + drift.warningCount;
  const hasActivity = auditSparkline.some((value) => value > 0);
  return (
    <section className={styles.card}>
      <header className={styles.cardHeader}>
        <div><h2>Quality and assurance</h2><p>{total === 0 ? 'No drift issues detected' : `${drift.errorCount} errors · ${drift.warningCount} warnings`}</p></div>
        <Link className={styles.textLink} href="/health">Open health</Link>
      </header>
      <div className={styles.attentionBody}>
        {hasActivity && <div className={styles.sparkBlock}><span>Audit activity · 14 days</span><Sparkline data={auditSparkline} /></div>}
        {total === 0 ? (
          <div className={styles.successState}><span aria-hidden="true">✓</span><div><strong>No drift findings in this report</strong><p>This library check does not establish customer acceptance or project release readiness.</p></div></div>
        ) : drift.topIssues.length === 0 ? (
          <div className={styles.emptyCopy}>The report contains findings, but no detail is available here. Open the drift report to investigate.</div>
        ) : (
          <ul className={styles.issueList}>
            {drift.topIssues.map((issue) => (
              <li key={`${issue.artifactId}-${issue.message}`} data-severity={issue.severity}>
                <span>{issue.severity}</span><div><strong>{issue.artifactId}</strong><p>{issue.message}</p></div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function KeyMetrics({ items }: { items: TopKpi[] }) {
  if (items.length === 0) return null;
  return (
    <section className={styles.metricsSection}>
      <div className={styles.sectionHeading}><div><h2>Golden 20 coverage</h2><p>Highest-priority governed metric definitions</p></div><Link className={styles.textLink} href="/library?tab=kpis">View all KPIs</Link></div>
      <div className={styles.kpiGrid}>
        {items.map((kpi) => (
          <Link key={kpi.id} href={`/detail/kpi/${encodeURIComponent(kpi.id)}`} className={styles.kpiCard}>
            <div className={styles.kpiTitle}><span data-complete={kpi.completeness >= 80} /><strong>{kpi.name}</strong></div>
            <span className={styles.kpiRef}>{kpi.ref}</span>
            <span className={styles.kpiValue}>{kpi.auroraValue ?? `${kpi.completeness}%`}</span>
            <span className={styles.kpiMeta}>{kpi.auroraValue ? `Aurora showcase · ${kpi.auroraLabel ?? 'example value'}` : `${kpi.domain || 'Unassigned'} · metadata completeness`}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}

export function FrameworkOverview({ stats, domains, topKpis, activity = [], auditSparkline = [], drift }: FrameworkOverviewProps) {
  const health = (drift?.errorCount ?? 0) > 0 ? 'Library findings' : stats.pendingReviews > 0 ? 'Library reviews pending' : 'Library inventory';

  return (
    <main className={styles.page}>
      <header className={styles.hero}>
        <div className={styles.heroCopy}>
          <p className={styles.overline}>Studio / Library overview</p>
          <h1>Choose the next useful step.</h1>
          <p>These counts describe the reusable framework library, not the selected project’s progress or readiness. Review project files and saved decisions in the project package.</p>
        </div>
        <div className={styles.heroActions}>
          <span className={styles.healthBadge} data-state={health}>{health}</span>
          <Link className={styles.secondaryLink} href="/package">Open project package</Link>
        </div>
      </header>

      <PriorityCard stats={stats} drift={drift} />
      <StatGrid stats={stats} />
      <details className={styles.details}>
        <summary>Library composition and KPI examples</summary>
        <div className={styles.detailsBody}><CompositionCard stats={stats} domains={domains} /><KeyMetrics items={topKpis} /></div>
      </details>
      <details className={styles.details}>
        <summary>Library quality checks and recorded activity</summary>
        <div className={styles.detailsBody}><div className={styles.secondaryGrid}>{drift && <AttentionCard drift={drift} auditSparkline={auditSparkline} />}<ActivityFeed items={activity} /></div></div>
      </details>
    </main>
  );
}
