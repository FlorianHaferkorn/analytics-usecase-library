// Dashboard — framework overview
function Sparkline({ data, color = "var(--accent)", height = 32 }) {
  const max = Math.max(...data), min = Math.min(...data);
  const range = max - min || 1;
  const w = 120;
  const pts = data.map((v, i) => [(i / (data.length - 1)) * w, height - ((v - min) / range) * (height - 4) - 2]);
  const d = "M" + pts.map(p => p.join(",")).join(" L");
  const areaD = d + ` L${w},${height} L0,${height} Z`;
  return (
    <svg width={w} height={height} style={{display:"block"}}>
      <path d={areaD} fill={color} opacity="0.08" />
      <path d={d} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={pts[pts.length-1][0]} cy={pts[pts.length-1][1]} r="2.5" fill={color} />
    </svg>
  );
}

function DonutCoverage({ pct = 82 }) {
  const r = 36, c = 2 * Math.PI * r;
  return (
    <svg width="96" height="96" viewBox="0 0 96 96">
      <circle cx="48" cy="48" r={r} stroke="var(--line)" strokeWidth="6" fill="none"/>
      <circle cx="48" cy="48" r={r} stroke="var(--accent)" strokeWidth="6" fill="none"
              strokeLinecap="round" strokeDasharray={c}
              strokeDashoffset={c * (1 - pct/100)}
              transform="rotate(-90 48 48)"
              style={{ transition: "stroke-dashoffset 600ms ease" }}/>
      <text x="48" y="52" textAnchor="middle" fontFamily="var(--font-display)"
            fontSize="22" fontWeight="500" fill="var(--ink)">{pct}%</text>
    </svg>
  );
}

function DomainBar() {
  const total = FRAMEWORK.domains.reduce((a,b) => a + b.count, 0);
  return (
    <div style={{ display: "flex", height: 8, borderRadius: 99, overflow: "hidden", background: "var(--line-2)" }}>
      {FRAMEWORK.domains.map(d => (
        <div key={d.id} title={`${d.name} · ${d.count}`} style={{
          flex: d.count, background: `oklch(0.7 0.1 ${d.color})`,
        }}/>
      ))}
    </div>
  );
}

function StatCard({ label, value, hint, trend }) {
  return (
    <div style={{
      padding: "var(--pad)", background: "var(--panel)",
      border: "1px solid var(--line)", borderRadius: "var(--radius)",
      display: "flex", flexDirection: "column", gap: 8,
    }}>
      <div style={{ fontSize: 12, color: "var(--ink-3)", letterSpacing: "-0.005em" }}>{label}</div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <div className="display" style={{ fontSize: 32, fontWeight: 500, letterSpacing: "-0.02em" }}>{value}</div>
        {trend && <span style={{
          fontSize: 11.5, color: trend.startsWith("+") ? "oklch(0.52 0.14 150)" : "oklch(0.55 0.15 30)",
        }}>{trend}</span>}
      </div>
      {hint && <div style={{ fontSize: 11.5, color: "var(--ink-4)" }}>{hint}</div>}
    </div>
  );
}

function Dashboard({ onOpenDetail }) {
  const totalMetrics = FRAMEWORK.metrics.length;
  const certified = FRAMEWORK.metrics.filter(m => m.status === "certified").length;

  return (
    <div style={{ padding: "var(--pad)", display: "flex", flexDirection: "column", gap: "var(--gap)", maxWidth: 1400, margin: "0 auto", width: "100%" }}>
      {/* Hero */}
      <section style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 24, paddingTop: 12 }}>
        <div>
          <div style={{ fontSize: 12, color: "var(--ink-3)" }} className="mono">FRAMEWORK · v2.4.1 · main</div>
          <h1 className="display" style={{ fontSize: 36, margin: "6px 0 4px", letterSpacing: "-0.025em", fontWeight: 500 }}>
            Good afternoon, Alex.
          </h1>
          <div style={{ color: "var(--ink-3)", fontSize: 14 }}>
            Your framework is <span style={{color:"var(--ink)"}}>healthy</span>. 3 metrics need review and 1 draft is waiting on your input.
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button style={ghostBtn}><I.Clock size={14}/> History</button>
          <button style={ghostBtn}><I.Branch size={14}/> v2.4.1</button>
          <button style={primaryBtn}><I.Sparkle size={14} stroke={1.8}/> Draft with AI</button>
        </div>
      </section>

      {/* Stat grid */}
      <section style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "var(--gap)" }}>
        <StatCard label="Metrics" value={totalMetrics} trend="+3" hint={`${certified} certified · ${totalMetrics - certified} in review`} />
        <StatCard label="Dimensions" value={FRAMEWORK.dimensions.length} hint="Spanning 5 sources" />
        <StatCard label="Sources connected" value={FRAMEWORK.sources.length} hint="All healthy" trend="+1" />
        <StatCard label="Pending reviews" value="3" hint="Oldest 3d" trend="−2" />
      </section>

      {/* Two-column */}
      <section style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: "var(--gap)" }}>
        {/* Coverage + composition */}
        <div style={card}>
          <div style={cardHead}>
            <div>
              <div style={cardTitle}>Framework composition</div>
              <div style={cardSub}>How your metrics are distributed across domains</div>
            </div>
            <button style={ghostSmall}>View all <I.ArrowR size={12}/></button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: 32, padding: "var(--pad)", alignItems: "center" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
              <DonutCoverage pct={82}/>
              <div style={{ fontSize: 11.5, color: "var(--ink-3)", textAlign: "center" }}>
                Documentation<br/>coverage
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <DomainBar/>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {FRAMEWORK.domains.map(d => (
                  <div key={d.id} style={{ display: "grid", gridTemplateColumns: "12px 1fr auto auto", gap: 12, alignItems: "center", fontSize: 13 }}>
                    <span style={{ width: 8, height: 8, borderRadius: 2, background: `oklch(0.7 0.1 ${d.color})` }}/>
                    <span>{d.name}</span>
                    <span className="mono" style={{ color: "var(--ink-3)", fontSize: 11.5 }}>
                      {Math.round((d.count / FRAMEWORK.domains.reduce((a,b)=>a+b.count,0)) * 100)}%
                    </span>
                    <span className="mono" style={{ color: "var(--ink-4)", fontSize: 11.5, width: 28, textAlign: "right" }}>{d.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Activity */}
        <div style={card}>
          <div style={cardHead}>
            <div>
              <div style={cardTitle}>Recent activity</div>
              <div style={cardSub}>Across the framework</div>
            </div>
          </div>
          <div style={{ padding: "4px 0 12px" }}>
            {FRAMEWORK.activity.map((a, i) => (
              <div key={i} style={{
                padding: "10px var(--pad)", display: "flex", gap: 12, alignItems: "flex-start",
                borderTop: i === 0 ? "none" : "1px solid var(--line-2)",
              }}>
                <div style={{
                  width: 24, height: 24, borderRadius: 99,
                  background: `oklch(0.65 0.12 ${(i*60) % 360})`, color: "#fff",
                  display: "grid", placeItems: "center", fontSize: 10, fontWeight: 600, flexShrink: 0,
                }}>{a.who.split(/[.\s]/).map(s=>s[0]).join("")}</div>
                <div style={{ flex: 1, minWidth: 0, fontSize: 12.5, lineHeight: 1.5 }}>
                  <span style={{ fontWeight: 500 }}>{a.who}</span>
                  <span style={{ color: "var(--ink-3)" }}> {a.what} </span>
                  <span className="mono" style={{ color: "var(--accent)" }}>{a.target}</span>
                  <div style={{ color: "var(--ink-4)", fontSize: 11.5, marginTop: 2 }}>{a.when}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Top metrics */}
      <section style={card}>
        <div style={cardHead}>
          <div>
            <div style={cardTitle}>Key metrics</div>
            <div style={cardSub}>Certified metrics powering your north-star</div>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <button style={ghostSmall}><I.Filter size={12}/> Filter</button>
            <button style={ghostSmall}>Open canvas <I.ArrowR size={12}/></button>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", padding: "0 var(--pad) var(--pad)" }}>
          {[
            { m: "mrr",   v: "$4.82M", t: "+6.1%", spark: [12,14,13,15,17,18,17,20,22,21,24,26] },
            { m: "nrr",   v: "114%",   t: "+2pts", spark: [100,102,104,103,107,110,111,112,113,114,114,114] },
            { m: "dau",   v: "128k",   t: "+4.4%", spark: [80,82,85,90,88,92,94,98,105,112,120,128] },
            { m: "activation_rate", v: "41%", t: "−1pt", spark: [44,45,44,43,43,42,42,43,42,41,41,41] },
          ].map((k, i) => {
            const m = FRAMEWORK.metrics.find(x => x.id === k.m);
            return (
              <button key={i} onClick={() => onOpenDetail(m)} style={{
                textAlign: "left", padding: "16px 0",
                borderRight: i < 3 ? "1px solid var(--line-2)" : "none",
                paddingRight: 20, paddingLeft: i === 0 ? 0 : 20,
                display: "flex", flexDirection: "column", gap: 10,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <StatusDot status={m.status}/>
                  <span style={{ fontSize: 12.5, fontWeight: 500 }}>{m.name}</span>
                </div>
                <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-4)" }}>{m.ref}</div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                  <div className="display" style={{ fontSize: 24, fontWeight: 500 }}>{k.v}</div>
                  <span style={{ fontSize: 11.5, color: k.t.startsWith("+") ? "oklch(0.52 0.14 150)" : "oklch(0.55 0.15 30)" }}>{k.t}</span>
                </div>
                <Sparkline data={k.spark} color={k.t.startsWith("+") ? "var(--accent)" : "oklch(0.6 0.14 30)"}/>
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );
}

const card = {
  background: "var(--panel)",
  border: "1px solid var(--line)",
  borderRadius: "var(--radius)",
  overflow: "hidden",
};
const cardHead = {
  padding: "18px var(--pad)",
  borderBottom: "1px solid var(--line-2)",
  display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12,
};
const cardTitle = { fontSize: 14, fontWeight: 500, letterSpacing: "-0.01em" };
const cardSub = { fontSize: 12, color: "var(--ink-3)", marginTop: 2 };

const ghostBtn = {
  height: 32, padding: "0 12px", borderRadius: 7,
  border: "1px solid var(--line)", background: "var(--panel)",
  fontSize: 12.5, color: "var(--ink-2)",
  display: "inline-flex", alignItems: "center", gap: 6,
};
const primaryBtn = {
  height: 32, padding: "0 14px", borderRadius: 7,
  background: "var(--ink)", color: "var(--bg)",
  fontSize: 12.5, fontWeight: 500,
  display: "inline-flex", alignItems: "center", gap: 6,
};
const ghostSmall = {
  height: 26, padding: "0 10px", borderRadius: 6,
  fontSize: 12, color: "var(--ink-2)",
  display: "inline-flex", alignItems: "center", gap: 5,
};

Object.assign(window, { Dashboard, Sparkline, StatCard, card, cardHead, cardTitle, cardSub, ghostBtn, primaryBtn, ghostSmall });
