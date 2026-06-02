// Use Cases — T1-T4 Tier system, the actual deliverable artifacts
const { useState: useStateUC, useMemo: useMemoUC } = React;

// ───────── Tier semantics ─────────
const TIERS = {
  T1: { label: "Strategic Overview",      tag: "T1", time: "3s",   color: "250", desc: "Are we on track?",                  audience: "Board · ExCo" },
  T2: { label: "Tactical Variance",        tag: "T2", time: "30s",  color: "30",  desc: "Why are we off?",                   audience: "Leadership" },
  T3: { label: "Operational Monitoring",   tag: "T3", time: "5min", color: "190", desc: "What's breaking now?",              audience: "Ops Teams" },
  T4: { label: "Prescriptive Recommendation", tag: "T4", time: "30min", color: "150", desc: "What should we do, and where?", audience: "Owners" },
};

// ───────── Tier badge ─────────
function TierBadge({ tier, large }) {
  const t = TIERS[tier];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: large ? "4px 10px" : "2px 8px",
      borderRadius: 6,
      fontFamily: "var(--font-mono)",
      fontSize: large ? 11 : 10,
      fontWeight: 600, letterSpacing: "0.04em",
      background: `oklch(0.7 0.1 ${t.color} / 0.14)`,
      color: `oklch(0.45 0.13 ${t.color})`,
      border: `1px solid oklch(0.7 0.1 ${t.color} / 0.3)`,
    }}>
      {t.tag} · {t.time}
    </span>
  );
}

// ───────── Mini chart primitives ─────────
function MiniLine({ data, color = "var(--accent)", refLine, height = 80 }) {
  const max = Math.max(...data.flat(), refLine ?? -Infinity);
  const min = Math.min(...data.flat(), refLine ?? Infinity);
  const range = (max - min) || 1;
  const W = 280;
  const series = Array.isArray(data[0]) ? data : [data];
  const colors = [color, "var(--ink-4)"];
  const yFor = v => height - ((v - min) / range) * (height - 8) - 4;
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${height}`} preserveAspectRatio="none" style={{ display: "block" }}>
      {refLine != null && (
        <g>
          <line x1="0" x2={W} y1={yFor(refLine)} y2={yFor(refLine)}
                stroke="var(--ink-4)" strokeDasharray="3 3" strokeWidth="1" opacity="0.5"/>
          <text x={W-2} y={yFor(refLine)-3} textAnchor="end" fontSize="9" fill="var(--ink-4)" fontFamily="var(--font-mono)">Plan</text>
        </g>
      )}
      {series.map((s, si) => {
        const pts = s.map((v, i) => [(i / (s.length - 1)) * W, yFor(v)]);
        const d = "M" + pts.map(p => p.join(",")).join(" L");
        return <path key={si} d={d} fill="none" stroke={colors[si]} strokeWidth={si===0?1.6:1} strokeLinejoin="round" strokeLinecap="round" opacity={si===0?1:0.5}/>;
      })}
    </svg>
  );
}

function MiniWaterfall({ bars }) {
  const W = 280, H = 90;
  let cum = 0;
  const positions = bars.map(b => {
    if (b.type === "start" || b.type === "end") {
      const start = 0;
      const v = b.value;
      cum = b.type === "end" ? cum : v;
      return { ...b, start, top: v };
    }
    const start = cum;
    cum += b.value;
    return { ...b, start, top: cum };
  });
  const all = positions.flatMap(p => [p.start, p.top, p.value]);
  const max = Math.max(...all, 0);
  const min = Math.min(...all, 0);
  const range = (max - min) || 1;
  const yFor = v => H - ((v - min) / range) * (H - 16) - 8;
  const bw = (W - bars.length * 4) / bars.length;
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H+18}`} preserveAspectRatio="none" style={{ display: "block" }}>
      {positions.map((p, i) => {
        const x = i * (bw + 4);
        const isAnchor = p.type === "start" || p.type === "end";
        const y0 = isAnchor ? yFor(0) : yFor(p.start);
        const y1 = isAnchor ? yFor(p.top) : yFor(p.top);
        const top = Math.min(y0, y1), bot = Math.max(y0, y1);
        const fill = isAnchor ? "var(--ink)" : (p.value >= 0 ? "oklch(0.6 0.13 150)" : "oklch(0.6 0.15 30)");
        return (
          <g key={i}>
            <rect x={x} y={top} width={bw} height={Math.max(2, bot-top)} fill={fill} rx="1"/>
            <text x={x + bw/2} y={H+10} textAnchor="middle" fontSize="9" fill="var(--ink-3)" fontFamily="var(--font-mono)">{p.label}</text>
          </g>
        );
      })}
    </svg>
  );
}

function MiniHBar({ rows, max }) {
  const m = max || Math.max(...rows.map(r => Math.abs(r.value)));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {rows.map((r, i) => {
        const w = (Math.abs(r.value) / m) * 100;
        const neg = r.value < 0;
        const color = r.color || (neg ? "oklch(0.6 0.15 30)" : "oklch(0.55 0.12 150)");
        return (
          <div key={i} style={{ display: "grid", gridTemplateColumns: "60px 1fr 50px", alignItems: "center", gap: 8, fontSize: 10.5 }}>
            <span style={{ color: "var(--ink-2)" }}>{r.label}</span>
            <div style={{ position: "relative", height: 10, background: "var(--bg-2)", borderRadius: 2 }}>
              <div style={{ position: neg ? "absolute" : "static", right: neg ? "50%" : "auto", left: neg ? "auto" : "50%", marginLeft: neg ? 0 : 0,
                            width: `${w/2}%`, height: "100%", background: color, borderRadius: 2 }}/>
              <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: 1, background: "var(--line)" }}/>
            </div>
            <span className="mono" style={{ color: "var(--ink-3)", textAlign: "right", fontSize: 10 }}>{r.value > 0 ? "+" : ""}{r.value.toFixed(1)}</span>
          </div>
        );
      })}
    </div>
  );
}

function MiniStack100({ rows }) {
  const colors = ["oklch(0.55 0.12 250)", "oklch(0.7 0.12 30)", "oklch(0.65 0.12 150)"];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {rows.map((r, i) => (
        <div key={i} style={{ display: "grid", gridTemplateColumns: "60px 1fr", alignItems: "center", gap: 8, fontSize: 10.5 }}>
          <span style={{ color: "var(--ink-2)" }}>{r.label}</span>
          <div style={{ display: "flex", height: 14, borderRadius: 2, overflow: "hidden", border: "0.5px solid var(--line)" }}>
            {r.values.map((v, vi) => (
              <div key={vi} style={{ flex: v, background: colors[vi], display: "grid", placeItems: "center", color: "white", fontSize: 9 }} className="mono">
                {v > 12 ? `${v}` : ""}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ───────── KPI tile ─────────
function KpiTile({ label, value, delta, deltaDir, period, polarity }) {
  const goodDir = polarity === "lower_is_better" ? "down" : "up";
  const isGood = deltaDir === goodDir;
  const color = isGood ? "oklch(0.55 0.13 150)" : "oklch(0.55 0.16 30)";
  return (
    <div style={{ flex: 1, padding: "10px 12px", background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 6, minWidth: 0 }}>
      <div style={{ fontSize: 10, color: "var(--ink-3)", textTransform: "uppercase", letterSpacing: "0.05em", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{label}</div>
      <div className="display" style={{ fontSize: 22, fontWeight: 500, marginTop: 2, letterSpacing: "-0.02em" }}>{value}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2, fontSize: 10.5 }}>
        <span style={{ color, fontWeight: 500 }}>{deltaDir === "up" ? "▲" : "▼"} {delta}</span>
        <span style={{ color: "var(--ink-4)" }}>{period}</span>
      </div>
    </div>
  );
}

// ───────── Chart card ─────────
function ChartCard({ q, children }) {
  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 6, padding: 12, display: "flex", flexDirection: "column", gap: 10, minWidth: 0 }}>
      <div style={{ fontSize: 11, fontWeight: 500, color: "var(--ink-2)", lineHeight: 1.35 }}>{q}</div>
      <div style={{ flex: 1 }}>{children}</div>
    </div>
  );
}

function SignalRow({ tier, title, body, dest }) {
  const tone = tier === "T1" ? "oklch(0.55 0.14 75)" : tier === "T2" ? "oklch(0.55 0.16 30)" : "oklch(0.55 0.13 250)";
  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderLeft: `2px solid ${tone}`, borderRadius: 4, padding: "8px 12px", display: "flex", alignItems: "center", gap: 12 }}>
      <span style={{ fontSize: 9, fontWeight: 700, color: tone, letterSpacing: "0.05em", textTransform: "uppercase", whiteSpace: "nowrap" }}>
        {tier === "T1" ? "Strategic Signal" : tier === "T2" ? "Tactical Signal" : "Signal"}
      </span>
      <div style={{ flex: 1, fontSize: 11, lineHeight: 1.4 }}>
        <strong>{title}</strong> <span style={{ color: "var(--ink-3)" }}>{body}</span>
      </div>
      {dest && <span className="mono" style={{ fontSize: 9, color: "var(--ink-4)" }}>→ {dest}</span>}
    </div>
  );
}

// ───────── Tier renderers ─────────
function PulseFrame({ uc, children }) {
  return (
    <div style={{
      background: "var(--bg-2)", border: "1px solid var(--line)", borderRadius: 8,
      padding: 14, display: "flex", flexDirection: "column", gap: 10,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span className="mono" style={{ fontSize: 9.5, color: "var(--ink-4)", letterSpacing: "0.06em" }}>
          {uc.bracket} · {uc.domain.toUpperCase()} · OVERVIEW
        </span>
        <div style={{ flex: 1 }}/>
        <TierBadge tier={uc.tier}/>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
        <h2 className="display" style={{ fontSize: 18, fontWeight: 500, margin: 0, letterSpacing: "-0.015em" }}>{uc.title}</h2>
      </div>
      <div style={{ fontSize: 11, color: "var(--ink-3)", fontStyle: "italic", marginTop: -4 }}>
        Decision: <span style={{ color: "var(--ink-2)", fontStyle: "normal" }}>{uc.question}</span>
      </div>
      {children}
    </div>
  );
}

function T1Render({ uc }) {
  const kpis = [
    { label: "Net Sales YTD",  value: "€42.3M", delta: "8.2%", deltaDir: "down", period: "vs Plan" },
    { label: "Gross Margin %", value: "38.4%",  delta: "1.2pp", deltaDir: "down", period: "vs PY" },
    { label: "OTIF %",         value: "94.1%",  delta: "0.8pp", deltaDir: "up",   period: "vs Plan" },
    { label: "NPS",            value: "52",     delta: "4",     deltaDir: "up",   period: "vs Q-1" },
    { label: "CLV",            value: "€18.4K", delta: "2.1%",  deltaDir: "up",   period: "vs PY" },
  ];
  return (
    <PulseFrame uc={uc}>
      <div style={{ display: "flex", gap: 6 }}>{kpis.map((k, i) => <KpiTile key={i} {...k}/>)}</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
        <ChartCard q="How has Net Sales developed vs Plan over 12mo?">
          <MiniLine data={[[42,43.5,45,44,43,42.5,42,41.5,42,42.8,43,42.3], [40,41,42,42.5,43,43.5,43.8,44,44,44.2,44.3,44.5]]} refLine={45}/>
        </ChartCard>
        <ChartCard q="Which strategic units are on and off track?">
          <MiniHBar rows={[
            { label: "DACH",    value: -3.1 },
            { label: "Nordics", value: -0.9 },
            { label: "Benelux", value: -0.5 },
            { label: "Iberia",  value:  0.3 },
            { label: "UK & I",  value:  0.6 },
            { label: "CEE",     value:  0.8 },
          ]}/>
        </ChartCard>
        <ChartCard q="How is revenue distributed across the portfolio?">
          <MiniStack100 rows={[
            { label: "FY2024",  values: [52,32,16] },
            { label: "FY2025",  values: [48,34,18] },
            { label: "YTD2026", values: [45,35,20] },
          ]}/>
        </ChartCard>
      </div>
      <SignalRow tier="T1" title="DACH region requires strategic review."
        body="Net Sales -€3.1M vs Plan YTD; consistent with 3-month downward trend. Escalate to T2 for driver analysis."
        dest="T2 TACTICAL"/>
    </PulseFrame>
  );
}

function T2Render({ uc }) {
  const kpis = [
    { label: "Net Sales YTD", value: "€42.3M", delta: "€4.2M", deltaDir: "down", period: "vs Plan" },
    { label: "Volume",        value: "182K u", delta: "6.4%",  deltaDir: "down", period: "vs Plan" },
    { label: "ASP",           value: "€232",   delta: "1.8%",  deltaDir: "down", period: "vs PY" },
    { label: "Promo Depth",   value: "14.2%",  delta: "2.1pp", deltaDir: "up",   period: "vs Plan", polarity: "lower_is_better" },
  ];
  return (
    <PulseFrame uc={uc}>
      <div style={{ display: "flex", gap: 6 }}>{kpis.map((k, i) => <KpiTile key={i} {...k}/>)}</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
        <ChartCard q="When did the gap begin? Net Sales vs Plan, 12mo.">
          <MiniLine data={[45,45.2,45,44.3,43,42,41.5,41,41.8,42.3,42.5,42.3]} refLine={45}/>
        </ChartCard>
        <ChartCard q="Which factors explain the −€4.2M gap vs Plan?">
          <MiniWaterfall bars={[
            { label: "Plan",   value: 46.5, type: "start" },
            { label: "Vol",    value: -3.1 },
            { label: "Price",  value: -0.8 },
            { label: "Mix",    value: -0.5 },
            { label: "FX",     value:  0.2 },
            { label: "Actual", value: 42.3, type: "end" },
          ]}/>
        </ChartCard>
        <ChartCard q="Which regions drive the largest deviation?">
          <MiniHBar rows={[
            { label: "DACH",    value: -3.1 },
            { label: "Nordics", value: -0.9 },
            { label: "Benelux", value: -0.5 },
            { label: "Iberia",  value:  0.3 },
            { label: "UK & I",  value:  0.6 },
          ]}/>
        </ChartCard>
      </div>
      <SignalRow tier="T2" title="Volume decline in DACH is the dominant driver (−€3.1M, 74% of gap)."
        body="Price effect secondary (−€0.8M). Promotional depth up 2.1pp — validate pricing levers."
        dest="T4 RECOMMEND"/>
    </PulseFrame>
  );
}

function T3Render({ uc }) {
  const kpis = [
    { label: "Open Exceptions",  value: "14",    delta: "3",   deltaDir: "up",   period: "vs yday", polarity: "lower_is_better" },
    { label: "Critical",         value: "3",     delta: "1",   deltaDir: "up",   period: "vs yday", polarity: "lower_is_better" },
    { label: "OTIF (7d)",        value: "91.4%", delta: "2.6pp", deltaDir: "down", period: "vs SLA" },
    { label: "Avg Age (open)",   value: "4.2d",  delta: "0.8d", deltaDir: "up",   period: "vs target", polarity: "lower_is_better" },
  ];
  const exceptions = [
    { e: "SO-24891 · Müller AG",    sev: "critical", m: "OTIF",     a: "0%",   t: "≥95%", o: "CS · DACH",   age: "4d" },
    { e: "SO-24903 · Volta BV",     sev: "critical", m: "Lead Time",a: "11d",  t: "≤7d",  o: "Ops · BNX",   age: "3d" },
    { e: "SO-24867 · Siemens",      sev: "critical", m: "Fill Rate",a: "62%",  t: "≥90%", o: "SCM · DACH",  age: "6d" },
    { e: "SO-24912 · Philips",      sev: "warning",  m: "OTIF",     a: "88%",  t: "≥95%", o: "CS · BNX",    age: "2d" },
    { e: "SO-24920 · Bosch",        sev: "warning",  m: "Fill Rate",a: "84%",  t: "≥90%", o: "SCM · DACH",  age: "1d" },
  ];
  const sevColor = { critical: "oklch(0.55 0.16 25)", warning: "oklch(0.55 0.14 70)", info: "var(--ink-3)" };
  return (
    <PulseFrame uc={uc}>
      <div style={{ display: "flex", gap: 6 }}>{kpis.map((k, i) => <KpiTile key={i} {...k}/>)}</div>
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 10 }}>
        <ChartCard q="Which shipments are above the overdue threshold?">
          <div style={{ overflow: "auto", marginTop: -2 }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 10.5 }}>
              <thead>
                <tr>{["Sev","Entity","Metric","Actual","Threshold","Owner","Age"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "4px 6px", fontWeight: 500, fontSize: 9.5, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.04em", borderBottom: "1px solid var(--line)" }}>{h}</th>
                ))}</tr>
              </thead>
              <tbody>
                {exceptions.map((r, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid var(--line-2)" }}>
                    <td style={{ padding: "5px 6px" }}>
                      <span style={{ width: 7, height: 7, display: "inline-block", borderRadius: 99, background: sevColor[r.sev] }}/>
                    </td>
                    <td style={{ padding: "5px 6px", fontWeight: 500 }}>{r.e}</td>
                    <td style={{ padding: "5px 6px", color: "var(--ink-3)" }}>{r.m}</td>
                    <td className="mono" style={{ padding: "5px 6px", color: sevColor[r.sev], fontWeight: 600 }}>{r.a}</td>
                    <td className="mono" style={{ padding: "5px 6px", color: "var(--ink-4)" }}>{r.t}</td>
                    <td style={{ padding: "5px 6px", color: "var(--ink-3)" }}>{r.o}</td>
                    <td className="mono" style={{ padding: "5px 6px", color: "var(--ink-3)" }}>{r.age}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ChartCard>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <ChartCard q="Are exceptions increasing? Last 30d.">
            <MiniLine data={[[1,2,1,2,2,2,3], [5,4,6,5,7,8,11]]} color="oklch(0.55 0.16 25)"/>
          </ChartCard>
          <ChartCard q="Which owner team has the most criticals?">
            <MiniHBar rows={[
              { label: "SCM DACH", value: 4, color: "oklch(0.55 0.16 25)" },
              { label: "CS DACH",  value: 3, color: "oklch(0.55 0.16 25)" },
              { label: "Ops BNX",  value: 2, color: "oklch(0.55 0.14 70)" },
              { label: "CS BNX",   value: 2, color: "oklch(0.55 0.14 70)" },
            ]}/>
          </ChartCard>
        </div>
      </div>
    </PulseFrame>
  );
}

function T4Render({ uc }) {
  const rows = [
    { entity: "Müller Industrie AG", seg: "Core",   rev: "€4.2M", gm: "11.3%", promo: "22.4%", delta: -3.7, action: "C-M1.1", crit: true },
    { entity: "Siemens Mobility",    seg: "Core",   rev: "€3.8M", gm: "13.1%", promo: "19.8%", delta: -2.9, action: "C-M1.1", crit: true },
    { entity: "Bosch GmbH",          seg: "Core",   rev: "€2.9M", gm: "14.8%", promo: "18.2%", delta: -1.2, action: "C-M1.2" },
    { entity: "Volta BV",            seg: "Growth", rev: "€1.8M", gm: "15.2%", promo: "17.1%", delta: -0.8, action: "C-M1.2" },
    { entity: "Atlas Copco",         seg: "Growth", rev: "€1.6M", gm: "16.3%", promo: "15.9%", delta: -0.3, action: "C-M1.2" },
    { entity: "Nordex Energy",       seg: "Core",   rev: "€1.4M", gm: "17.1%", promo: "14.8%", delta:  0.1, action: null },
    { entity: "Continental AG",      seg: "Core",   rev: "€1.2M", gm: "18.4%", promo: "13.2%", delta:  0.4, action: null },
    { entity: "Hella KGaA",          seg: "Growth", rev: "€0.9M", gm: "19.1%", promo: "12.4%", delta:  1.1, action: null },
  ];
  const maxAbs = Math.max(...rows.map(r => Math.abs(r.delta)));
  return (
    <PulseFrame uc={uc}>
      <div style={{ display: "grid", gridTemplateColumns: "150px 1fr 220px", gap: 10 }}>
        {/* Slicer pane */}
        <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 6, padding: 10, fontSize: 10.5, display: "flex", flexDirection: "column", gap: 10 }}>
          {[
            { label: "Period",  items: ["YTD 2026","Last Q","Last M"], active: ["YTD 2026"] },
            { label: "Region",  items: ["DACH","Nordics","Benelux"],   active: ["DACH"] },
            { label: "Segment", items: ["Core","Growth","Emerging"],   active: ["Core","Growth"] },
            { label: "Priority",items: ["High","Medium","Low"],        active: ["High","Medium"] },
          ].map((g, i) => (
            <div key={i}>
              <div style={{ fontSize: 9.5, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>{g.label}</div>
              {g.items.map(it => (
                <div key={it} style={{ display: "flex", alignItems: "center", gap: 6, padding: "2px 0" }}>
                  <span style={{ width: 10, height: 10, borderRadius: 2, border: "1px solid var(--line)", background: g.active.includes(it) ? "var(--accent)" : "var(--bg)" }}/>
                  <span style={{ color: g.active.includes(it) ? "var(--ink)" : "var(--ink-3)" }}>{it}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
        {/* Center matrix */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderLeft: "2px solid var(--accent)", borderRadius: 4, padding: "8px 12px", fontSize: 11, lineHeight: 1.45 }}>
            <strong>GM% in DACH below 18% threshold for 3 consecutive months.</strong>{" "}
            <span style={{ color: "var(--ink-3)" }}>Promo depth +2.1pp YoY; 6 accounts account for 72% of the margin gap. Recommended: reduce promo depth by 15% — expected recovery of +0.8pp GM% by EOM.</span>
          </div>
          <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 6, overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 10.5 }}>
              <thead>
                <tr>{["Account","Seg","Rev YTD","GM%","Promo","GM% vs Thr.","Action"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "6px 8px", fontWeight: 500, fontSize: 9.5, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.04em", borderBottom: "1px solid var(--line)" }}>{h}</th>
                ))}</tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid var(--line-2)", background: r.crit ? "oklch(0.95 0.04 25 / 0.5)" : "transparent" }}>
                    <td style={{ padding: "5px 8px", fontWeight: 500 }}>{r.entity}</td>
                    <td style={{ padding: "5px 8px", color: "var(--ink-3)" }}>{r.seg}</td>
                    <td className="mono" style={{ padding: "5px 8px", textAlign: "left" }}>{r.rev}</td>
                    <td className="mono" style={{ padding: "5px 8px" }}>{r.gm}</td>
                    <td className="mono" style={{ padding: "5px 8px", color: "var(--ink-3)" }}>{r.promo}</td>
                    <td style={{ padding: "5px 8px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <div style={{ position: "relative", flex: 1, height: 10, background: "var(--bg-2)", borderRadius: 2 }}>
                          <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: 1, background: "var(--line)" }}/>
                          <div style={{
                            position: "absolute",
                            left: r.delta < 0 ? `${50 - (Math.abs(r.delta)/maxAbs)*50}%` : "50%",
                            width: `${(Math.abs(r.delta)/maxAbs)*50}%`,
                            top: 1, bottom: 1, borderRadius: 1,
                            background: r.delta < 0 ? "oklch(0.6 0.15 30)" : "oklch(0.55 0.12 150)",
                          }}/>
                        </div>
                        <span className="mono" style={{ fontSize: 10, color: r.delta < 0 ? "oklch(0.5 0.15 30)" : "oklch(0.45 0.12 150)", width: 40, textAlign: "right" }}>
                          {r.delta > 0 ? "+" : ""}{r.delta.toFixed(1)}pp
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: "5px 8px" }}>
                      {r.action && (
                        <span className="mono" style={{ fontSize: 9, color: "var(--accent)", background: "var(--accent-soft)", padding: "1px 5px", borderRadius: 2, fontWeight: 600 }}>
                          {r.action}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        {/* Action panel */}
        <div style={{ background: "var(--panel)", border: "1px solid var(--accent)", borderRadius: 6, padding: 12, display: "flex", flexDirection: "column", gap: 8, fontSize: 10.5 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="mono" style={{ fontSize: 9, fontWeight: 700, color: "var(--accent)", letterSpacing: "0.05em" }}>ACTION · C-M1.1</span>
          </div>
          <div style={{ fontSize: 12, fontWeight: 500, lineHeight: 1.35 }}>Reduce promo depth by 15% in DACH Core accounts</div>
          <div style={{ color: "var(--ink-3)", lineHeight: 1.45 }}>GM% &lt; 18% for 3 months; 2 accounts (Müller, Siemens) explain 58% of gap.</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 3, marginTop: 4 }}>
            {["Cap discount at 18% for Q-end","Review mix with CM","Alert buyer in SAP CRM","Reforecast GM% weekly"].map((s, i) => (
              <div key={i} style={{ display: "flex", gap: 6, alignItems: "flex-start" }}>
                <span className="mono" style={{ fontSize: 9, color: "var(--ink-4)", marginTop: 1 }}>{i+1}.</span>
                <span style={{ flex: 1 }}>{s}</span>
              </div>
            ))}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginTop: 6, paddingTop: 8, borderTop: "1px solid var(--line-2)" }}>
            <div><div style={{ fontSize: 9, color: "var(--ink-4)", textTransform: "uppercase" }}>Owner</div><div style={{ fontWeight: 500 }}>CM DACH</div></div>
            <div><div style={{ fontSize: 9, color: "var(--ink-4)", textTransform: "uppercase" }}>Due</div><div style={{ fontWeight: 500 }}>End of month</div></div>
            <div><div style={{ fontSize: 9, color: "var(--ink-4)", textTransform: "uppercase" }}>Impact</div><div style={{ fontWeight: 600, color: "oklch(0.5 0.13 150)" }}>+€1.2M</div></div>
            <div><div style={{ fontSize: 9, color: "var(--ink-4)", textTransform: "uppercase" }}>Priority</div><div style={{ fontWeight: 500 }}>High</div></div>
          </div>
        </div>
      </div>
    </PulseFrame>
  );
}

const TIER_RENDERER = { T1: T1Render, T2: T2Render, T3: T3Render, T4: T4Render };

// ───────── Catalog (list view) ─────────
function UseCases({ open }) {
  const [tier, setTier] = useStateUC("all");
  const [bracket, setBracket] = useStateUC("all");
  const [view, setView] = useStateUC("grid");
  const [selected, setSelected] = useStateUC(null);
  const [q, setQ] = useStateUC("");

  const filtered = useMemoUC(() => USE_CASES.filter(uc => {
    if (tier !== "all" && uc.tier !== tier) return false;
    if (bracket !== "all" && uc.bracket !== bracket) return false;
    if (q && !(`${uc.title} ${uc.id} ${uc.question}`).toLowerCase().includes(q.toLowerCase())) return false;
    return true;
  }), [tier, bracket, q]);

  if (selected) return <UseCaseDetail uc={selected} onBack={() => setSelected(null)} onOpen={open}/>;

  return (
    <div style={{ padding: "var(--pad)", maxWidth: 1500, margin: "0 auto", width: "100%" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 4 }}>
        <div>
          <div style={{ fontSize: 12, color: "var(--ink-3)" }} className="mono">USE CASE LIBRARY · 9 ACTIVE · 2 DRAFT</div>
          <h1 className="display" style={{ fontSize: 32, margin: "6px 0 4px", letterSpacing: "-0.025em", fontWeight: 500 }}>
            Use Cases
          </h1>
          <div style={{ color: "var(--ink-3)", fontSize: 13.5 }}>
            Each use case is a tiered answer to one decision question. Build them once, ship as Pulse layouts.
          </div>
        </div>
        <button style={primaryBtn}><I.Plus size={14}/> New use case</button>
      </div>

      {/* Decision-time hierarchy strip */}
      <div style={{ marginTop: 24, marginBottom: 22, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
        {Object.entries(TIERS).map(([t, info]) => {
          const count = USE_CASES.filter(u => u.tier === t).length;
          const active = tier === t;
          return (
            <button key={t} onClick={() => setTier(active ? "all" : t)} style={{
              textAlign: "left", padding: 14, borderRadius: 10,
              background: "var(--panel)",
              border: `1px solid ${active ? "var(--accent)" : "var(--line)"}`,
              boxShadow: active ? "0 0 0 3px var(--accent-soft)" : "var(--shadow-sm)",
              transition: "all 160ms",
              display: "flex", flexDirection: "column", gap: 8, position: "relative", overflow: "hidden",
            }}>
              <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 3, background: `oklch(0.7 0.1 ${info.color})` }}/>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span className="mono" style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.06em", color: `oklch(0.45 0.13 ${info.color})` }}>
                  {info.tag} · {info.time}
                </span>
                <span className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>{count}</span>
              </div>
              <div className="display" style={{ fontSize: 16, fontWeight: 500, letterSpacing: "-0.01em" }}>{info.label}</div>
              <div style={{ fontSize: 11.5, color: "var(--ink-3)" }}>{info.desc}</div>
              <div style={{ fontSize: 10.5, color: "var(--ink-4)", marginTop: 2 }}>{info.audience}</div>
            </button>
          );
        })}
      </div>

      {/* Bracket chips */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14, flexWrap: "wrap" }}>
        <span style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em", marginRight: 4 }}>Bracket</span>
        {[{ id: "all", label: "All", count: USE_CASES.length }, ...BRACKETS].map(b => {
          const active = bracket === b.id;
          return (
            <button key={b.id} onClick={() => setBracket(b.id)} style={{
              padding: "5px 10px", borderRadius: 99, fontSize: 11.5,
              border: `1px solid ${active ? "var(--ink)" : "var(--line)"}`,
              background: active ? "var(--ink)" : "var(--panel)",
              color: active ? "var(--bg)" : "var(--ink-2)",
              fontWeight: active ? 500 : 400,
              display: "inline-flex", alignItems: "center", gap: 6,
            }}>
              {b.color && <span style={{ width: 6, height: 6, borderRadius: 99, background: `oklch(0.7 0.1 ${b.color})` }}/>}
              {b.label}
              <span className="mono" style={{ fontSize: 10, opacity: 0.7 }}>{b.count}</span>
            </button>
          );
        })}
        <div style={{ flex: 1 }}/>
        <div style={{ height: 30, padding: "0 10px", display: "flex", alignItems: "center", gap: 8, border: "1px solid var(--line)", borderRadius: 7, background: "var(--panel)", width: 240 }}>
          <I.Search size={12}/>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search use cases…" style={{ flex: 1, border: 0, outline: 0, background: "transparent", fontSize: 12.5 }}/>
        </div>
        <div style={{ display: "flex", border: "1px solid var(--line)", borderRadius: 7, overflow: "hidden", height: 30 }}>
          {[["grid", "Grid"], ["list", "List"]].map(([id, l]) => (
            <button key={id} onClick={() => setView(id)} style={{
              padding: "0 12px", fontSize: 12, color: view === id ? "var(--ink)" : "var(--ink-3)",
              background: view === id ? "var(--hover)" : "transparent", fontWeight: view === id ? 500 : 400,
            }}>{l}</button>
          ))}
        </div>
      </div>

      {/* Cards or list */}
      {view === "grid" ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
          {filtered.map(uc => <UseCaseCard key={uc.id} uc={uc} onClick={() => setSelected(uc)}/>)}
        </div>
      ) : (
        <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 10, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead><tr>
              {["Tier","ID","Title","Decision Question","Owner","Audience","Freq","Status","Updated"].map(h => (
                <th key={h} style={{ textAlign: "left", fontWeight: 500, fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em", padding: "12px var(--pad)", borderBottom: "1px solid var(--line)" }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {filtered.map(uc => (
                <tr key={uc.id} onClick={() => setSelected(uc)} style={{ cursor: "pointer", transition: "background 120ms" }}
                  onMouseEnter={e => e.currentTarget.style.background = "var(--hover)"}
                  onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                  <td style={{ padding: "12px var(--pad)", borderBottom: "1px solid var(--line-2)" }}><TierBadge tier={uc.tier}/></td>
                  <td className="mono" style={{ padding: "12px var(--pad)", borderBottom: "1px solid var(--line-2)", color: "var(--ink-3)" }}>{uc.id}</td>
                  <td style={{ padding: "12px var(--pad)", borderBottom: "1px solid var(--line-2)", fontWeight: 500 }}>{uc.title}</td>
                  <td style={{ padding: "12px var(--pad)", borderBottom: "1px solid var(--line-2)", color: "var(--ink-3)", fontStyle: "italic" }}>{uc.question}</td>
                  <td style={{ padding: "12px var(--pad)", borderBottom: "1px solid var(--line-2)" }}>{uc.owner}</td>
                  <td style={{ padding: "12px var(--pad)", borderBottom: "1px solid var(--line-2)", color: "var(--ink-3)" }}>{uc.audience}</td>
                  <td style={{ padding: "12px var(--pad)", borderBottom: "1px solid var(--line-2)" }}>{uc.freq}</td>
                  <td style={{ padding: "12px var(--pad)", borderBottom: "1px solid var(--line-2)" }}>
                    <Pill tone={uc.status === "live" ? "positive" : uc.status === "review" ? "warn" : "draft"}>{uc.status}</Pill>
                  </td>
                  <td style={{ padding: "12px var(--pad)", borderBottom: "1px solid var(--line-2)", color: "var(--ink-4)", fontSize: 12 }}>{uc.updated}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function UseCaseCard({ uc, onClick }) {
  const Renderer = TIER_RENDERER[uc.tier];
  const bracketColor = (BRACKETS.find(b => b.id === uc.bracket) || {}).color || "250";
  return (
    <button onClick={onClick} style={{
      textAlign: "left", padding: 0, borderRadius: 12,
      background: "var(--panel)", border: "1px solid var(--line)",
      overflow: "hidden", display: "flex", flexDirection: "column",
      transition: "border-color 160ms, box-shadow 160ms, transform 160ms",
      boxShadow: "var(--shadow-sm)",
    }}
    onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--accent)"; e.currentTarget.style.boxShadow = "var(--shadow-md)"; e.currentTarget.style.transform = "translateY(-1px)"; }}
    onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--line)"; e.currentTarget.style.boxShadow = "var(--shadow-sm)"; e.currentTarget.style.transform = "translateY(0)"; }}>
      {/* Mini preview */}
      <div style={{ height: 200, background: "var(--bg-2)", padding: 10, overflow: "hidden", position: "relative", borderBottom: "1px solid var(--line)" }}>
        <div style={{ transform: "scale(0.42)", transformOrigin: "top left", width: "238%", height: "238%", pointerEvents: "none" }}>
          <Renderer uc={uc}/>
        </div>
      </div>
      {/* Meta */}
      <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 6 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 6, height: 6, borderRadius: 99, background: `oklch(0.7 0.1 ${bracketColor})` }}/>
          <span className="mono" style={{ fontSize: 10.5, color: "var(--ink-4)", letterSpacing: "0.04em" }}>{uc.id} · {uc.bracket}</span>
          <div style={{ flex: 1 }}/>
          <TierBadge tier={uc.tier}/>
        </div>
        <div style={{ fontSize: 14.5, fontWeight: 500, letterSpacing: "-0.01em", lineHeight: 1.3 }}>{uc.title}</div>
        <div style={{ fontSize: 12, color: "var(--ink-3)", fontStyle: "italic", lineHeight: 1.4 }}>"{uc.question}"</div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 4, fontSize: 11, color: "var(--ink-4)" }}>
          <span>{uc.owner}</span>
          <span>·</span>
          <span>{uc.freq}</span>
          <span style={{ flex: 1 }}/>
          <Pill tone={uc.status === "live" ? "positive" : uc.status === "review" ? "warn" : "draft"}>{uc.status}</Pill>
        </div>
      </div>
    </button>
  );
}

// ───────── Use Case Detail ─────────
function UseCaseDetail({ uc, onBack }) {
  const [tab, setTab] = useStateUC("preview");
  const [activeTier, setActiveTier] = useStateUC(uc.tier);
  const Renderer = TIER_RENDERER[activeTier];

  const tabs = [
    { id: "preview",   label: "Preview" },
    { id: "spec",      label: "Specification" },
    { id: "lineage",   label: "Lineage" },
    { id: "actions",   label: "Action Codes", count: uc.actions.length },
    { id: "history",   label: "History" },
  ];

  return (
    <div style={{ display: "flex", height: "100%", overflow: "hidden" }}>
      <div style={{ flex: 1, overflow: "auto" }}>
        <div style={{ padding: "var(--pad)", maxWidth: 1300, margin: "0 auto", width: "100%" }}>
          <button onClick={onBack} style={{ ...ghostSmall, marginBottom: 14, paddingLeft: 0 }}>
            <I.Chevron size={12} style={{ transform: "rotate(180deg)" }}/> Back to use cases
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <span className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>{uc.id}</span>
            <TierBadge tier={uc.tier} large/>
            <Pill tone={uc.status === "live" ? "positive" : uc.status === "review" ? "warn" : "draft"}>{uc.status}</Pill>
            <span style={{ fontSize: 12, color: "var(--ink-4)" }}>· {uc.bracket} · {uc.domain}</span>
          </div>

          <h1 className="display" style={{ fontSize: 36, margin: "0 0 8px", fontWeight: 500, letterSpacing: "-0.025em" }}>{uc.title}</h1>
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", background: "var(--bg-2)", border: "1px solid var(--line)", borderLeft: "3px solid var(--accent)", borderRadius: 6, marginBottom: 18 }}>
            <span style={{ fontSize: 10, fontWeight: 700, color: "var(--accent)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Decision</span>
            <span style={{ fontSize: 14, fontStyle: "italic", color: "var(--ink-2)" }}>{uc.question}</span>
          </div>

          {/* Tabs */}
          <div style={{ display: "flex", gap: 2, borderBottom: "1px solid var(--line)", marginBottom: 22 }}>
            {tabs.map(t => {
              const active = tab === t.id;
              return (
                <button key={t.id} onClick={() => setTab(t.id)} style={{
                  padding: "10px 14px", display: "flex", alignItems: "center", gap: 6,
                  fontSize: 13, color: active ? "var(--ink)" : "var(--ink-3)",
                  fontWeight: active ? 500 : 400,
                  borderBottom: `1.5px solid ${active ? "var(--accent)" : "transparent"}`,
                  marginBottom: -1,
                }}>
                  {t.label}
                  {t.count != null && (
                    <span className="mono" style={{ fontSize: 10, padding: "1px 6px", borderRadius: 99, background: "var(--hover)", color: "var(--ink-3)" }}>{t.count}</span>
                  )}
                </button>
              );
            })}
          </div>

          {tab === "preview" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {/* Tier switcher — narrative path */}
              <div style={{ display: "flex", alignItems: "center", gap: 0, padding: "10px 12px", background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 10 }}>
                <span style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em", marginRight: 12 }}>Decision flow</span>
                {Object.keys(TIERS).map((t, i) => {
                  const active = activeTier === t;
                  const isUcTier = uc.tier === t;
                  return (
                    <React.Fragment key={t}>
                      {i > 0 && <span style={{ color: "var(--ink-4)", margin: "0 4px" }}>→</span>}
                      <button onClick={() => setActiveTier(t)} style={{
                        padding: "5px 10px", borderRadius: 6, fontSize: 11,
                        background: active ? `oklch(0.7 0.1 ${TIERS[t].color} / 0.2)` : "transparent",
                        color: active ? `oklch(0.4 0.13 ${TIERS[t].color})` : "var(--ink-3)",
                        fontWeight: active ? 600 : 400,
                        border: isUcTier && !active ? `1px dashed oklch(0.7 0.1 ${TIERS[t].color} / 0.5)` : "1px solid transparent",
                        position: "relative",
                      }} className="mono">
                        {t} · {TIERS[t].time}
                      </button>
                    </React.Fragment>
                  );
                })}
                <div style={{ flex: 1 }}/>
                <button style={ghostSmall}><I.Eye size={12}/> Open full</button>
                <button style={{ ...ghostSmall, marginLeft: 4 }}><I.Edit size={12}/> Edit layout</button>
              </div>

              <Renderer uc={uc}/>

              {/* Validation rules */}
              <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 10, padding: "var(--pad)" }}>
                <div style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>Tier validation</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 12.5 }}>
                  {[
                    { ok: true,  text: `KPI band — ${activeTier === "T1" ? "5" : "4"} cards, full width` },
                    { ok: true,  text: "Slicer bar within Pulse limit (≤3 slicers)" },
                    { ok: activeTier !== "T1", text: "Variance/waterfall reconciles to total Δ" },
                    { ok: activeTier === "T4", text: "Action panel mandatory for T4" },
                    { ok: true,  text: "Decision question matches tier-time hierarchy" },
                    { ok: activeTier !== "T1" || true, text: "Strategic signal — no owner, no steps" },
                  ].map((v, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ width: 14, height: 14, borderRadius: 99, background: v.ok ? "oklch(0.92 0.08 150)" : "oklch(0.92 0.08 30)", color: v.ok ? "oklch(0.4 0.14 150)" : "oklch(0.4 0.16 30)", display: "grid", placeItems: "center", fontSize: 9, fontWeight: 700 }}>
                        {v.ok ? "✓" : "!"}
                      </span>
                      <span style={{ color: "var(--ink-2)" }}>{v.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {tab === "spec" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 10 }}>
                <div style={cardHead}><div style={cardTitle}>Use case specification</div><span className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>YAML</span></div>
                <pre className="mono" style={{ margin: 0, padding: "var(--pad)", fontSize: 12, lineHeight: 1.7, background: "var(--bg-2)", color: "var(--ink-2)", overflow: "auto" }}>
{`id: ${uc.id}
title: "${uc.title}"
bracket: ${uc.bracket}
domain: ${uc.domain}
tier: ${uc.tier}
decision_question: |
  ${uc.question}
audience: ${uc.audience}
owner: ${uc.owner}
frequency: ${uc.freq}
metrics:
  primary: [met.commercial.net_sales, met.commercial.gm_pct]
  secondary: [met.commercial.volume, met.commercial.asp]
dimensions: [dim.region, dim.segment, dim.period]
slicers: [Period, Region, ${uc.tier === "T4" ? "Priority" : "Business Unit"}]
action_codes:
${uc.actions.map(a => `  - ${a}`).join("\n") || "  []"}
status: ${uc.status}`}
                </pre>
              </div>
            </div>
          )}

          {tab === "lineage" && (
            <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 10, padding: "var(--pad)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18 }}>
                <span className="mono" style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase" }}>Sources</span>
                <span style={{ flex: 1, height: 1, background: "var(--line)" }}/>
                <span className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>Metrics</span>
                <span style={{ flex: 1, height: 1, background: "var(--line)" }}/>
                <span className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>This use case</span>
                <span style={{ flex: 1, height: 1, background: "var(--line)" }}/>
                <span className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>Actions</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 16 }}>
                {[
                  ["src.billing", "src.crm", "src.events"],
                  ["met.commercial.net_sales", "met.commercial.gm_pct", "met.commercial.volume"],
                  [uc.id + " · " + uc.title],
                  uc.actions.length ? uc.actions : ["—"],
                ].map((col, i) => (
                  <div key={i} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {col.map(item => (
                      <div key={item} style={{
                        padding: "10px 12px", background: i === 2 ? "var(--ink)" : "var(--bg-2)",
                        color: i === 2 ? "var(--bg)" : "var(--ink-2)",
                        border: "1px solid var(--line)",
                        borderRadius: 6, fontSize: 12, fontFamily: i === 2 ? "var(--font-ui)" : "var(--font-mono)",
                        fontWeight: i === 2 ? 500 : 400,
                      }}>
                        {item}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}

          {tab === "actions" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {uc.actions.length === 0 && (
                <div style={{ padding: 28, textAlign: "center", color: "var(--ink-3)", border: "1px dashed var(--line)", borderRadius: 10, fontSize: 13 }}>
                  No action codes linked. Add one to make this a T4 use case.
                </div>
              )}
              {uc.actions.map(aId => {
                const a = ACTION_CODES.find(x => x.id === aId);
                if (!a) return null;
                return (
                  <div key={aId} style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 10, padding: "var(--pad)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                      <span className="mono" style={{ fontSize: 11, fontWeight: 700, color: "var(--accent)", background: "var(--accent-soft)", padding: "3px 8px", borderRadius: 4 }}>{a.id}</span>
                      <span style={{ fontSize: 14, fontWeight: 500 }}>{a.name}</span>
                      <div style={{ flex: 1 }}/>
                      <Pill tone={a.priority === "Critical" ? "warn" : a.priority === "High" ? "accent" : "neutral"}>{a.priority}</Pill>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14, marginTop: 10 }}>
                      <PropPair label="Trigger" value={a.trigger} mono/>
                      <PropPair label="Owner" value={a.owner}/>
                      <PropPair label="Impact" value={a.impact} bold/>
                      <PropPair label="Active instances" value={a.active}/>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {tab === "history" && (
            <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 10, padding: "6px 0" }}>
              {[
                ["A. Haferkorn", `published v1.2 to ${uc.audience}`, uc.updated],
                ["R. Okafor",    "added action code C-M1.1",         "2d ago"],
                ["L. Chen",      "validated tier classification",    "5d ago"],
                ["M. Park",      `created use case ${uc.id}`,        "2w ago"],
              ].map((e, i) => (
                <div key={i} style={{ padding: "12px var(--pad)", borderTop: i === 0 ? "none" : "1px solid var(--line-2)", display: "flex", alignItems: "center", gap: 12 }}>
                  <I.Clock size={13}/>
                  <div style={{ fontSize: 13, flex: 1 }}>
                    <span style={{ fontWeight: 500 }}>{e[0]}</span>
                    <span style={{ color: "var(--ink-3)" }}> {e[1]}</span>
                  </div>
                  <span style={{ fontSize: 11.5, color: "var(--ink-4)" }}>{e[2]}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right rail */}
      <aside style={{ width: 300, flexShrink: 0, borderLeft: "1px solid var(--line)", padding: "var(--pad)", overflow: "auto", background: "var(--bg)" }}>
        <div style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>Properties</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 14, fontSize: 12.5 }}>
          <PropRow label="Tier"><TierBadge tier={uc.tier}/></PropRow>
          <PropRow label="Bracket"><Pill>{uc.bracket}</Pill></PropRow>
          <PropRow label="Domain">{uc.domain}</PropRow>
          <PropRow label="Owner"><OwnerChip name={uc.owner}/></PropRow>
          <PropRow label="Audience">{uc.audience}</PropRow>
          <PropRow label="Frequency">{uc.freq}</PropRow>
          <PropRow label="Last updated">{uc.updated}</PropRow>
        </div>

        <div style={{ margin: "24px 0 12px", fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Decision-time hierarchy
        </div>
        <div style={{ background: "var(--bg-2)", border: "1px solid var(--line)", borderRadius: 10, padding: 12, fontSize: 11.5, lineHeight: 1.5 }}>
          A <strong>{uc.tier}</strong> use case must answer its decision in
          <span style={{ color: "var(--accent)", fontWeight: 600 }}> {TIERS[uc.tier].time} </span>
          for <strong>{TIERS[uc.tier].audience}</strong>.
          <div style={{ marginTop: 8, color: "var(--ink-3)", fontSize: 11 }}>
            Pulse principle: 3s read → 30s scan → 5min investigate → 30min decide.
          </div>
        </div>

        <div style={{ margin: "24px 0 12px", fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Studio AI
        </div>
        <div style={{ padding: 14, borderRadius: 10, background: "linear-gradient(180deg, var(--accent-soft), transparent)", border: "1px solid var(--line)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8, fontSize: 12 }}>
            <I.Sparkle size={12} stroke={1.8}/><span style={{ fontWeight: 500 }}>Suggestion</span>
          </div>
          <div style={{ fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.5, marginBottom: 10 }}>
            {uc.tier === "T1" || uc.tier === "T2"
              ? "This use case escalates to a T4 prescriptive layer. Want me to draft the recommended actions?"
              : "Detected 3 candidate metrics not yet linked. Auto-add to the spec?"}
          </div>
          <button style={{ ...primaryBtn, width: "100%", justifyContent: "center" }}>Review draft</button>
        </div>
      </aside>
    </div>
  );
}

function PropPair({ label, value, mono, bold }) {
  return (
    <div>
      <div style={{ fontSize: 10.5, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
      <div style={{ fontSize: 12.5, marginTop: 3, fontFamily: mono ? "var(--font-mono)" : "var(--font-ui)", fontWeight: bold ? 600 : 400, color: bold ? "oklch(0.5 0.13 150)" : "var(--ink-2)" }}>{value}</div>
    </div>
  );
}

Object.assign(window, { UseCases, UseCaseDetail, TierBadge, TIERS });
