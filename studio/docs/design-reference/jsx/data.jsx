// Canvas — node graph of the framework
function Canvas({ onOpenDetail }) {
  const [zoom, setZoom] = useState(0.85);
  const [pan, setPan] = useState({ x: 0, y: 20 });
  const [sel, setSel] = useState(null);
  const [hover, setHover] = useState(null);
  const [dragging, setDragging] = useState(false);
  const dragRef = useRef(null);
  const [nodes, setNodes] = useState(GRAPH.nodes);

  const nodeMap = useMemo(() => Object.fromEntries(nodes.map(n => [n.id, n])), [nodes]);

  const onMouseDown = (e) => {
    if (e.target.closest("[data-node]")) return;
    dragRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
    setDragging(true);
  };
  const onMouseMove = (e) => {
    if (dragging && dragRef.current) {
      setPan({ x: e.clientX - dragRef.current.x, y: e.clientY - dragRef.current.y });
    }
  };
  const onMouseUp = () => { setDragging(false); dragRef.current = null; };

  const onWheel = (e) => {
    e.preventDefault();
    const next = Math.max(0.4, Math.min(1.6, zoom - e.deltaY * 0.001));
    setZoom(next);
  };

  const nodeKinds = {
    source:    { bg: "var(--panel)", border: "var(--line)",           accent: "oklch(0.6 0.04 250)", icon: "Source" },
    dimension: { bg: "var(--panel)", border: "var(--line)",           accent: "oklch(0.7 0.1 310)",  icon: "Dim" },
    metric:    { bg: "var(--panel)", border: "var(--line)",           accent: "oklch(0.7 0.1 250)",  icon: "Metric" },
    derived:   { bg: "var(--panel)", border: "var(--accent)",         accent: "var(--accent)",       icon: "Metric" },
    goal:      { bg: "var(--ink)",   border: "var(--ink)",            accent: "var(--bg)",           icon: "Sparkle" },
  };

  const NODE_W = 178, NODE_H = 56;

  const edgePath = (from, to) => {
    const x1 = from.x + NODE_W, y1 = from.y + NODE_H/2;
    const x2 = to.x,             y2 = to.y + NODE_H/2;
    const mx = (x1 + x2) / 2;
    return `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`;
  };

  const isHighlighted = (edge) => {
    if (!sel && !hover) return false;
    const target = sel || hover;
    return edge[0] === target || edge[1] === target;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden", background: "var(--bg-2)" }}>
      {/* Toolbar */}
      <div style={{
        height: 48, flexShrink: 0, padding: "0 var(--pad)",
        display: "flex", alignItems: "center", gap: 8,
        borderBottom: "1px solid var(--line)", background: "var(--bg)",
      }}>
        <button style={ghostSmall}><I.Filter size={12}/> All domains</button>
        <button style={ghostSmall}>Layer: Logical</button>
        <div style={{ width: 1, height: 18, background: "var(--line)" }}/>
        <button style={ghostSmall}><I.Plus size={12}/> Add node</button>
        <button style={ghostSmall}><I.Link size={12}/> Connect</button>
        <div style={{ flex: 1 }}/>
        <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11.5, color: "var(--ink-3)" }} className="mono">
          {Math.round(zoom * 100)}%
        </div>
        <div style={{ display: "flex", border: "1px solid var(--line)", borderRadius: 6, overflow: "hidden" }}>
          <button onClick={() => setZoom(z => Math.max(0.4, z - 0.1))} style={{ padding: "6px 10px", color: "var(--ink-2)" }}>−</button>
          <div style={{ width: 1, background: "var(--line)" }}/>
          <button onClick={() => { setZoom(0.85); setPan({x:0,y:20}); }} style={{ padding: "6px 10px", color: "var(--ink-2)", fontSize: 12 }}>Fit</button>
          <div style={{ width: 1, background: "var(--line)" }}/>
          <button onClick={() => setZoom(z => Math.min(1.6, z + 0.1))} style={{ padding: "6px 10px", color: "var(--ink-2)" }}>+</button>
        </div>
      </div>

      {/* Viewport */}
      <div
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onWheel={onWheel}
        style={{
          flex: 1, position: "relative", overflow: "hidden",
          cursor: dragging ? "grabbing" : "grab",
          backgroundImage: `radial-gradient(circle at 1px 1px, var(--line) 1px, transparent 0)`,
          backgroundSize: `${24 * zoom}px ${24 * zoom}px`,
          backgroundPosition: `${pan.x}px ${pan.y}px`,
        }}
      >
        <div style={{
          position: "absolute", top: 0, left: 0,
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: "0 0",
          width: 1300, height: 700,
        }}>
          {/* Edges */}
          <svg width="1300" height="700" style={{ position: "absolute", inset: 0, pointerEvents: "none", overflow: "visible" }}>
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M0,0 L10,5 L0,10 z" fill="var(--ink-4)"/>
              </marker>
              <marker id="arrow-hl" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M0,0 L10,5 L0,10 z" fill="var(--accent)"/>
              </marker>
            </defs>
            {GRAPH.edges.map(([a, b], i) => {
              const from = nodeMap[a], to = nodeMap[b];
              if (!from || !to) return null;
              const hl = isHighlighted([a, b]);
              return (
                <path key={i} d={edgePath(from, to)}
                      fill="none"
                      stroke={hl ? "var(--accent)" : "var(--ink-4)"}
                      strokeWidth={hl ? 1.5 : 1}
                      opacity={sel || hover ? (hl ? 1 : 0.15) : 0.55}
                      markerEnd={`url(#${hl ? "arrow-hl" : "arrow"})`}
                      style={{ transition: "opacity 160ms, stroke 160ms, stroke-width 160ms" }}/>
              );
            })}
          </svg>

          {/* Nodes */}
          {nodes.map(n => {
            const k = nodeKinds[n.kind];
            const IC = I[k.icon];
            const isSel = sel === n.id;
            const dim = (sel || hover) && !isHighlightedNode(n.id, sel || hover);
            return (
              <div key={n.id} data-node
                   onMouseEnter={() => setHover(n.id)}
                   onMouseLeave={() => setHover(null)}
                   onClick={() => setSel(sel === n.id ? null : n.id)}
                   onDoubleClick={() => n.kind !== "goal" && n.kind !== "source" && onOpenDetail({ ref: n.id, name: n.label })}
                   style={{
                     position: "absolute", left: n.x, top: n.y,
                     width: NODE_W, height: NODE_H,
                     background: n.kind === "goal" ? "var(--ink)" : "var(--panel)",
                     color: n.kind === "goal" ? "var(--bg)" : "var(--ink)",
                     border: `1px solid ${isSel ? "var(--accent)" : k.border}`,
                     borderRadius: 10,
                     boxShadow: isSel ? `0 0 0 3px var(--accent-soft), var(--shadow-md)` : "var(--shadow-sm)",
                     padding: "10px 12px",
                     display: "flex", flexDirection: "column", gap: 3,
                     cursor: "pointer",
                     opacity: dim ? 0.3 : 1,
                     transition: "opacity 160ms, box-shadow 160ms, border-color 160ms",
                   }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{
                    width: 18, height: 18, borderRadius: 5,
                    background: n.kind === "goal" ? "rgba(255,255,255,0.1)" : k.accent + "20",
                    color: n.kind === "goal" ? "var(--bg)" : k.accent,
                    display: "grid", placeItems: "center",
                  }}><IC size={11}/></span>
                  <span style={{ fontSize: 12.5, fontWeight: 500, letterSpacing: "-0.005em" }}>{n.label}</span>
                </div>
                <span className="mono" style={{ fontSize: 10, color: n.kind === "goal" ? "rgba(255,255,255,0.5)" : "var(--ink-4)", marginLeft: 24 }}>
                  {n.sub}
                </span>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div style={{
          position: "absolute", left: 20, bottom: 20,
          background: "var(--panel)", border: "1px solid var(--line)",
          borderRadius: 10, padding: "12px 14px",
          display: "flex", flexDirection: "column", gap: 6,
          fontSize: 11.5, boxShadow: "var(--shadow-sm)",
        }}>
          <div style={{ fontSize: 10.5, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 2 }}>Legend</div>
          {[
            ["Source", "Source"], ["Dimension", "Dim"], ["Metric", "Metric"], ["Derived", "Metric"], ["North star", "Sparkle"],
          ].map(([l, ic]) => {
            const IC = I[ic];
            return (
              <div key={l} style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--ink-2)" }}>
                <IC size={12} stroke={1.3}/><span>{l}</span>
              </div>
            );
          })}
        </div>

        {/* Inspector */}
        {sel && nodeMap[sel] && (
          <div style={{
            position: "absolute", right: 20, top: 20, bottom: 20,
            width: 320, background: "var(--panel)",
            border: "1px solid var(--line)", borderRadius: 12,
            boxShadow: "var(--shadow-md)",
            display: "flex", flexDirection: "column",
            overflow: "hidden",
          }}>
            <div style={{ padding: "16px 18px", borderBottom: "1px solid var(--line-2)", display: "flex", alignItems: "flex-start", gap: 10 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: "var(--ink-3)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{nodeMap[sel].kind}</div>
                <div style={{ fontSize: 16, fontWeight: 500, marginTop: 4, letterSpacing: "-0.01em" }}>{nodeMap[sel].label}</div>
                <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)", marginTop: 4 }}>{nodeMap[sel].id}</div>
              </div>
              <button onClick={() => setSel(null)} style={iconBtn}><I.X size={13}/></button>
            </div>
            <div style={{ padding: "16px 18px", display: "flex", flexDirection: "column", gap: 14, fontSize: 12.5 }}>
              <InspectorRow label="Description" value="The definitive measure of recurring revenue, aggregated daily from billing events."/>
              <InspectorRow label="Owner" value="R. Okafor"/>
              <InspectorRow label="Dependencies" value={`${GRAPH.edges.filter(e => e[1] === sel).length} inputs · ${GRAPH.edges.filter(e => e[0] === sel).length} outputs`}/>
              <InspectorRow label="Last updated" value="2h ago"/>
            </div>
            <div style={{ padding: 14, marginTop: "auto", borderTop: "1px solid var(--line-2)", display: "flex", gap: 6 }}>
              <button onClick={() => onOpenDetail({ ref: sel, name: nodeMap[sel].label })} style={{ ...ghostBtn, flex: 1, justifyContent: "center" }}>
                <I.Eye size={12}/> Open
              </button>
              <button style={{ ...primaryBtn, flex: 1, justifyContent: "center" }}>
                <I.Edit size={12}/> Edit
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function InspectorRow({ label, value }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <div style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
      <div style={{ color: "var(--ink-2)", lineHeight: 1.5 }}>{value}</div>
    </div>
  );
}

function isHighlightedNode(id, target) {
  if (id === target) return true;
  return GRAPH.edges.some(e => (e[0] === target && e[1] === id) || (e[1] === target && e[0] === id));
}

Object.assign(window, { Canvas });
