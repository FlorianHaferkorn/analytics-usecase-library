'use client';

import Link from 'next/link';

/* ── Sub-components ── */

function Sparkline({ data, color = 'var(--accent)', height = 32 }: { data: number[]; color?: string; height?: number }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 120;
  const pts = data.map((v, i) => [(i / (data.length - 1)) * w, height - ((v - min) / range) * (height - 4) - 2] as [number, number]);
  const d = 'M' + pts.map((p) => p.join(',')).join(' L');
  const areaD = d + ` L${w},${height} L0,${height} Z`;
  return (
    <svg width={w} height={height} style={{ display: 'block' }}>
      <path d={areaD} fill={color} opacity="0.08" />
      <path d={d} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={pts[pts.length - 1]![0]} cy={pts[pts.length - 1]![1]} r="2.5" fill={color} />
    </svg>
  );
}

function DonutChart({ pct = 82 }: { pct: number }) {
  const r = 36;
  const c = 2 * Math.PI * r;
  return (
    <svg width="96" height="96" viewBox="0 0 96 96">
      <circle cx="48" cy="48" r={r} stroke="var(--line)" strokeWidth="6" fill="none" />
      <circle cx="48" cy="48" r={r} stroke="var(--accent)" strokeWidth="6" fill="none"
        strokeLinecap="round" strokeDasharray={c}
        strokeDashoffset={c * (1 - pct / 100)}
        transform="rotate(-90 48 48)"
        style={{ transition: 'stroke-dashoffset 600ms ease' }} />
      <text x="48" y="52" textAnchor="middle" fontFamily="var(--font-display)"
        fontSize="20" fontWeight="500" fill="var(--ink)">{pct}%</text>
    </svg>
  );
}

/* ── Types ── */

interface DomainEntry { name: string; count: number }
interface TopKpi { id: string; name: string; ref: string; unit: string; domain: string; completeness: number }

export interface ActivityItem {
  role_title: string;       // e.g. "Sales BI Lead"
  initials: string;         // e.g. "SB"
  action: string;           // e.g. "certified" | "reviewed"
  target_id: string;        // KPI / bracket / action id (mono)
  time: string;             // human-readable
}

export interface FrameworkOverviewProps {
  userName?: string;
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

/* ── Aurora-aligned domain colour ramp ──
 * Quiet, low-chroma cool palette anchored to the brand cyan (215°).
 * Indices wrap cyclically so any number of domains stays in-brand.
 */
const DOMAIN_COLORS = [
  'oklch(0.72 0.07 215)',   // brand cyan, muted
  'oklch(0.62 0.06 195)',   // teal
  'oklch(0.55 0.05 245)',   // dusty blue
  'oklch(0.68 0.05 165)',   // sage
  'oklch(0.50 0.04 270)',   // muted indigo
  'oklch(0.78 0.04 80)',    // warm sand (only neutral)
  'oklch(0.45 0.04 220)',   // dark slate-blue
  'oklch(0.65 0.05 140)',   // muted moss
];
const domainColor = (i: number) => DOMAIN_COLORS[i % DOMAIN_COLORS.length];

/* ── Shared style tokens ── */
const card: React.CSSProperties = {
  background: 'var(--panel)',
  border: '1px solid var(--line)',
  borderRadius: 'var(--radius)',
  overflow: 'hidden',
};
const cardHead: React.CSSProperties = {
  padding: '18px var(--pad)',
  borderBottom: '1px solid var(--line-2)',
  display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12,
};

/* ── Greeting helper ── */
function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 18) return 'Good afternoon';
  return 'Good evening';
}

/* ── Sub-sections ── */

function StatGrid({ stats }: { stats: FrameworkOverviewProps['stats'] }) {
  const goldenPct = stats.golden20Total > 0
    ? Math.round((stats.golden20Present / stats.golden20Total) * 100)
    : 0;
  const items: { label: string; value: number; hint: string; trend?: string }[] = [
    { label: 'KPIs', value: stats.kpiCount, hint: `${stats.certified} certified · Golden 20 ${goldenPct}%` },
    { label: 'Brackets', value: stats.bracketCount, hint: 'Use cases' },
    { label: 'Actions', value: stats.actionCount, hint: stats.orphanActions > 0 ? `${stats.orphanActions} unreferenced` : 'All wired to brackets' },
    { label: 'In review', value: stats.pendingReviews, hint: 'KPI set + drift errors' },
  ];
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--gap)' }}>
      {items.map((item) => (
        <div key={item.label} style={{ ...card, padding: 'var(--pad)', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ fontSize: 12, color: 'var(--ink-3)', letterSpacing: '-0.005em' }}>{item.label}</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 500, color: 'var(--ink)', letterSpacing: '-0.02em', lineHeight: 1 }}>{item.value}</div>
            {item.trend && (
              <span style={{ fontSize: 11.5, color: item.trend.startsWith('+') ? 'oklch(0.52 0.14 150)' : 'oklch(0.55 0.15 30)' }}>{item.trend}</span>
            )}
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--ink-4)' }}>{item.hint}</div>
        </div>
      ))}
    </div>
  );
}

function CompositionCard({ stats, domains }: { stats: FrameworkOverviewProps['stats']; domains: DomainEntry[] }) {
  const total = domains.reduce((s, d) => s + d.count, 0) || 1;
  const certPct = stats.kpiCount > 0 ? Math.round((stats.certified / stats.kpiCount) * 100) : 0;
  return (
    <div style={card}>
      <div style={cardHead}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--ink)', letterSpacing: '-0.01em' }}>Framework composition</div>
            <div style={{ fontSize: 12, color: 'var(--ink-3)', marginTop: 2 }}>How your KPI set is distributed across domains</div>
        </div>
        <Link href="/library?tab=kpis" style={{ ...ghostSmall, textDecoration: 'none' }}>View all →</Link>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 32, padding: 'var(--pad)', alignItems: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
          <DonutChart pct={certPct} />
          <div style={{ fontSize: 11.5, color: 'var(--ink-3)', textAlign: 'center', lineHeight: 1.3 }}>
            Documentation<br/>coverage
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Domain bar */}
          <div style={{ display: 'flex', height: 8, borderRadius: 999, overflow: 'hidden', background: 'var(--line-2)' }}>
            {domains.map((d, i) => (
              <div key={d.name} title={`${d.name} · ${d.count}`} style={{ flex: d.count, background: domainColor(i) }} />
            ))}
          </div>
          {/* Domain list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {domains.map((d, i) => (
              <div key={d.name} style={{ display: 'grid', gridTemplateColumns: '12px 1fr auto auto', gap: 12, alignItems: 'center', fontSize: 13 }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: domainColor(i) }} />
                <span style={{ color: 'var(--ink-2)', textTransform: 'capitalize' }}>{d.name}</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-3)', fontSize: 11.5 }}>
                  {Math.round((d.count / total) * 100)}%
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-4)', fontSize: 11.5, width: 28, textAlign: 'right' }}>{d.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

const ghostSmall: React.CSSProperties = {
  height: 26, padding: '0 10px', borderRadius: 6,
  fontSize: 12, color: 'var(--ink-2)', background: 'transparent',
  border: '1px solid transparent', cursor: 'pointer',
  display: 'inline-flex', alignItems: 'center', gap: 5,
};

function ActivityFeed({ items }: { items: ActivityItem[] }) {
  return (
    <div style={card}>
      <div style={cardHead}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--ink)', letterSpacing: '-0.01em' }}>Recent activity</div>
          <div style={{ fontSize: 12, color: 'var(--ink-3)', marginTop: 2 }}>From audit log</div>
        </div>
      </div>
      <div style={{ padding: '4px 0 12px' }}>
        {items.length === 0 ? (
          <div style={{ padding: '16px var(--pad)', fontSize: 12.5, color: 'var(--ink-3)' }}>
            No recent audit events. Edits to KPI definitions, brackets, or factsheets will appear here.
          </div>
        ) : items.map((item, i) => (
          <div key={i} style={{
            display: 'flex', gap: 12, alignItems: 'flex-start',
            padding: '10px var(--pad)',
            borderTop: i === 0 ? 'none' : '1px solid var(--line-2)',
          }}>
            <div style={{
              width: 24, height: 24, borderRadius: 99, flexShrink: 0,
              background: domainColor(i), color: 'oklch(0.16 0.02 215)',
              display: 'grid', placeItems: 'center',
              fontSize: 10, fontWeight: 600, fontFamily: 'var(--font-display)',
            }}>{item.initials}</div>
            <div style={{ flex: 1, minWidth: 0, fontSize: 12.5, lineHeight: 1.5 }}>
              <span style={{ fontWeight: 500, color: 'var(--ink)' }}>{item.role_title}</span>
              <span style={{ color: 'var(--ink-3)' }}> {item.action} </span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)', fontSize: '0.92em', wordBreak: 'break-all' }}>{item.target_id}</span>
              <div style={{ color: 'var(--ink-4)', fontSize: 11.5, marginTop: 2 }}>{item.time}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function NeedsAttentionCard({ drift, auditSparkline }: {
  drift: NonNullable<FrameworkOverviewProps['drift']>;
  auditSparkline: number[];
}) {
  const total = drift.errorCount + drift.warningCount;
  const hasSpark = auditSparkline.some((v) => v > 0);
  return (
    <div style={card}>
      <div style={cardHead}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--ink)', letterSpacing: '-0.01em' }}>Needs attention</div>
          <div style={{ fontSize: 12, color: 'var(--ink-3)', marginTop: 2 }}>
            {total === 0 ? 'No drift issues detected' : `${drift.errorCount} errors · ${drift.warningCount} warnings`}
          </div>
        </div>
        <Link href="/registry/health" style={{ ...ghostSmall, textDecoration: 'none' }}>Drift scan →</Link>
      </div>
      <div style={{ padding: 'var(--pad)', display: 'flex', flexDirection: 'column', gap: 14 }}>
        {hasSpark && (
          <div>
            <div style={{ fontSize: 11.5, color: 'var(--ink-3)', marginBottom: 6 }}>Audit events (14 days)</div>
            <Sparkline data={auditSparkline} height={36} />
          </div>
        )}
        {drift.topIssues.length === 0 ? (
          <div style={{ fontSize: 12.5, color: 'var(--ink-3)' }}>Framework references are consistent.</div>
        ) : (
          <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {drift.topIssues.map((issue) => (
              <li key={`${issue.artifactId}-${issue.message.slice(0, 24)}`} style={{ fontSize: 12.5, lineHeight: 1.45 }}>
                <span style={{
                  fontSize: 10, fontWeight: 600, textTransform: 'uppercase', marginRight: 6,
                  color: issue.severity === 'error' ? 'oklch(0.55 0.15 30)' : 'oklch(0.62 0.12 80)',
                }}>{issue.severity}</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)', fontSize: '0.92em' }}>{issue.artifactId}</span>
                <span style={{ color: 'var(--ink-3)' }}> — {issue.message}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function KeyMetricsRow({ topKpis }: { topKpis: TopKpi[] }) {
  if (topKpis.length === 0) return null;
  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--ink-2)', marginBottom: 10 }}>Golden 20 — documentation coverage</div>
      <div style={{ ...card, display: 'grid', gridTemplateColumns: `repeat(${Math.min(topKpis.length, 4)}, 1fr)` }}>
      {topKpis.map((kpi, i) => (
        <Link
          key={kpi.id}
          href={`/detail/kpi/${encodeURIComponent(kpi.id)}`}
          style={{
            padding: '18px 20px',
            borderLeft: i > 0 ? '1px solid var(--line-2)' : 'none',
            display: 'flex', flexDirection: 'column', gap: 6,
            textDecoration: 'none', color: 'inherit',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{
              width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
              background: kpi.completeness >= 80 ? 'var(--success)' : kpi.completeness >= 50 ? 'var(--warning)' : 'var(--line)',
            }} />
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{kpi.name}</span>
          </div>
          <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--ink-4)' }}>{kpi.ref}</span>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 500, color: 'var(--ink)', lineHeight: 1 }}>{kpi.completeness}%</span>
          <span style={{ fontSize: 11.5, color: 'var(--ink-3)' }}>{kpi.domain || '—'} · metadata complete</span>
        </Link>
      ))}
      </div>
    </div>
  );
}

/* ── Main export ── */

export function FrameworkOverview({
  userName = 'there',
  stats,
  domains,
  topKpis,
  activity = [],
  auditSparkline = [],
  drift,
}: FrameworkOverviewProps) {
  const driftErrors = drift?.errorCount ?? 0;
  const healthLabel = driftErrors > 0 ? 'needs attention' : stats.inReview > 0 ? 'mostly healthy' : 'healthy';
  const inReviewLine = stats.inReview > 0
    ? `${stats.inReview} KPI${stats.inReview !== 1 ? 's' : ''} need review.`
    : driftErrors > 0
      ? `${driftErrors} drift error${driftErrors !== 1 ? 's' : ''} to resolve.`
      : 'No KPI definitions awaiting review.';
  const displayName = userName.charAt(0).toUpperCase() + userName.slice(1);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap)' }}>
      {/* Hero */}
      <section style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 24, paddingTop: 12 }}>
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: 0 }}>
            FRAMEWORK · v1.0.0 · main
          </div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--ink)', marginTop: 10 }}>
            ActionReady Studio
          </div>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 36, fontWeight: 500, color: 'var(--ink)',
            letterSpacing: '-0.025em',
            margin: '6px 0 4px',
          }}>
            {greeting()}, {displayName}.
          </h1>
          <div style={{ color: 'var(--ink-3)', fontSize: 14 }}>
            Your framework is <span style={{ color: 'var(--ink)' }}>{healthLabel}</span>. {inReviewLine}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link href="/canvas" style={{ ...ghostBtn, textDecoration: 'none' }}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <circle cx="8" cy="8" r="5.5" />
              <path d="M8 5v3l2 1.5" />
            </svg>
            Open Canvas
          </Link>
          <Link href="/library" style={{ ...ghostBtn, textDecoration: 'none' }}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <circle cx="4" cy="3.5" r="1.3" />
              <circle cx="4" cy="12.5" r="1.3" />
              <circle cx="12" cy="6" r="1.3" />
              <path d="M4 5v6M5.3 6c2.5 0 3.7-.4 5.4-1.4" />
            </svg>
            Open Library
          </Link>
          <Link href="/delivery" style={{ ...primaryBtn, textDecoration: 'none' }}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M8 2v3M8 11v3M2 8h3M11 8h3M4 4l2 2M10 10l2 2M12 4l-2 2M4 12l2-2" />
            </svg>
            Open Delivery
          </Link>
        </div>
      </section>

      {/* Stat grid (4 columns, matches design) */}
      <StatGrid stats={stats} />

      {/* 2-column: composition + activity */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 'var(--gap)', alignItems: 'start' }}>
        <CompositionCard stats={stats} domains={domains} />
        <ActivityFeed items={activity} />
      </div>

      {drift && (
        <NeedsAttentionCard drift={drift} auditSparkline={auditSparkline} />
      )}

      {/* Key metrics */}
      <KeyMetricsRow topKpis={topKpis} />
    </div>
  );
}

const ghostBtn: React.CSSProperties = {
  height: 32, padding: '0 12px', borderRadius: 7,
  border: '1px solid var(--line)', background: 'var(--panel)',
  fontSize: 12.5, color: 'var(--ink-2)', cursor: 'pointer',
  display: 'inline-flex', alignItems: 'center', gap: 6,
};

const primaryBtn: React.CSSProperties = {
  height: 32, padding: '0 14px', borderRadius: 7,
  background: 'var(--ink)', color: 'var(--bg)',
  fontSize: 12.5, fontWeight: 500, cursor: 'pointer',
  border: 'none',
  display: 'inline-flex', alignItems: 'center', gap: 6,
};
