// Detail view — metric detail with inline editing & comments
function Detail({ metric: metricProp, onBack }) {
  const metric = metricProp || FRAMEWORK.metrics.find(m => m.id === "nrr");
  const [tab, setTab] = useState("overview");
  const [editingName, setEditingName] = useState(false);
  const [name, setName] = useState(metric.name);
  const [desc, setDesc] = useState(
    "Measures how revenue from existing customers evolves over time, inclusive of expansions, downgrades, and churn. Calculated as ending ARR from the starting cohort divided by starting ARR."
  );
  const [editingDesc, setEditingDesc] = useState(false);
  const [comments, setComments] = useState([
    { who: "R. Okafor", when: "2h ago", text: "I moved this to certified — cohort logic matches the board definition now." },
    { who: "L. Chen",   when: "yday",   text: "Can we add an expansion-only cut? Useful for the finance review." },
  ]);
  const [draft, setDraft] = useState("");

  useEffect(() => { setName(metric.name); }, [metric]);

  const sql = `select
  cohort_month,
  sum(ending_arr) / nullif(sum(starting_arr), 0) as nrr
from {{ ref('fct_customer_arr') }}
where cohort_month >= date_trunc('month', current_date) - interval '12 month'
group by 1;`;

  const tabs = [
    { id: "overview",     label: "Overview" },
    { id: "definition",   label: "Definition" },
    { id: "lineage",      label: "Lineage" },
    { id: "comments",     label: "Comments", count: comments.length },
    { id: "history",      label: "History" },
  ];

  return (
    <div style={{ display: "flex", height: "100%", overflow: "hidden" }}>
      {/* Main */}
      <div style={{ flex: 1, overflow: "auto" }}>
        <div style={{ padding: "var(--pad)", maxWidth: 900, margin: "0 auto", width: "100%" }}>
          {/* Header */}
          <div style={{ paddingTop: 8 }}>
            <button onClick={onBack} style={{ ...ghostSmall, marginBottom: 14, paddingLeft: 0 }}>
              <I.Chevron size={12} style={{ transform: "rotate(180deg)" }}/> Back to library
            </button>

            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <span className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>{metric.ref}</span>
              <Pill tone="positive"><I.Check size={10} stroke={2}/> Certified</Pill>
              <Pill tone="neutral">{metric.type}</Pill>
              <Pill tone="neutral">{metric.domain}</Pill>
            </div>

            {editingName ? (
              <input autoFocus value={name} onChange={e => setName(e.target.value)}
                     onBlur={() => setEditingName(false)}
                     onKeyDown={e => e.key === "Enter" && setEditingName(false)}
                     className="display"
                     style={{
                       fontSize: 36, fontWeight: 500, letterSpacing: "-0.025em",
                       width: "100%", border: 0, outline: 0, padding: 0,
                       borderBottom: "2px solid var(--accent)", background: "transparent",
                     }}/>
            ) : (
              <h1 onClick={() => setEditingName(true)} className="display" style={{
                fontSize: 36, margin: 0, fontWeight: 500, letterSpacing: "-0.025em",
                cursor: "text", padding: "0 4px", marginLeft: -4, borderRadius: 6,
                transition: "background 120ms",
              }}
              onMouseEnter={e => e.currentTarget.style.background = "var(--hover)"}
              onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                {name}
              </h1>
            )}

            {editingDesc ? (
              <textarea autoFocus value={desc} onChange={e => setDesc(e.target.value)}
                        onBlur={() => setEditingDesc(false)}
                        style={{
                          width: "100%", border: "1px solid var(--accent)", borderRadius: 8,
                          padding: 10, fontSize: 14.5, lineHeight: 1.6, background: "transparent",
                          resize: "vertical", minHeight: 80, outline: 0, marginTop: 10,
                        }}/>
            ) : (
              <p onClick={() => setEditingDesc(true)} style={{
                fontSize: 14.5, lineHeight: 1.6, color: "var(--ink-2)", marginTop: 12,
                cursor: "text", padding: "8px 4px", marginLeft: -4, borderRadius: 6,
              }}
              onMouseEnter={e => e.currentTarget.style.background = "var(--hover)"}
              onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                {desc}
              </p>
            )}
          </div>

          {/* Tabs */}
          <div style={{ display: "flex", gap: 2, borderBottom: "1px solid var(--line)", marginTop: 22, marginBottom: 20 }}>
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
                    <span className="mono" style={{
                      fontSize: 10, padding: "1px 6px", borderRadius: 99,
                      background: "var(--hover)", color: "var(--ink-3)",
                    }}>{t.count}</span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Tab content */}
          {tab === "overview" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--gap)" }}>
              <div style={card}>
                <div style={{ ...cardHead, paddingTop: 14, paddingBottom: 14 }}>
                  <div style={cardTitle}>Latest value</div>
                  <span className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>as of today</span>
                </div>
                <div style={{ padding: "var(--pad)", display: "grid", gridTemplateColumns: "auto 1fr", gap: 28, alignItems: "center" }}>
                  <div>
                    <div className="display" style={{ fontSize: 48, fontWeight: 500, letterSpacing: "-0.03em" }}>114%</div>
                    <div style={{ fontSize: 12, color: "oklch(0.52 0.14 150)" }}>+2 pts vs last month</div>
                  </div>
                  <Sparkline data={[100,102,104,103,107,110,111,112,113,114,114,114]} height={56}/>
                </div>
              </div>

              <div style={card}>
                <div style={cardHead}><div style={cardTitle}>Dimensions</div>
                  <button style={ghostSmall}><I.Plus size={11}/> Add</button>
                </div>
                <div style={{ padding: "var(--pad)", display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {["Plan Tier", "Region", "Signup Cohort", "Channel"].map(d => (
                    <Pill key={d} tone="neutral"><I.Dim size={10}/>{d}</Pill>
                  ))}
                </div>
              </div>
            </div>
          )}

          {tab === "definition" && (
            <div style={card}>
              <div style={cardHead}>
                <div><div style={cardTitle}>SQL definition</div><div style={cardSub}>Compiled via dbt · ref: fct_customer_arr</div></div>
                <button style={ghostSmall}><I.Copy size={12}/> Copy</button>
              </div>
              <pre className="mono" style={{
                margin: 0, padding: "var(--pad)",
                fontSize: 12.5, lineHeight: 1.7,
                background: "var(--bg-2)",
                color: "var(--ink-2)", overflow: "auto",
              }}>{sql}</pre>
            </div>
          )}

          {tab === "lineage" && (
            <div style={{ ...card, padding: "var(--pad)", fontSize: 13, color: "var(--ink-3)" }}>
              Upstream: <span className="mono" style={{color:"var(--ink)"}}>src.billing</span> →
              <span className="mono" style={{color:"var(--ink)"}}> met.revenue.mrr</span>.
              Downstream: <span className="mono" style={{color:"var(--ink)"}}>goal.efficient_growth</span>.
              <div style={{ marginTop: 10 }}><button style={ghostBtn}><I.Graph size={13}/> Open in Canvas</button></div>
            </div>
          )}

          {tab === "comments" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {comments.map((c, i) => (
                <div key={i} style={{ ...card, padding: "14px var(--pad)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                    <div style={{
                      width: 24, height: 24, borderRadius: 99,
                      background: `oklch(0.65 0.12 ${(i*80) % 360})`, color: "#fff",
                      display: "grid", placeItems: "center", fontSize: 10, fontWeight: 600,
                    }}>{c.who.split(/[.\s]/).map(s=>s[0]).join("")}</div>
                    <span style={{ fontSize: 12.5, fontWeight: 500 }}>{c.who}</span>
                    <span style={{ fontSize: 11.5, color: "var(--ink-4)" }}>{c.when}</span>
                  </div>
                  <div style={{ fontSize: 13.5, lineHeight: 1.55, color: "var(--ink-2)" }}>{c.text}</div>
                </div>
              ))}
              <div style={{ ...card, padding: 12, display: "flex", gap: 10, alignItems: "center" }}>
                <input value={draft} onChange={e => setDraft(e.target.value)}
                       placeholder="Leave a comment or @mention someone…"
                       style={{ flex: 1, border: 0, outline: 0, fontSize: 13, background: "transparent" }}
                       onKeyDown={e => {
                         if (e.key === "Enter" && draft.trim()) {
                           setComments([...comments, { who: "A. Haferkorn", when: "just now", text: draft }]);
                           setDraft("");
                         }
                       }}/>
                <button style={primaryBtn} onClick={() => {
                  if (!draft.trim()) return;
                  setComments([...comments, { who: "A. Haferkorn", when: "just now", text: draft }]);
                  setDraft("");
                }}>Comment</button>
              </div>
            </div>
          )}

          {tab === "history" && (
            <div style={{ ...card, padding: "6px 0" }}>
              {[
                ["R. Okafor",     "certified definition",        "2h ago"],
                ["A. Haferkorn",  "edited description",          "yday"],
                ["L. Chen",       "added dimension 'Region'",    "3d ago"],
                ["M. Park",       "created metric",              "2w ago"],
              ].map((e, i) => (
                <div key={i} style={{
                  padding: "12px var(--pad)",
                  borderTop: i === 0 ? "none" : "1px solid var(--line-2)",
                  display: "flex", alignItems: "center", gap: 12,
                }}>
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
      <aside style={{
        width: 300, flexShrink: 0, borderLeft: "1px solid var(--line)",
        padding: "var(--pad)", overflow: "auto", background: "var(--bg)",
      }}>
        <div style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>Properties</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 14, fontSize: 12.5 }}>
          <PropRow label="Owner"><OwnerChip name="R. Okafor"/></PropRow>
          <PropRow label="Reviewers">
            <div style={{ display: "flex", gap: 4 }}>
              <OwnerChip name="L. Chen" small/>
              <OwnerChip name="M. Park" small/>
            </div>
          </PropRow>
          <PropRow label="Domain"><Pill>Revenue</Pill></PropRow>
          <PropRow label="Type">Ratio</PropRow>
          <PropRow label="Grain">Month</PropRow>
          <PropRow label="Unit"><span className="mono">%</span></PropRow>
          <PropRow label="Sources"><span className="mono" style={{ color: "var(--ink-2)" }}>src.billing</span></PropRow>
          <PropRow label="Created">Mar 14, 2025</PropRow>
        </div>

        <div style={{ margin: "24px 0 12px", fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Studio AI
        </div>
        <div style={{
          padding: 14, borderRadius: 10,
          background: "linear-gradient(180deg, var(--accent-soft), transparent)",
          border: "1px solid var(--line)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8, fontSize: 12 }}>
            <I.Sparkle size={12} stroke={1.8}/>
            <span style={{ fontWeight: 500 }}>Suggestions</span>
          </div>
          <div style={{ fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.5, marginBottom: 10 }}>
            Your definition references <span className="mono">fct_customer_arr</span> but omits mid-month contractions. Shall I draft a fix?
          </div>
          <button style={{ ...primaryBtn, width: "100%", justifyContent: "center" }}>Review draft</button>
        </div>
      </aside>
    </div>
  );
}

function PropRow({ label, children }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "90px 1fr", alignItems: "center", gap: 8 }}>
      <span style={{ color: "var(--ink-4)", fontSize: 11.5 }}>{label}</span>
      <span style={{ color: "var(--ink-2)" }}>{children}</span>
    </div>
  );
}
function OwnerChip({ name, small }) {
  const init = name.split(/[.\s]/).map(s=>s[0]).join("");
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
      <span style={{
        width: small ? 18 : 20, height: small ? 18 : 20, borderRadius: 99,
        background: `oklch(0.6 0.13 ${name.charCodeAt(0) * 7 % 360})`,
        color: "#fff", fontSize: 9, fontWeight: 600,
        display: "grid", placeItems: "center",
      }}>{init}</span>
      {!small && <span style={{ fontSize: 12.5 }}>{name}</span>}
    </span>
  );
}

Object.assign(window, { Detail });
