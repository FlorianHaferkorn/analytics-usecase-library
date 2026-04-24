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
  const items = [
    { label: 'KPIs', value: stats.kpiCount, hint: `${stats.certified} certified` },
    { label: 'Brackets', value: stats.bracketCount, hint: 'use cases' },
    { label: 'Actions', value: stats.actionCount, hint: 'action codes' },
    { label: 'In Review', value: stats.pendingReviews, hint: 'need attention' },
  ];
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
      {items.map((item) => (
        <div key={item.label} style={{ ...card, padding: '16px 20px' }}>
          <p style={{ fontSize: 11, color: 'var(--ink-4)', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 6 }}>{item.label}</p>
          <p style={{ fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 500, color: 'var(--ink)', lineHeight: 1 }}>{item.value}</p>
          <p style={{ fontSize: 11, color: 'var(--ink-4)', marginTop: 4 }}>{item.hint}</p>
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
        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--ink)' }}>Framework composition</span>
        <button style={{ fontSize: 12, color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>View all →</button>
      </div>
      <div style={{ padding: '20px var(--pad)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 20 }}>
          <DonutChart pct={certPct} />
          <div>
            <p style={{ fontSize: 13, fontWeight: 500, color: 'var(--ink)', marginBottom: 2 }}>Certified</p>
            <p style={{ fontSize: 12, color: 'var(--ink-3)' }}>{stats.certified} of {stats.kpiCount} KPIs</p>
            <p style={{ fontSize: 11, color: 'var(--ink-4)', marginTop: 6 }}>{stats.inReview} in review</p>
          </div>
        </div>
        {/* Domain bar */}
        <div style={{ display: 'flex', height: 8, borderRadius: 999, overflow: 'hidden', gap: 2, marginBottom: 14 }}>
          {domains.map((d) => (
            <div key={d.name} style={{ flex: d.count / total, background: `hsl(${d.hue} 60% 55%)`, minWidth: 4 }} />
          ))}
        </div>
        {/* Domain list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {domains.map((d) => (
            <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: `hsl(${d.hue} 60% 55%)`, flexShrink: 0 }} />
              <span style={{ fontSize: 12, color: 'var(--ink-2)', flex: 1, textTransform: 'capitalize' }}>{d.name}</span>
              <span style={{ fontSize: 11, color: 'var(--ink-4)' }}>{Math.round((d.count / total) * 100)}%</span>
              <span style={{ fontSize: 11, color: 'var(--ink-4)', minWidth: 24, textAlign: 'right' }}>{d.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ActivityFeed() {
  return (
    <div style={card}>
      <div style={cardHead}>
        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--ink)' }}>Recent activity</span>
      </div>
      <div style={{ padding: '8px 0' }}>
        {FEED.map((item, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px var(--pad)' }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
              background: item.color, color: 'var(--accent-ink)',
              display: 'grid', placeItems: 'center',
              fontSize: 10, fontWeight: 700,
            }}>{item.initials}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--ink)' }}>{item.name}</span>
              {' '}
              <span style={{ fontSize: 12, color: 'var(--ink-3)' }}>{item.action}</span>
              {' '}
              <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--accent)', wordBreak: 'break-all' }}>{item.target}</span>
            </div>
            <span style={{ fontSize: 11, color: 'var(--ink-4)', flexShrink: 0, whiteSpace: 'nowrap' }}>{item.time}</span>
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
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap)' }}>
      {/* Hero */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, color: 'var(--ink)', letterSpacing: '-0.02em', marginBottom: 4 }}>
            {greeting()}, Aurora Group
          </h1>
          <p style={{ fontSize: 13, color: 'var(--ink-3)' }}>
            Your framework is healthy.{stats.inReview > 0 && ` ${stats.inReview} KPI${stats.inReview !== 1 ? 's' : ''} need review.`}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button style={{
            height: 32, padding: '0 14px', borderRadius: 7,
            border: '1px solid var(--line)', background: 'var(--panel)',
            fontSize: 13, color: 'var(--ink-2)', cursor: 'pointer',
          }}>
            History
          </button>
          <button style={{
            height: 32, padding: '0 14px', borderRadius: 7,
            background: 'var(--accent)', border: 'none',
            color: 'var(--accent-ink)', fontSize: 13, fontWeight: 500, cursor: 'pointer',
            display: 'inline-flex', alignItems: 'center', gap: 6,
          }}>
            ✦ Draft with AI →
          </button>
        </div>
      </div>

      {/* Stat grid */}
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
