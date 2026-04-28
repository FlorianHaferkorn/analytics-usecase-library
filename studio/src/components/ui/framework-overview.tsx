'use client';

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

interface DomainEntry { name: string; count: number; hue: number }
interface TopKpi { id: string; name: string; ref: string; unit: string; domain: string }

export interface FrameworkOverviewProps {
  stats: {
    kpiCount: number;
    bracketCount: number;
    actionCount: number;
    pendingReviews: number;
    certified: number;
    inReview: number;
    totalDomains: number;
  };
  domains: DomainEntry[];
  topKpis: TopKpi[];
}

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

/* ── Activity feed data ── */
const FEED = [
  { initials: 'AH', name: 'A. Haferkorn', action: 'certified',    target: 'sales.net_sales.amount', time: '2h ago',  color: 'var(--accent)' },
  { initials: 'FM', name: 'F. Müller',    action: 'drafted',      target: 'cost.opex.per_unit',     time: '5h ago',  color: 'var(--warning)' },
  { initials: 'MS', name: 'M. Schmidt',   action: 'reviewed',     target: 'margin.gross.pct',       time: '1d ago',  color: 'var(--info)' },
  { initials: 'AH', name: 'A. Haferkorn', action: 'connected',    target: 'src.crm',                time: '2d ago',  color: 'var(--accent)' },
  { initials: 'FM', name: 'F. Müller',    action: 'commented on', target: 'cac.blended',            time: '3d ago',  color: 'var(--warning)' },
];

/* ── Demo sparkline data sets ── */
const SPARK_SETS = [
  [40,42,41,45,44,48,47,50,52,55,54,58],
  [60,58,57,59,62,60,65,64,66,68,67,70],
  [30,32,31,33,35,34,36,38,37,39,41,40],
  [50,49,51,53,52,55,57,56,58,60,59,62],
];

/* ── Greeting helper ── */
function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 18) return 'Good afternoon';
  return 'Good evening';
}

/* ── Sub-sections ── */

function StatGrid({ stats }: { stats: FrameworkOverviewProps['stats'] }) {
  const items: { label: string; value: number; hint: string; trend?: string }[] = [
    { label: 'KPIs', value: stats.kpiCount, hint: `${stats.certified} certified · ${stats.inReview} in review` },
    { label: 'Brackets', value: stats.bracketCount, hint: 'Use cases' },
    { label: 'Actions', value: stats.actionCount, hint: 'Action codes' },
    { label: 'In review', value: stats.pendingReviews, hint: 'Need attention' },
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
          <div style={{ fontSize: 12, color: 'var(--ink-3)', marginTop: 2 }}>How your KPIs are distributed across domains</div>
        </div>
        <button style={ghostSmall}>View all →</button>
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
            {domains.map((d) => (
              <div key={d.name} title={`${d.name} · ${d.count}`} style={{ flex: d.count, background: `oklch(0.7 0.1 ${d.hue})` }} />
            ))}
          </div>
          {/* Domain list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {domains.map((d) => (
              <div key={d.name} style={{ display: 'grid', gridTemplateColumns: '12px 1fr auto auto', gap: 12, alignItems: 'center', fontSize: 13 }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: `oklch(0.7 0.1 ${d.hue})` }} />
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

function ActivityFeed() {
  return (
    <div style={card}>
      <div style={cardHead}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--ink)', letterSpacing: '-0.01em' }}>Recent activity</div>
          <div style={{ fontSize: 12, color: 'var(--ink-3)', marginTop: 2 }}>Across the framework</div>
        </div>
      </div>
      <div style={{ padding: '4px 0 12px' }}>
        {FEED.map((item, i) => (
          <div key={i} style={{
            display: 'flex', gap: 12, alignItems: 'flex-start',
            padding: '10px var(--pad)',
            borderTop: i === 0 ? 'none' : '1px solid var(--line-2)',
          }}>
            <div style={{
              width: 24, height: 24, borderRadius: 99, flexShrink: 0,
              background: `oklch(0.65 0.12 ${(i * 60) % 360})`, color: '#fff',
              display: 'grid', placeItems: 'center',
              fontSize: 10, fontWeight: 600,
            }}>{item.initials}</div>
            <div style={{ flex: 1, minWidth: 0, fontSize: 12.5, lineHeight: 1.5 }}>
              <span style={{ fontWeight: 500, color: 'var(--ink)' }}>{item.name}</span>
              <span style={{ color: 'var(--ink-3)' }}> {item.action} </span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)', fontSize: '0.92em' }}>{item.target}</span>
              <div style={{ color: 'var(--ink-4)', fontSize: 11.5, marginTop: 2 }}>{item.time}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function KeyMetricsRow({ topKpis }: { topKpis: TopKpi[] }) {
  if (topKpis.length === 0) return null;
  return (
    <div style={{ ...card, display: 'grid', gridTemplateColumns: `repeat(${topKpis.length}, 1fr)` }}>
      {topKpis.map((kpi, i) => (
        <div key={kpi.id} style={{
          padding: '18px 20px',
          borderLeft: i > 0 ? '1px solid var(--line-2)' : 'none',
          display: 'flex', flexDirection: 'column', gap: 6,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: i === 0 ? 'var(--success)' : 'var(--line)', flexShrink: 0 }} />
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{kpi.name}</span>
          </div>
          <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--ink-4)' }}>{kpi.ref}</span>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 500, color: 'var(--ink)', lineHeight: 1 }}>—</span>
          <Sparkline data={SPARK_SETS[i % SPARK_SETS.length] ?? [0, 1]} height={32} />
        </div>
      ))}
    </div>
  );
}

/* ── Main export ── */

export function FrameworkOverview({ stats, domains, topKpis }: FrameworkOverviewProps) {
  const inReviewLine = stats.inReview > 0
    ? `${stats.inReview} KPI${stats.inReview !== 1 ? 's' : ''} need review.`
    : 'No KPIs awaiting review.';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap)' }}>
      {/* Hero */}
      <section style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 24, paddingTop: 12 }}>
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: 0 }}>
            FRAMEWORK · v1.0.0 · main
          </div>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 36, fontWeight: 500, color: 'var(--ink)',
            letterSpacing: '-0.025em',
            margin: '6px 0 4px',
          }}>
            {greeting()}, Alex.
          </h1>
          <div style={{ color: 'var(--ink-3)', fontSize: 14 }}>
            Your framework is <span style={{ color: 'var(--ink)' }}>healthy</span>. {inReviewLine}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={ghostBtn}>History</button>
          <button style={ghostBtn}>v1.0.0</button>
          <button style={primaryBtn}>Draft with AI</button>
        </div>
      </section>

      {/* Stat grid (4 columns, matches design) */}
      <StatGrid stats={stats} />

      {/* 2-column: composition + activity */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 'var(--gap)', alignItems: 'start' }}>
        <CompositionCard stats={stats} domains={domains} />
        <ActivityFeed />
      </div>

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
