// ============================================================================
// <PageShell> — chrome around any template page.
// ============================================================================
// Provides the same density/theme/canvas/zoom/anatomy controls as DemoApp
// but lets you switch which *page* is mounted inside the canvas.
// ============================================================================

import { useState } from "react";
import { CANVAS, tokensController, type DensityMode, type ThemeMode } from "../tokens/tokens.js";
import {
  T1Strategic,
  T1_META,
  T2Tactical,
  T2_META,
  T3Operational,
  T3_META,
  T4Prescriptive,
  T4_META,
} from "../pages/index.js";
import "../demo/demo.css";
import "./page-shell.css";

type CanvasPreset = keyof typeof CANVAS.PRESETS;

type PageKey = "T1" | "T2" | "T3" | "T4";

interface PageEntry {
  key: PageKey;
  meta: { id: string; name: string; description: string };
  Component: () => JSX.Element;
}

const PAGES: PageEntry[] = [
  { key: "T1", meta: T1_META, Component: T1Strategic },
  { key: "T2", meta: T2_META, Component: T2Tactical },
  { key: "T3", meta: T3_META, Component: T3Operational },
  { key: "T4", meta: T4_META, Component: T4Prescriptive },
];

export function PageShell(): JSX.Element {
  const [pageKey, setPageKey] = useState<PageKey>("T1");
  const [density, setDensityState] = useState<DensityMode>("balanced");
  const [theme, setThemeState] = useState<ThemeMode>("light");
  const [preset, setPresetState] = useState<CanvasPreset>("hd");
  const [scale, setScaleState] = useState<number>(1);
  const [anatomy, setAnatomy] = useState<boolean>(false);

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

  const active = PAGES.find((p) => p.key === pageKey) ?? PAGES[0]!;
  const ActivePage = active.Component;

  return (
    <div className="demo-shell" data-anatomy={anatomy ? "on" : "off"}>
      <header className="demo-header">
        <h1 className="demo-title">Page Template Preview · Phase 2</h1>
        <p className="demo-sub">
          Token-driven page templates T1–T4. Switch page, density, theme,
          canvas size and zoom — all layout flows through CSS variables.
        </p>
      </header>

      <section className="demo-controls">
        <ControlGroup label="Page">
          {PAGES.map((p) => (
            <button
              key={p.key}
              className={`btn ${pageKey === p.key ? "btn--active" : ""}`}
              onClick={() => setPageKey(p.key)}
              title={p.meta.description}
            >
              {p.meta.id} · {p.meta.name}
            </button>
          ))}
        </ControlGroup>

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
          {(["hd", "fhd", "qhd", "a4_landscape"] as const).map((p) => (
            <button
              key={p}
              className={`btn ${preset === p ? "btn--active" : ""}`}
              onClick={() => applyPreset(p)}
            >
              {p}
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

      <section className="page-shell__meta">
        <span className="page-shell__meta-id">{active.meta.id}</span>
        <span className="page-shell__meta-name">{active.meta.name}</span>
        <span className="page-shell__meta-desc">{active.meta.description}</span>
      </section>

      <main className="demo-stage">
        <ActivePage />
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
