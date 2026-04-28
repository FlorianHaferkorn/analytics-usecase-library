// Library — catalog of framework elements
function Library({ onOpenDetail }) {
  const [tab, setTab] = useState("metrics");
  const [q, setQ] = useState("");
  const [domain, setDomain] = useState("all");

  const tabs = [
    { id: "metrics",    label: "Metrics",    count: FRAMEWORK.metrics.length, icon: "Metric" },
    { id: "dimensions", label: "Dimensions", count: FRAMEWORK.dimensions.length, icon: "Dim" },
    { id: "sources",    label: "Sources",    count: FRAMEWORK.sources.length, icon: "Source" },
  ];

  const rows = tab === "metrics" ? FRAMEWORK.metrics
             : tab === "dimensions" ? FRAMEWORK.dimensions
             : FRAMEWORK.sources;

  const filtered = rows.filter(r => {
    if (q && !(`${r.name} ${r.ref}`).toLowerCase().includes(q.toLowerCase())) return false;
    if (tab === "metrics" && domain !== "all" && r.domain !== domain) return false;
    return true;
  });

  return (
    <div style={{ padding: "var(--pad)", maxWidth: 1400, margin: "0 auto", width: "100%" }}>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <h1 className="display" style={{ fontSize: 28, margin: 0, letterSpacing: "-0.02em", fontWeight: 500 }}>Library</h1>
          <div style={{ color: "var(--ink-3)", fontSize: 13, marginTop: 4 }}>
            The single source of truth for every metric, dimension and source.
          </div>
        </div>
        <button style={primaryBtn}><I.Plus size={14}/> New metric</button>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 2, borderBottom: "1px solid var(--line)", marginBottom: 16 }}>
        {tabs.map(t => {
          const IC = I[t.icon];
          const active = tab === t.id;
          return (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              padding: "10px 14px", display: "flex", alignItems: "center", gap: 8,
              fontSize: 13, color: active ? "var(--ink)" : "var(--ink-3)",
              fontWeight: active ? 500 : 400,
              borderBottom: `1.5px solid ${active ? "var(--accent)" : "transparent"}`,
              marginBottom: -1,
            }}>
              <IC size={13}/>
              {t.label}
              <span className="mono" style={{ fontSize: 10.5, color: "var(--ink-4)" }}>{t.count}</span>
            </button>
          );
        })}
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 8, marginBottom: 14, alignItems: "center" }}>
        <div style={{
          flex: 1, height: 34, padding: "0 12px",
          display: "flex", alignItems: "center", gap: 10,
          border: "1px solid var(--line)", borderRadius: 8,
          background: "var(--panel)",
        }}>
          <I.Search size={13}/>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder={`Search ${tab}…`}
                 style={{ flex: 1, background: "transparent", border: 0, outline: 0, fontSize: 13 }}/>
          <KBD>/</KBD>
        </div>
        {tab === "metrics" && (
          <select value={domain} onChange={e => setDomain(e.target.value)} style={selectStyle}>
            <option value="all">All domains</option>
            {FRAMEWORK.domains.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        )}
        <button style={ghostBtn}><I.Filter size={13}/> Filter</button>
      </div>

      {/* Table */}
      <div style={{ ...card }}>
        {tab === "metrics" && (
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Name</th>
                <th style={thStyle}>Ref</th>
                <th style={thStyle}>Type</th>
                <th style={thStyle}>Domain</th>
                <th style={thStyle}>Owner</th>
                <th style={thStyle}>Grain</th>
                <th style={thStyle}>Deps</th>
                <th style={thStyle}>Updated</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((m, i) => {
                const d = FRAMEWORK.domains.find(x => x.id === m.domain);
                return (
                  <tr key={m.id} onClick={() => onOpenDetail(m)} style={rowStyle}>
                    <td style={{ ...tdStyle, fontWeight: 500 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <StatusDot status={m.status}/>
                        {m.name}
                        <Pill tone={m.status === "certified" ? "positive" : m.status === "review" ? "warn" : "draft"}>{m.status}</Pill>
                      </div>
                    </td>
                    <td style={{ ...tdStyle, color: "var(--ink-3)" }} className="mono">{m.ref}</td>
                    <td style={tdStyle}>{m.type}</td>
                    <td style={tdStyle}>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                        <span style={{ width: 6, height: 6, borderRadius: 2, background: `oklch(0.7 0.1 ${d.color})` }}/>
                        {d.name}
                      </span>
                    </td>
                    <td style={tdStyle}>{m.owner}</td>
                    <td style={tdStyle}>{m.grain}</td>
                    <td style={{ ...tdStyle, color: "var(--ink-3)" }} className="mono">{m.deps}</td>
                    <td style={{ ...tdStyle, color: "var(--ink-3)" }}>{m.updated}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        {tab === "dimensions" && (
          <table style={tableStyle}>
            <thead><tr>
              <th style={thStyle}>Name</th><th style={thStyle}>Ref</th>
              <th style={thStyle}>Source</th><th style={thStyle}>Cardinality</th>
            </tr></thead>
            <tbody>
              {filtered.map(d => (
                <tr key={d.id} style={rowStyle}>
                  <td style={{ ...tdStyle, fontWeight: 500 }}>{d.name}</td>
                  <td style={{ ...tdStyle, color: "var(--ink-3)" }} className="mono">{d.ref}</td>
                  <td style={tdStyle}>{d.source}</td>
                  <td style={{ ...tdStyle, color: "var(--ink-3)" }} className="mono">{d.cardinality}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {tab === "sources" && (
          <table style={tableStyle}>
            <thead><tr>
              <th style={thStyle}>Name</th><th style={thStyle}>Ref</th>
              <th style={thStyle}>Rows</th><th style={thStyle}>Last sync</th>
            </tr></thead>
            <tbody>
              {filtered.map(s => (
                <tr key={s.id} style={rowStyle}>
                  <td style={{ ...tdStyle, fontWeight: 500 }}>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
                      <StatusDot status="certified"/> {s.name}
                    </span>
                  </td>
                  <td style={{ ...tdStyle, color: "var(--ink-3)" }} className="mono">{s.ref}</td>
                  <td style={{ ...tdStyle, color: "var(--ink-3)" }} className="mono">{s.rows}</td>
                  <td style={tdStyle}>{s.lastSync}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 13 };
const thStyle = {
  textAlign: "left", fontWeight: 500, fontSize: 11,
  color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em",
  padding: "12px var(--pad)", borderBottom: "1px solid var(--line)",
};
const tdStyle = { padding: "14px var(--pad)", borderBottom: "1px solid var(--line-2)" };
const rowStyle = { cursor: "pointer", transition: "background 120ms" };

const selectStyle = {
  height: 34, padding: "0 10px", borderRadius: 8,
  border: "1px solid var(--line)", background: "var(--panel)",
  fontSize: 13, color: "var(--ink)",
};

Object.assign(window, { Library });
