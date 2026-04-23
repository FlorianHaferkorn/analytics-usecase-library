// Tweaks panel
function Tweaks({ open, onClose, tweaks, setTweak }) {
  if (!open) return null;

  const hues = [
    { name: "Indigo",  h: 250 },
    { name: "Emerald", h: 150 },
    { name: "Amber",   h: 75 },
    { name: "Rose",    h: 20 },
    { name: "Violet",  h: 290 },
    { name: "Teal",    h: 190 },
    { name: "Graphite",h: 250, chroma: 0.01, lightness: 0.38 },
  ];

  return (
    <div style={{
      position: "fixed", right: 16, bottom: 16, zIndex: 80,
      width: 312, background: "var(--panel)",
      border: "1px solid var(--line)", borderRadius: 12,
      boxShadow: "var(--shadow-lg)", overflow: "hidden",
    }}>
      <div style={{
        padding: "12px 14px", borderBottom: "1px solid var(--line-2)",
        display: "flex", alignItems: "center", gap: 10,
      }}>
        <I.Settings size={13}/>
        <span style={{ fontSize: 13, fontWeight: 500 }}>Tweaks</span>
        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--ink-4)" }}>Live preview</span>
        <button onClick={onClose} style={iconBtn}><I.X size={12}/></button>
      </div>

      <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 16 }}>

        <TweakSection label="Theme">
          <div style={{ display: "flex", gap: 6 }}>
            {["light", "dark"].map(t => (
              <button key={t} onClick={() => setTweak("theme", t)} style={{
                flex: 1, padding: "8px 10px", borderRadius: 7,
                border: `1px solid ${tweaks.theme === t ? "var(--accent)" : "var(--line)"}`,
                background: tweaks.theme === t ? "var(--accent-soft)" : "var(--panel)",
                color: tweaks.theme === t ? "var(--accent)" : "var(--ink-2)",
                fontSize: 12, textTransform: "capitalize", fontWeight: tweaks.theme === t ? 500 : 400,
              }}>{t}</button>
            ))}
          </div>
        </TweakSection>

        <TweakSection label="Accent color">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(7,1fr)", gap: 6 }}>
            {hues.map(h => {
              const sel = tweaks.accentHue === h.h && (tweaks.accentChroma ?? 0.13) === (h.chroma ?? 0.13);
              return (
                <button key={h.name} title={h.name}
                  onClick={() => {
                    setTweak("accentHue", h.h);
                    setTweak("accentChroma", h.chroma ?? 0.13);
                    setTweak("accentLightness", h.lightness ?? 0.62);
                  }}
                  style={{
                    aspectRatio: "1", borderRadius: 7,
                    background: `oklch(${h.lightness ?? 0.62} ${h.chroma ?? 0.13} ${h.h})`,
                    border: `2px solid ${sel ? "var(--ink)" : "transparent"}`,
                    outline: "1px solid var(--line)",
                    cursor: "pointer",
                }}/>
              );
            })}
          </div>
          <div style={{ marginTop: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--ink-4)", marginBottom: 4 }}>
              <span>Fine-tune hue</span><span className="mono">{tweaks.accentHue}°</span>
            </div>
            <input type="range" min="0" max="360" value={tweaks.accentHue}
                   onChange={e => setTweak("accentHue", +e.target.value)}
                   style={{ width: "100%", accentColor: "var(--accent)" }}/>
          </div>
        </TweakSection>

        <TweakSection label="Density">
          <div style={{ display: "flex", gap: 4, background: "var(--bg-2)", padding: 3, borderRadius: 7 }}>
            {["airy", "balanced", "dense"].map(d => (
              <button key={d} onClick={() => setTweak("density", d)} style={{
                flex: 1, padding: "5px 8px", borderRadius: 5,
                background: tweaks.density === d ? "var(--panel)" : "transparent",
                boxShadow: tweaks.density === d ? "var(--shadow-sm)" : "none",
                color: tweaks.density === d ? "var(--ink)" : "var(--ink-3)",
                fontSize: 11.5, textTransform: "capitalize",
                fontWeight: tweaks.density === d ? 500 : 400,
              }}>{d}</button>
            ))}
          </div>
        </TweakSection>

        <TweakSection label="Font pairing">
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {[
              { id: "inter", label: "Inter · JetBrains Mono", sample: "Aa" },
              { id: "ibm",   label: "IBM Plex Sans · Mono",    sample: "Aa" },
              { id: "geist", label: "Geist · Geist Mono",      sample: "Aa" },
              { id: "serif", label: "Inter · Instrument Serif", sample: "Aa" },
            ].map(f => {
              const sel = tweaks.fontPairing === f.id;
              return (
                <button key={f.id} onClick={() => setTweak("fontPairing", f.id)} style={{
                  padding: "8px 10px", borderRadius: 7,
                  border: `1px solid ${sel ? "var(--accent)" : "var(--line)"}`,
                  background: sel ? "var(--accent-soft)" : "var(--panel)",
                  display: "flex", alignItems: "center", gap: 10,
                  fontSize: 12, textAlign: "left",
                }}>
                  <span style={{
                    width: 28, height: 24, display: "grid", placeItems: "center",
                    background: "var(--bg-2)", borderRadius: 5,
                    fontSize: 14, fontWeight: 500,
                    fontFamily: f.id === "ibm" ? "IBM Plex Sans" : f.id === "geist" ? "Geist" : f.id === "serif" ? "Instrument Serif" : "Inter",
                  }}>{f.sample}</span>
                  <span style={{ color: sel ? "var(--accent)" : "var(--ink-2)", fontWeight: sel ? 500 : 400 }}>{f.label}</span>
                </button>
              );
            })}
          </div>
        </TweakSection>

        <TweakSection label="Sidebar">
          <div style={{ display: "flex", gap: 4, background: "var(--bg-2)", padding: 3, borderRadius: 7 }}>
            {["expanded", "collapsed"].map(s => (
              <button key={s} onClick={() => setTweak("sidebar", s)} style={{
                flex: 1, padding: "5px 8px", borderRadius: 5,
                background: tweaks.sidebar === s ? "var(--panel)" : "transparent",
                boxShadow: tweaks.sidebar === s ? "var(--shadow-sm)" : "none",
                color: tweaks.sidebar === s ? "var(--ink)" : "var(--ink-3)",
                fontSize: 11.5, textTransform: "capitalize",
                fontWeight: tweaks.sidebar === s ? 500 : 400,
              }}>{s}</button>
            ))}
          </div>
        </TweakSection>

      </div>
    </div>
  );
}

function TweakSection({ label, children }) {
  return (
    <div>
      <div style={{
        fontSize: 10.5, color: "var(--ink-4)",
        textTransform: "uppercase", letterSpacing: "0.08em",
        marginBottom: 8, fontWeight: 500,
      }}>{label}</div>
      {children}
    </div>
  );
}

Object.assign(window, { Tweaks });
