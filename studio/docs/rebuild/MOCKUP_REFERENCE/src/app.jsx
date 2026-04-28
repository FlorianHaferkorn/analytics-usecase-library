// App — root component, routing, tweaks state, Tweaks host protocol
function App() {
  const [tweaks, setTweaks] = useState(window.__TWEAKS__);
  const [route, setRoute] = useState("dashboard");
  const [detailMetric, setDetailMetric] = useState(null);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [tweaksOpen, setTweaksOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(tweaks.sidebar === "collapsed");

  useEffect(() => { setSidebarCollapsed(tweaks.sidebar === "collapsed"); }, [tweaks.sidebar]);

  // Apply tweaks to root element
  useEffect(() => {
    const r = document.documentElement;
    r.dataset.theme = tweaks.theme;
    r.dataset.density = tweaks.density;
    r.dataset.fonts = tweaks.fontPairing;
    r.style.setProperty("--accent", `oklch(${tweaks.accentLightness ?? 0.62} ${tweaks.accentChroma ?? 0.13} ${tweaks.accentHue})`);
    r.style.setProperty("--accent-soft", `oklch(${tweaks.accentLightness ?? 0.62} ${tweaks.accentChroma ?? 0.13} ${tweaks.accentHue} / 0.14)`);
    r.style.setProperty("--accent-ink", tweaks.theme === "dark" ? `oklch(0.12 0.02 ${tweaks.accentHue})` : `oklch(0.98 0.01 ${tweaks.accentHue})`);
  }, [tweaks]);

  const setTweak = useCallback((k, v) => {
    setTweaks(t => {
      const next = { ...t, [k]: v };
      // persist
      window.parent?.postMessage({ type: "__edit_mode_set_keys", edits: { [k]: v } }, "*");
      return next;
    });
  }, []);

  // Edit mode protocol
  useEffect(() => {
    const onMsg = (e) => {
      if (e.data?.type === "__activate_edit_mode")   { setEditMode(true); setTweaksOpen(true); }
      if (e.data?.type === "__deactivate_edit_mode") { setEditMode(false); setTweaksOpen(false); }
    };
    window.addEventListener("message", onMsg);
    window.parent?.postMessage({ type: "__edit_mode_available" }, "*");
    return () => window.removeEventListener("message", onMsg);
  }, []);

  // Keybinds
  useEffect(() => {
    const onKey = (e) => {
      const mod = e.metaKey || e.ctrlKey;
      if (mod && e.key.toLowerCase() === "k") { e.preventDefault(); setCmdOpen(o => !o); }
      else if (e.key.toLowerCase() === "n" && !e.target.matches("input,textarea")) { setWizardOpen(true); }
      else if (e.key === "Escape") { setCmdOpen(false); setWizardOpen(false); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const openDetail = (m) => { setDetailMetric(m); setRoute("detail"); };

  return (
    <div style={{ height: "100vh", display: "flex", overflow: "hidden" }}>
      <Sidebar route={route} setRoute={setRoute}
               collapsed={sidebarCollapsed}
               setCollapsed={(v) => { setSidebarCollapsed(v); setTweak("sidebar", v ? "collapsed" : "expanded"); }}
               onNew={() => setWizardOpen(true)}
               onCmd={() => setCmdOpen(true)}/>

      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0, background: "var(--bg)" }}>
        <Topbar route={route}
                onCmd={() => setCmdOpen(true)}
                onToggleTweaks={() => setTweaksOpen(o => !o)}/>
        <div style={{ flex: 1, overflow: "auto" }}>
          {route === "dashboard" && <Dashboard onOpenDetail={openDetail}/>}
          {route === "canvas"    && <Canvas onOpenDetail={openDetail}/>}
          {route === "library"   && <Library onOpenDetail={openDetail}/>}
          {route === "detail"    && <Detail metric={detailMetric} onBack={() => setRoute("library")}/>}
        </div>
      </main>

      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} onNav={setRoute}/>
      <Wizard open={wizardOpen} onClose={() => setWizardOpen(false)}/>
      <Tweaks open={tweaksOpen} onClose={() => setTweaksOpen(false)} tweaks={tweaks} setTweak={setTweak}/>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
