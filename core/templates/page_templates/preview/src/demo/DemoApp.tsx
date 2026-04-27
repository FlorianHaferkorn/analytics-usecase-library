// ============================================================================
// DemoApp — Phase 1 smoke test.
// ============================================================================
// Proves the token + grid foundation works:
//   - Canvas size switchable between HD / FHD / QHD presets
//   - Density switch (dense / balanced / airy) changes real spacing
//   - Theme toggle light/dark
//   - Zoom slider re-scales typography
//   - Four demo slots prove slotPos() produces a clean non-overlapping layout
// ============================================================================

import { useState } from "react";
import { Canvas, Slot } from "../grid/index.js";
import {
  CANVAS,
  tokensController,
  type DensityMode,
  type ThemeMode,
} from "../tokens/tokens.js";
import "./demo.css";

type CanvasPreset = keyof typeof CANVAS.PRESETS;

export function DemoApp(): JSX.Element {
  const [density, setDensityState] = useState<DensityMode>("balanced");
  const [theme, setThemeState] = useState<ThemeMode>("light");
  const [preset, setPresetState] = useState<CanvasPreset>("hd");
  const [scale, setScaleState] = useState<number>(1);
  const [anatomy, setAnatomy] = useState<boolean>(true);

  const applyDensity = (d: DensityMode): void => {
    tokensController.setDensity(d);
    setDensityState(d);
  };
  const applyTheme = (t: ThemeMode): void => {
    tokensController.setTheme(t);
    setThemeState(t);
  };
  const applyPreset = (p: CanvasPreset): void => {
    tokensController.setCanvasPreset(p);
    setPresetState(p);
  };
  const applyScale = (s: number): void => {
    tokensController.setScale(s);
    setScaleState(s);
  };

  return (
    <div className="demo-shell">
      <header className="demo-header">
        <h1 className="demo-title">Page Template Preview v2 · Phase 1 Smoke Test</h1>
        <p className="demo-sub">
          Tokens &rarr; Grid &rarr; Slot API. Change any control — layout reflows
          through CSS variables, no React re-render.
        </p>
      </header>

      <section className="demo-controls">
        <ControlGroup label="Density">
          {(["dense", "balanced", "airy"] as const).map((d) => (
            <button
              key={d}
              className={`btn ${density === d ? "btn--active" : ""}`}
              onClick={() => applyDensity(d)}
            >
              {d}
            </button>
          ))}
        </ControlGroup>

        <ControlGroup label="Theme">
          {(["light", "dark"] as const).map((t) => (
            <button
              key={t}
              className={`btn ${theme === t ? "btn--active" : ""}`}
              onClick={() => applyTheme(t)}
            >
              {t}
            </button>
          ))}
        </ControlGroup>

        <ControlGroup label="Canvas">
          {(
            ["hd", "fhd", "qhd", "a4_landscape"] as const
          ).map((p) => (
            <button
              key={p}
              className={`btn ${preset === p ? "btn--active" : ""}`}
              onClick={() => applyPreset(p)}
            >
              {p} ({CANVAS.PRESETS[p].w}&times;{CANVAS.PRESETS[p].h})
            </button>
          ))}
        </ControlGroup>

        <ControlGroup label={`Zoom ${scale.toFixed(2)}x`}>
          <input
            type="range"
            min={0.5}
            max={2}
            step={0.05}
            value={scale}
            onChange={(e) => applyScale(Number(e.target.value))}
          />
        </ControlGroup>

        <ControlGroup label="Anatomy">
          <button
            className={`btn ${anatomy ? "btn--active" : ""}`}
            onClick={() => setAnatomy((a) => !a)}
          >
            {anatomy ? "on" : "off"}
          </button>
        </ControlGroup>
      </section>

      <main className="demo-stage">
        <Canvas anatomy={anatomy}>
          <Slot col={0} row={0} cs={12} rs={1.8} slotId="Header" label="Header">
            <DemoBox title="Header · KPI band placeholder" />
          </Slot>

          <Slot col={0} row={2} cs={2} rs={10} slotId="Sidebar" label="Sidebar">
            <DemoBox title="Sidebar · slicer pane (cs=2, rs=10)" />
          </Slot>

          <Slot col={2} row={2} cs={8} rs={7} slotId="Main" label="Main content">
            <DemoBox title="Main · content area (cs=8, rs=7)" />
          </Slot>

          <Slot col={10} row={2} cs={2} rs={10} slotId="Action" label="Action panel">
            <DemoBox title="Action · panel (cs=2, rs=10)" />
          </Slot>

          <Slot col={2} row={9} cs={8} rs={3} slotId="Footer" label="Footer">
            <DemoBox title="Footer · narrative (cs=8, rs=3)" />
          </Slot>
        </Canvas>
      </main>
    </div>
  );
}

function ControlGroup({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <div className="ctrl-group">
      <span className="ctrl-label">{label}</span>
      <div className="ctrl-body">{children}</div>
    </div>
  );
}

function DemoBox({ title }: { title: string }): JSX.Element {
  return <div className="demo-box">{title}</div>;
}
