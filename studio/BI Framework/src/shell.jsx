// Shell: sidebar + topbar + command palette scaffolding
const { useState, useEffect, useRef, useMemo, useCallback } = React;

const NAV_ITEMS = [
  { id: "dashboard", label: "Overview",   icon: "Home" },
  { id: "canvas",    label: "Canvas",     icon: "Graph" },
  { id: "library",   label: "Library",    icon: "Library" },
  { id: "detail",    label: "Detail",     icon: "Book" },
];

const Pill = ({ tone = "neutral", children }) => {
  const tones = {
    neutral:  { bg: "var(--hover)",    fg: "var(--ink-2)", bd: "var(--line)" },
    accent:   { bg: "var(--accent-soft)", fg: "var(--accent)", bd: "transparent" },
    positive: { bg: "oklch(0.92 0.06 150 / 0.5)", fg: "oklch(0.42 0.12 150)", bd: "transparent" },
    warn:     { bg: "oklch(0.94 0.06 75 / 0.6)",  fg: "oklch(0.48 0.14 60)",  bd: "transparent" },
    draft:    { bg: "var(--line-2)", fg: "var(--ink-3)", bd: "var(--line)" },
  };
  const t = tones[tone] || tones.neutral;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "2px 8px", borderRadius: 999,
      fontSize: 11.5, fontWeight: 500, letterSpacing: "-0.005em",
      background: t.bg, color: t.fg, border: `1px solid ${t.bd}`,
      whiteSpace: "nowrap",
    }}>{children}</span>
  );
};

const StatusDot = ({ status }) => {
  const colors = {
    certified: "oklch(0.6 0.15 150)",
    review:    "oklch(0.7 0.15 75)",
    draft:     "var(--ink-4)",
  };
  return <span style={{
    display: "inline-block", width: 6, height: 6, borderRadius: 99,
    background: colors[status] || "var(--ink-4)"
  }} />;
};

const KBD = ({ children }) => (
  <span style={{
    display: "inline-flex", alignItems: "center", justifyContent: "center",
    minWidth: 18, height: 18, padding: "0 5px",
    fontFamily: "var(--font-mono)", fontSize: 10.5, fontWeight: 500,
    color: "var(--ink-3)", background: "var(--bg-2)",
    border: "1px solid var(--line)", borderRadius: 5,
  }}>{children}</span>
);

function Sidebar({ route, setRoute, collapsed, setCollapsed, onNew, onCmd }) {
  const w = collapsed ? 68 : 248;
  return (
    <aside style={{
      width: w, flexShrink: 0, height: "100%",
      borderRight: "1px solid var(--line)",
      background: "var(--bg)",
      display: "flex", flexDirection: "column",
      transition: "width 240ms cubic-bezier(.2,.8,.2,1)",
      position: "relative",
    }}>
      {/* Brand */}
      <div style={{
        height: 56, padding: "0 16px",
        display: "flex", alignItems: "center", gap: 10,
        borderBottom: "1px solid var(--line-2)",
      }}>
        <div style={{
          width: 26, height: 26, borderRadius: 7,
          background: "var(--ink)", color: "var(--bg)",
          display: "grid", placeItems: "center",
          fontFamily: "var(--font-display)", fontWeight: 600, fontSize: 14,
          letterSpacing: "-0.04em",
        }}>S</div>
        {!collapsed && (
          <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.1 }}>
            <div style={{ fontWeight: 600, fontSize: 13.5, letterSpacing: "-0.01em" }}>Studio</div>
            <div style={{ fontSize: 11, color: "var(--ink-3)" }}>Analytics Framework</div>
          </div>
        )}
      </div>

      {/* New + Search */}
      <div style={{ padding: "14px 12px 6px", display: "flex", flexDirection: "column", gap: 6 }}>
        <button onClick={onNew} style={{
          height: 34, padding: collapsed ? 0 : "0 10px",
          display: "flex", alignItems: "center", justifyContent: collapsed ? "center" : "flex-start",
          gap: 10, borderRadius: 8,
          background: "var(--ink)", color: "var(--bg)",
          fontWeight: 500, fontSize: 13,
        }}>
          <I.Plus size={14} stroke={2} />
          {!collapsed && <>New element<span style={{marginLeft:"auto",opacity:.6}}><KBD>N</KBD></span></>}
        </button>
        <button onClick={onCmd} style={{
          height: 32, padding: collapsed ? 0 : "0 10px",
          display: "flex", alignItems: "center", justifyContent: collapsed ? "center" : "flex-start",
          gap: 10, borderRadius: 8,
          background: "transparent", color: "var(--ink-3)",
          border: "1px solid var(--line)", fontSize: 12.5,
        }}>
          <I.Search size={13} />
          {!collapsed && <>Search framework…<span style={{marginLeft:"auto"}}><KBD>⌘K</KBD></span></>}
        </button>
      </div>

      {/* Nav */}
      <nav style={{ padding: "12px 8px", display: "flex", flexDirection: "column", gap: 1 }}>
        {!collapsed && <div style={navHeader}>Workspace</div>}
        {NAV_ITEMS.map(item => {
          const Active = route === item.id;
          const IconC = I[item.icon];
          return (
            <button key={item.id} onClick={() => setRoute(item.id)} style={{
              height: 32, padding: collapsed ? 0 : "0 10px",
              display: "flex", alignItems: "center", justifyContent: collapsed ? "center" : "flex-start",
              gap: 10, borderRadius: 7,
              background: Active ? "var(--hover)" : "transparent",
              color: Active ? "var(--ink)" : "var(--ink-2)",
              fontWeight: Active ? 500 : 400, fontSize: 13,
              position: "relative",
            }} onMouseEnter={e => !Active && (e.currentTarget.style.background = "var(--hover)")}
              onMouseLeave={e => !Active && (e.currentTarget.style.background = "transparent")}>
              <IconC size={15} stroke={Active ? 1.8 : 1.5} />
              {!collapsed && item.label}
              {!collapsed && Active && <span style={{
                position: "absolute", left: -8, top: 8, bottom: 8, width: 2,
                background: "var(--accent)", borderRadius: 2,
              }}/>}
            </button>
          );
        })}
      </nav>

      {!collapsed && (
        <div style={{ padding: "8px" }}>
          <div style={navHeader}>Domains</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {FRAMEWORK.domains.map(d => (
              <button key={d.id} style={{
                height: 28, padding: "0 10px",
                display: "flex", alignItems: "center", gap: 10, borderRadius: 7,
                color: "var(--ink-2)", fontSize: 12.5,
              }} onMouseEnter={e => e.currentTarget.style.background = "var(--hover)"}
                onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                <span style={{
                  width: 6, height: 6, borderRadius: 2,
                  background: `oklch(0.7 0.1 ${d.color})`,
                }}/>
                <span>{d.name}</span>
                <span style={{marginLeft:"auto",color:"var(--ink-4)",fontSize:11}} className="mono">{d.count}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div style={{ flex: 1 }} />

      {/* Footer */}
      <div style={{
        padding: "10px 12px", borderTop: "1px solid var(--line-2)",
        display: "flex", alignItems: "center", gap: 10,
      }}>
        <div style={{
          width: 28, height: 28, borderRadius: 99,
          background: "linear-gradient(135deg, var(--accent), oklch(0.5 0.12 320))",
          color: "#fff", display: "grid", placeItems: "center",
          fontSize: 11, fontWeight: 600,
        }}>AH</div>
        {!collapsed && (
          <>
            <div style={{ lineHeight: 1.2, flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12.5, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis" }}>Alex Haferkorn</div>
              <div style={{ fontSize: 11, color: "var(--ink-3)" }}>Acme · Pro</div>
            </div>
            <button onClick={() => setCollapsed(!collapsed)} style={{ color: "var(--ink-3)" }} title="Collapse">
              <I.Chevron size={14} />
            </button>
          </>
        )}
      </div>
    </aside>
  );
}

const navHeader = {
  padding: "8px 10px 6px",
  fontSize: 10.5, fontWeight: 500,
  color: "var(--ink-4)", textTransform: "uppercase",
  letterSpacing: "0.08em",
};

function Topbar({ route, onCmd, onToggleTweaks }) {
  const title = {
    dashboard: "Overview",
    canvas: "Canvas",
    library: "Library",
    detail: "Net Revenue Retention",
    wizard: "New element",
  }[route] || "Studio";

  const crumb = {
    dashboard: ["Framework", "Overview"],
    canvas: ["Framework", "Canvas"],
    library: ["Framework", "Library"],
    detail: ["Framework", "Revenue", "Net Revenue Retention"],
  }[route] || ["Framework"];

  return (
    <header style={{
      height: 56, flexShrink: 0,
      borderBottom: "1px solid var(--line)",
      padding: "0 20px",
      display: "flex", alignItems: "center", gap: 12,
      background: "var(--bg)",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--ink-3)", fontSize: 13 }}>
        {crumb.map((c, i) => (
          <React.Fragment key={i}>
            {i > 0 && <I.Chevron size={12} stroke={1.5} />}
            <span style={{ color: i === crumb.length - 1 ? "var(--ink)" : "var(--ink-3)",
                           fontWeight: i === crumb.length - 1 ? 500 : 400 }}>{c}</span>
          </React.Fragment>
        ))}
      </div>

      <div style={{ flex: 1 }} />

      <button onClick={onCmd} style={{
        height: 30, padding: "0 10px",
        display: "flex", alignItems: "center", gap: 8, borderRadius: 7,
        border: "1px solid var(--line)", color: "var(--ink-3)", fontSize: 12.5,
      }}>
        <I.Search size={13} />
        <span>Search…</span>
        <KBD>⌘K</KBD>
      </button>

      <button style={iconBtn} title="Notifications"><I.Bell size={15}/></button>
      <button onClick={onToggleTweaks} style={iconBtn} title="Settings"><I.Settings size={15}/></button>

      <div style={{ display: "flex", alignItems: "center", marginLeft: 4 }}>
        {[
          { i: "RO", c: "oklch(0.6 0.13 30)" },
          { i: "LC", c: "oklch(0.6 0.13 180)" },
          { i: "MP", c: "oklch(0.6 0.13 280)" },
        ].map((a, i) => (
          <div key={i} style={{
            width: 26, height: 26, borderRadius: 99,
            background: a.c, color: "#fff",
            display: "grid", placeItems: "center",
            fontSize: 10, fontWeight: 600,
            border: "2px solid var(--bg)",
            marginLeft: i === 0 ? 0 : -8,
          }}>{a.i}</div>
        ))}
      </div>

      <div style={{ width: 1, height: 20, background: "var(--line)" }} />

      <button style={{
        height: 30, padding: "0 12px", borderRadius: 7,
        background: "var(--accent)", color: "var(--accent-ink)",
        fontSize: 12.5, fontWeight: 500,
        display: "flex", alignItems: "center", gap: 6,
      }}>
        <I.Sparkle size={13} stroke={1.8}/>
        Ask Studio
      </button>
    </header>
  );
}

const iconBtn = {
  width: 30, height: 30, borderRadius: 7,
  display: "grid", placeItems: "center",
  color: "var(--ink-2)",
};

// Command palette (⌘K)
function CommandPalette({ open, onClose, onNav }) {
  const [q, setQ] = useState("");
  const inputRef = useRef(null);
  useEffect(() => { if (open) setTimeout(() => inputRef.current?.focus(), 10); }, [open]);
  if (!open) return null;

  const items = [
    ...FRAMEWORK.metrics.map(m => ({ kind: "metric", id: m.id, label: m.name, sub: m.ref, status: m.status })),
    ...FRAMEWORK.dimensions.map(d => ({ kind: "dimension", id: d.id, label: d.name, sub: d.ref })),
    ...FRAMEWORK.sources.map(s => ({ kind: "source", id: s.id, label: s.name, sub: s.ref })),
  ].filter(i => !q || i.label.toLowerCase().includes(q.toLowerCase()) || i.sub.toLowerCase().includes(q.toLowerCase())).slice(0, 8);

  const actions = [
    { label: "Create new metric", kind: "action", icon: "Plus", run: () => { onNav("wizard"); onClose(); } },
    { label: "Open canvas", kind: "action", icon: "Graph", run: () => { onNav("canvas"); onClose(); } },
    { label: "Open library", kind: "action", icon: "Library", run: () => { onNav("library"); onClose(); } },
  ];

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, zIndex: 100,
      background: "rgba(11,11,12,0.35)", backdropFilter: "blur(4px)",
      display: "grid", placeItems: "start center", paddingTop: "14vh",
      animation: "fadeIn 120ms ease",
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        width: 640, maxWidth: "90vw", background: "var(--panel)",
        borderRadius: 12, border: "1px solid var(--line)", boxShadow: "var(--shadow-lg)",
        overflow: "hidden",
      }}>
        <div style={{ padding: "14px 18px", display: "flex", alignItems: "center", gap: 12, borderBottom: "1px solid var(--line-2)" }}>
          <I.Search size={16} />
          <input ref={inputRef} value={q} onChange={e => setQ(e.target.value)}
                 placeholder="Search metrics, dimensions, sources, or type a command…"
                 style={{ flex: 1, background: "transparent", border: 0, outline: 0, fontSize: 14 }} />
          <KBD>esc</KBD>
        </div>

        <div style={{ maxHeight: 420, overflow: "auto", padding: 8 }}>
          {!q && (
            <>
              <div style={paletteHeader}>Actions</div>
              {actions.map((a, i) => {
                const IC = I[a.icon];
                return (
                  <button key={i} onClick={a.run} style={paletteRow}>
                    <IC size={14}/> <span>{a.label}</span>
                  </button>
                );
              })}
            </>
          )}
          <div style={paletteHeader}>{q ? "Results" : "Recent"}</div>
          {items.map(it => (
            <button key={it.kind + it.id} onClick={onClose} style={paletteRow}>
              {it.kind === "metric" && <I.Metric size={14} />}
              {it.kind === "dimension" && <I.Dim size={14} />}
              {it.kind === "source" && <I.Source size={14} />}
              <span>{it.label}</span>
              <span className="mono" style={{ marginLeft: "auto", color: "var(--ink-4)", fontSize: 11 }}>{it.sub}</span>
              {it.status && <StatusDot status={it.status} />}
            </button>
          ))}
          {q && items.length === 0 && (
            <div style={{ padding: 24, textAlign: "center", color: "var(--ink-3)", fontSize: 13 }}>
              No results for "{q}". <span style={{color:"var(--accent)"}}>Create "{q}" →</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const paletteHeader = {
  padding: "8px 10px 4px",
  fontSize: 10.5, fontWeight: 500, color: "var(--ink-4)",
  textTransform: "uppercase", letterSpacing: "0.08em",
};
const paletteRow = {
  width: "100%", padding: "8px 10px",
  display: "flex", alignItems: "center", gap: 10,
  borderRadius: 7, fontSize: 13, color: "var(--ink)",
  textAlign: "left",
};

Object.assign(window, { Sidebar, Topbar, CommandPalette, Pill, StatusDot, KBD, NAV_ITEMS });
