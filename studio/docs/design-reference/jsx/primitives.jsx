// Wizard — create new element with AI assist
function Wizard({ open, onClose }) {
  const [step, setStep] = useState(0);
  const [kind, setKind] = useState("metric");
  const [prompt, setPrompt] = useState("");
  const [generating, setGenerating] = useState(false);
  const [draft, setDraft] = useState(null);

  useEffect(() => { if (!open) { setStep(0); setKind("metric"); setPrompt(""); setDraft(null); } }, [open]);

  const runAI = () => {
    setGenerating(true);
    setTimeout(() => {
      setGenerating(false);
      setDraft({
        name: prompt ? titleCase(prompt) : "Qualified Pipeline Velocity",
        ref: "met.growth." + slug(prompt || "qualified_pipeline_velocity"),
        domain: "Growth",
        type: "Ratio",
        grain: "week",
        unit: "USD/day",
        description: "Measures how quickly qualified opportunities convert to closed-won revenue, normalized by cycle length.",
        sql: `select
  week,
  sum(closed_won_arr) / nullif(avg(cycle_days), 0) as velocity
from {{ ref('fct_opportunities') }}
where stage in ('qualified','closed_won')
group by 1;`,
        sources: ["src.crm", "src.billing"],
      });
      setStep(2);
    }, 900);
  };

  if (!open) return null;

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, zIndex: 90,
      background: "rgba(11,11,12,0.4)", backdropFilter: "blur(4px)",
      display: "grid", placeItems: "center", padding: 40,
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        width: 720, maxWidth: "100%", maxHeight: "88vh",
        background: "var(--panel)", borderRadius: 14,
        border: "1px solid var(--line)", boxShadow: "var(--shadow-lg)",
        display: "flex", flexDirection: "column", overflow: "hidden",
      }}>
        {/* Stepper */}
        <div style={{ padding: "16px 24px", borderBottom: "1px solid var(--line-2)", display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.08em" }}>New element</div>
          <div style={{ flex: 1, display: "flex", gap: 6 }}>
            {["Choose", "Describe", "Review"].map((s, i) => (
              <div key={s} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12,
                color: i === step ? "var(--ink)" : "var(--ink-4)", fontWeight: i === step ? 500 : 400 }}>
                <span style={{
                  width: 18, height: 18, borderRadius: 99,
                  background: i <= step ? "var(--accent)" : "var(--bg-2)",
                  color: i <= step ? "var(--accent-ink)" : "var(--ink-4)",
                  display: "grid", placeItems: "center", fontSize: 10, fontWeight: 600,
                }}>{i < step ? "✓" : i + 1}</span>
                {s}
                {i < 2 && <span style={{ width: 16, height: 1, background: "var(--line)", marginLeft: 4 }}/>}
              </div>
            ))}
          </div>
          <button onClick={onClose} style={iconBtn}><I.X size={14}/></button>
        </div>

        <div style={{ flex: 1, overflow: "auto", padding: 28 }}>
          {/* Step 0 */}
          {step === 0 && (
            <div>
              <h2 className="display" style={{ fontSize: 22, fontWeight: 500, margin: "0 0 6px", letterSpacing: "-0.02em" }}>What are you creating?</h2>
              <p style={{ color: "var(--ink-3)", margin: "0 0 22px", fontSize: 13.5 }}>
                Pick a primitive. You can always change type later.
              </p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                {[
                  { id: "metric",    icon: "Metric", label: "Metric",    desc: "A measurable number — count, sum, ratio or model." },
                  { id: "dimension", icon: "Dim",    label: "Dimension", desc: "A categorical slice — cohort, region, channel." },
                  { id: "source",    icon: "Source", label: "Source",    desc: "A connected upstream data source." },
                ].map(o => {
                  const IC = I[o.icon];
                  const active = kind === o.id;
                  return (
                    <button key={o.id} onClick={() => setKind(o.id)} style={{
                      padding: 16, borderRadius: 10,
                      border: `1px solid ${active ? "var(--accent)" : "var(--line)"}`,
                      boxShadow: active ? "0 0 0 3px var(--accent-soft)" : "none",
                      background: "var(--panel)", textAlign: "left",
                      display: "flex", flexDirection: "column", gap: 8,
                      transition: "all 120ms",
                    }}>
                      <IC size={18} stroke={1.5}/>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>{o.label}</div>
                      <div style={{ fontSize: 12, color: "var(--ink-3)", lineHeight: 1.5 }}>{o.desc}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Step 1 */}
          {step === 1 && (
            <div>
              <h2 className="display" style={{ fontSize: 22, fontWeight: 500, margin: "0 0 6px", letterSpacing: "-0.02em" }}>Describe your {kind}</h2>
              <p style={{ color: "var(--ink-3)", margin: "0 0 16px", fontSize: 13.5 }}>
                Studio will draft the definition, dependencies and SQL. You can edit anything afterwards.
              </p>
              <div style={{
                padding: 14, borderRadius: 10,
                border: "1px solid var(--line)",
                background: "var(--panel)",
              }}>
                <textarea value={prompt} onChange={e => setPrompt(e.target.value)}
                          placeholder={`e.g. "Velocity of qualified pipeline, weekly, for enterprise plan customers"`}
                          style={{
                            width: "100%", minHeight: 110, border: 0, outline: 0,
                            background: "transparent", fontSize: 14, lineHeight: 1.5, resize: "vertical",
                          }}/>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 11, color: "var(--ink-4)" }}>Try:</span>
                  {["Weekly activation by cohort", "Net new ARR per rep", "P50 support response time"].map(s => (
                    <button key={s} onClick={() => setPrompt(s)} style={{
                      fontSize: 11.5, padding: "4px 10px", borderRadius: 99,
                      border: "1px solid var(--line)", color: "var(--ink-2)",
                    }}>{s}</button>
                  ))}
                </div>
              </div>
              {generating && (
                <div style={{ marginTop: 14, padding: 12, borderRadius: 10, background: "var(--accent-soft)", color: "var(--accent)", fontSize: 12.5, display: "flex", alignItems: "center", gap: 8 }}>
                  <I.Sparkle size={13} stroke={1.8}/> Drafting definition and checking for duplicates…
                </div>
              )}
            </div>
          )}

          {/* Step 2 */}
          {step === 2 && draft && (
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, color: "oklch(0.52 0.14 150)", fontSize: 12, marginBottom: 8 }}>
                <I.Sparkle size={12} stroke={1.8}/> Draft ready — review and edit before saving.
              </div>
              <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>{draft.ref}</div>
              <h2 className="display" style={{ fontSize: 26, fontWeight: 500, margin: "4px 0 12px", letterSpacing: "-0.02em" }}>{draft.name}</h2>
              <div style={{ color: "var(--ink-2)", fontSize: 13.5, lineHeight: 1.6, marginBottom: 18 }}>{draft.description}</div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 18 }}>
                {[["Domain", draft.domain], ["Type", draft.type], ["Grain", draft.grain], ["Unit", draft.unit]].map(([k,v]) => (
                  <div key={k} style={{ padding: 10, border: "1px solid var(--line)", borderRadius: 8 }}>
                    <div style={{ fontSize: 10.5, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{k}</div>
                    <div style={{ fontSize: 13, fontWeight: 500, marginTop: 2 }}>{v}</div>
                  </div>
                ))}
              </div>

              <div style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>SQL</div>
              <pre className="mono" style={{
                margin: 0, padding: 14, borderRadius: 10,
                background: "var(--bg-2)", border: "1px solid var(--line)",
                fontSize: 12, lineHeight: 1.7, color: "var(--ink-2)", overflow: "auto",
              }}>{draft.sql}</pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: "14px 20px", borderTop: "1px solid var(--line-2)", display: "flex", justifyContent: "space-between", gap: 8 }}>
          <button style={ghostBtn} onClick={() => step === 0 ? onClose() : setStep(step - 1)}>
            {step === 0 ? "Cancel" : "Back"}
          </button>
          {step === 0 && <button style={primaryBtn} onClick={() => setStep(1)}>Continue <I.ArrowR size={12}/></button>}
          {step === 1 && (
            <button style={primaryBtn} onClick={runAI} disabled={generating}>
              <I.Sparkle size={12} stroke={1.8}/> {generating ? "Drafting…" : "Generate draft"}
            </button>
          )}
          {step === 2 && <button style={primaryBtn} onClick={onClose}><I.Check size={12} stroke={2}/> Save to framework</button>}
        </div>
      </div>
    </div>
  );
}

function titleCase(s) { return s.replace(/\b\w/g, c => c.toUpperCase()); }
function slug(s) { return s.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "").slice(0, 40); }

Object.assign(window, { Wizard });
