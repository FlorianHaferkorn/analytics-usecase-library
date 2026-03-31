"use client";
import { useState } from "react";
import { Button } from "@/components/ui/Button";

interface BrandConfig {
  brand_name: string;
  primary_color: string;
  secondary_color: string;
  positive_color: string;
  negative_color: string;
  warning_color: string;
  neutral_color: string;
  font_family: string;
  font_heading: string;
  font_mono: string;
  base_size: number;
  heading_weight: number;
  border_radius: number;
  mode: "light" | "dark" | "both";
}

const DEFAULT: BrandConfig = {
  brand_name: "ActionReady",
  primary_color: "#47D7AC",
  secondary_color: "#06041F",
  positive_color: "#16A34A",
  negative_color: "#DC2626",
  warning_color: "#D97706",
  neutral_color: "#8893A5",
  font_family: "Inter",
  font_heading: "Inter",
  font_mono: "JetBrains Mono",
  base_size: 14,
  heading_weight: 600,
  border_radius: 6,
  mode: "both",
};

const FONT_OPTIONS = [
  "Inter", "Segoe UI", "Roboto", "DM Sans", "Nunito Sans", "Source Sans 3",
  "Poppins", "Open Sans", "Lato", "Montserrat", "Work Sans", "IBM Plex Sans",
];

function ColorField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex items-center gap-2">
      <input type="color" value={value} onChange={(e) => onChange(e.target.value)}
        className="w-8 h-8 rounded border border-theme cursor-pointer p-0.5 bg-transparent" />
      <div className="flex-1 min-w-0">
        <label className="block text-[10px] text-theme-tertiary">{label}</label>
        <input type="text" value={value} onChange={(e) => onChange(e.target.value)}
          className="text-xs font-mono border border-theme rounded px-2 py-0.5 w-24 bg-theme-secondary text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint" />
      </div>
    </div>
  );
}

/* ---------- Mock Report Preview Components ---------- */

function KpiCard({ label, value, trend, color, config }: {
  label: string; value: string; trend: string; color: string; config: BrandConfig;
}) {
  return (
    <div className="p-3 rounded border" style={{
      borderColor: config.secondary_color + "20",
      borderRadius: config.border_radius,
      fontFamily: config.font_family,
    }}>
      <div className="text-[10px] opacity-60" style={{ color: config.secondary_color }}>{label}</div>
      <div className="text-xl font-bold mt-0.5" style={{ fontWeight: config.heading_weight, color: config.secondary_color }}>
        {value}
      </div>
      <div className="text-xs font-mono mt-0.5" style={{ color }}>{trend}</div>
    </div>
  );
}

function T1Preview({ config, bg }: { config: BrandConfig; bg: string }) {
  return (
    <div className="rounded-lg border overflow-hidden" style={{ borderColor: config.secondary_color + "15", borderRadius: config.border_radius }}>
      <div className="px-4 py-2 flex items-center justify-between" style={{ backgroundColor: config.secondary_color, color: "#fff" }}>
        <div>
          <div className="text-[10px] opacity-70" style={{ fontFamily: config.font_family }}>T1 Strategic Overview</div>
          <div className="text-sm font-semibold" style={{ fontFamily: config.font_heading, fontWeight: config.heading_weight }}>
            Revenue Performance
          </div>
        </div>
        <div className="text-[10px] opacity-50">3-second signal</div>
      </div>
      <div className="p-4 space-y-3" style={{ backgroundColor: bg, fontFamily: config.font_family, fontSize: config.base_size }}>
        {/* Big Number */}
        <div className="text-center py-3">
          <div className="text-3xl font-bold" style={{ color: config.secondary_color, fontWeight: config.heading_weight }}>
            $12.4M
          </div>
          <div className="text-xs mt-1" style={{ color: config.positive_color }}>
            +8.2% vs. target
          </div>
        </div>
        {/* KPI Row */}
        <div className="grid grid-cols-3 gap-2">
          <KpiCard label="Net Sales" value="$12.4M" trend="+8.2%" color={config.positive_color} config={config} />
          <KpiCard label="Gross Margin" value="34.2%" trend="-1.1pp" color={config.negative_color} config={config} />
          <KpiCard label="DSO" value="48 days" trend="at risk" color={config.warning_color} config={config} />
        </div>
      </div>
    </div>
  );
}

function T2Preview({ config, bg }: { config: BrandConfig; bg: string }) {
  return (
    <div className="rounded-lg border overflow-hidden" style={{ borderColor: config.secondary_color + "15", borderRadius: config.border_radius }}>
      <div className="px-4 py-2 flex items-center justify-between" style={{ backgroundColor: config.secondary_color, color: "#fff" }}>
        <div>
          <div className="text-[10px] opacity-70" style={{ fontFamily: config.font_family }}>T2 Tactical Variance</div>
          <div className="text-sm font-semibold" style={{ fontFamily: config.font_heading, fontWeight: config.heading_weight }}>
            Margin Analysis
          </div>
        </div>
        <div className="text-[10px] opacity-50">30-second diagnosis</div>
      </div>
      <div className="p-4 space-y-3" style={{ backgroundColor: bg, fontFamily: config.font_family, fontSize: config.base_size }}>
        {/* Variance bars */}
        <div className="space-y-2">
          {[
            { label: "Region North", val: 38, delta: "+2.1pp", color: config.positive_color },
            { label: "Region South", val: 31, delta: "-3.4pp", color: config.negative_color },
            { label: "Region West", val: 35, delta: "+0.2pp", color: config.positive_color },
            { label: "Region East", val: 28, delta: "-5.8pp", color: config.negative_color },
          ].map((r) => (
            <div key={r.label} className="flex items-center gap-2 text-xs">
              <span className="w-20 shrink-0" style={{ color: config.secondary_color }}>{r.label}</span>
              <div className="flex-1 h-4 rounded-sm overflow-hidden" style={{ backgroundColor: config.neutral_color + "20", borderRadius: config.border_radius / 2 }}>
                <div className="h-full" style={{ width: `${r.val * 2.5}%`, backgroundColor: config.primary_color + "80", borderRadius: config.border_radius / 2 }} />
              </div>
              <span className="text-[10px] font-mono w-14 text-right" style={{ color: r.color }}>{r.delta}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function T3Preview({ config, bg }: { config: BrandConfig; bg: string }) {
  return (
    <div className="rounded-lg border overflow-hidden" style={{ borderColor: config.secondary_color + "15", borderRadius: config.border_radius }}>
      <div className="px-4 py-2 flex items-center justify-between" style={{ backgroundColor: config.secondary_color, color: "#fff" }}>
        <div>
          <div className="text-[10px] opacity-70" style={{ fontFamily: config.font_family }}>T3 Operational Monitoring</div>
          <div className="text-sm font-semibold" style={{ fontFamily: config.font_heading, fontWeight: config.heading_weight }}>
            Production OEE
          </div>
        </div>
        <div className="text-[10px] opacity-50">real-time</div>
      </div>
      <div className="p-4" style={{ backgroundColor: bg, fontFamily: config.font_family, fontSize: config.base_size }}>
        <table className="w-full text-xs">
          <thead>
            <tr style={{ color: config.neutral_color }}>
              <th className="text-left py-1 font-medium">Line</th>
              <th className="text-right py-1 font-medium">OEE</th>
              <th className="text-right py-1 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              { line: "Line A", oee: "87%", status: "OK", sColor: config.positive_color },
              { line: "Line B", oee: "72%", status: "Warning", sColor: config.warning_color },
              { line: "Line C", oee: "91%", status: "OK", sColor: config.positive_color },
              { line: "Line D", oee: "58%", status: "Critical", sColor: config.negative_color },
            ].map((r) => (
              <tr key={r.line} style={{ borderTop: `1px solid ${config.neutral_color}15` }}>
                <td className="py-1.5" style={{ color: config.secondary_color }}>{r.line}</td>
                <td className="text-right font-mono" style={{ color: config.secondary_color }}>{r.oee}</td>
                <td className="text-right">
                  <span className="text-[10px] px-1.5 py-0.5 rounded" style={{
                    backgroundColor: r.sColor + "15",
                    color: r.sColor,
                    borderRadius: config.border_radius / 2,
                  }}>{r.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function T4Preview({ config, bg }: { config: BrandConfig; bg: string }) {
  return (
    <div className="rounded-lg border overflow-hidden" style={{ borderColor: config.secondary_color + "15", borderRadius: config.border_radius }}>
      <div className="px-4 py-2 flex items-center justify-between" style={{ backgroundColor: config.secondary_color, color: "#fff" }}>
        <div>
          <div className="text-[10px] opacity-70" style={{ fontFamily: config.font_family }}>T4 Prescriptive Recommendation</div>
          <div className="text-sm font-semibold" style={{ fontFamily: config.font_heading, fontWeight: config.heading_weight }}>
            Collection Actions
          </div>
        </div>
        <div className="text-[10px] opacity-50">300-second action</div>
      </div>
      <div className="p-4 space-y-2" style={{ backgroundColor: bg, fontFamily: config.font_family, fontSize: config.base_size }}>
        {[
          { customer: "Acme Corp", dso: "67 days", amount: "$234K", severity: "L3" },
          { customer: "Beta Inc", dso: "52 days", amount: "$189K", severity: "L2" },
          { customer: "Gamma Ltd", dso: "48 days", amount: "$156K", severity: "L1" },
        ].map((r) => (
          <div key={r.customer} className="flex items-center gap-3 text-xs p-2 rounded" style={{
            backgroundColor: config.neutral_color + "08",
            borderRadius: config.border_radius,
          }}>
            <div className="flex-1">
              <div className="font-medium" style={{ color: config.secondary_color }}>{r.customer}</div>
              <div className="text-[10px]" style={{ color: config.neutral_color }}>DSO: {r.dso} | AR: {r.amount}</div>
            </div>
            <span className="text-[10px] px-1.5 py-0.5 rounded font-medium" style={{
              backgroundColor: r.severity === "L3" ? config.negative_color + "15" : r.severity === "L2" ? config.warning_color + "15" : config.positive_color + "15",
              color: r.severity === "L3" ? config.negative_color : r.severity === "L2" ? config.warning_color : config.positive_color,
              borderRadius: config.border_radius / 2,
            }}>{r.severity}</span>
            <button className="text-[10px] px-2 py-1 rounded font-medium" style={{
              backgroundColor: config.primary_color,
              color: config.secondary_color,
              borderRadius: config.border_radius / 2,
            }}>
              Act
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- Main ---------- */

export default function BrandPage() {
  const [config, setConfig] = useState<BrandConfig>(DEFAULT);
  const [saved, setSaved] = useState(false);
  const [previewTab, setPreviewTab] = useState<"T1" | "T2" | "T3" | "T4">("T1");

  function set<K extends keyof BrandConfig>(key: K) {
    return (v: BrandConfig[K]) => {
      setConfig((c) => ({ ...c, [key]: v }));
      setSaved(false);
    };
  }

  function generateYaml() {
    return `brand_id: ${config.brand_name.toLowerCase().replace(/\s+/g, "_")}
brand_name: "${config.brand_name}"
schema_version: "1.0"
approval_status: draft

color:
  primary: "${config.primary_color}"
  secondary: "${config.secondary_color}"
  signals:
    positive: { color: "${config.positive_color}", icon: "\\u25B2" }
    negative: { color: "${config.negative_color}", icon: "\\u25BC" }
    warning:  { color: "${config.warning_color}", icon: "\\u25C6" }
    neutral:  { color: "${config.neutral_color}", icon: "\\u25CF" }
  mode: ${config.mode}

typography:
  font_family: "${config.font_family}"
  font_heading: "${config.font_heading}"
  font_mono: "${config.font_mono}"
  base_size_px: ${config.base_size}
  heading_weight: ${config.heading_weight}

layout:
  border_radius_px: ${config.border_radius}
`;
  }

  function handleDownload() {
    const blob = new Blob([generateYaml()], { type: "text/yaml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${config.brand_name.toLowerCase().replace(/\s+/g, "_")}_brand.yaml`;
    a.click();
    URL.revokeObjectURL(url);
    setSaved(true);
  }

  const previewBg = config.mode === "dark" ? config.secondary_color + "08" : "#FFFFFF";

  return (
    <div className="h-full flex overflow-hidden">
      {/* Left: Controls */}
      <div className="w-80 shrink-0 border-r border-theme bg-theme overflow-y-auto">
        <div className="p-4 space-y-5">
          <div>
            <h1 className="text-base font-semibold text-theme">Brand Designer</h1>
            <p className="text-xs text-theme-tertiary mt-0.5">
              Configure brand tokens and preview on page templates.
            </p>
          </div>

          {/* Identity */}
          <div>
            <h2 className="text-[10px] font-semibold text-theme-tertiary uppercase tracking-wider mb-2">Identity</h2>
            <input type="text" value={config.brand_name} onChange={(e) => set("brand_name")(e.target.value)}
              className="border border-theme rounded px-3 py-1.5 text-sm bg-theme-secondary text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint w-full" />
          </div>

          {/* Colors */}
          <div>
            <h2 className="text-[10px] font-semibold text-theme-tertiary uppercase tracking-wider mb-2">Colors</h2>
            <div className="space-y-2">
              <ColorField label="Primary (accent)" value={config.primary_color} onChange={set("primary_color")} />
              <ColorField label="Secondary (text)" value={config.secondary_color} onChange={set("secondary_color")} />
              <div className="border-t border-theme pt-2 mt-2">
                <div className="text-[10px] text-theme-tertiary mb-1.5">Signal Colors</div>
                <div className="space-y-2">
                  <ColorField label="Positive" value={config.positive_color} onChange={set("positive_color")} />
                  <ColorField label="Negative" value={config.negative_color} onChange={set("negative_color")} />
                  <ColorField label="Warning" value={config.warning_color} onChange={set("warning_color")} />
                  <ColorField label="Neutral" value={config.neutral_color} onChange={set("neutral_color")} />
                </div>
              </div>
            </div>
          </div>

          {/* Typography */}
          <div>
            <h2 className="text-[10px] font-semibold text-theme-tertiary uppercase tracking-wider mb-2">Typography</h2>
            <div className="space-y-2">
              <div>
                <label className="text-[10px] text-theme-tertiary block mb-0.5">Body Font</label>
                <select value={config.font_family} onChange={(e) => set("font_family")(e.target.value)}
                  className="w-full text-xs border border-theme rounded px-2 py-1.5 bg-theme-secondary text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint">
                  {FONT_OPTIONS.map((f) => <option key={f} value={f}>{f}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-theme-tertiary block mb-0.5">Heading Font</label>
                <select value={config.font_heading} onChange={(e) => set("font_heading")(e.target.value)}
                  className="w-full text-xs border border-theme rounded px-2 py-1.5 bg-theme-secondary text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint">
                  {FONT_OPTIONS.map((f) => <option key={f} value={f}>{f}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-theme-tertiary block mb-0.5">Base Size: {config.base_size}px</label>
                <input type="range" min={10} max={18} value={config.base_size}
                  onChange={(e) => set("base_size")(Number(e.target.value))}
                  className="w-full accent-brand-mint" />
              </div>
              <div>
                <label className="text-[10px] text-theme-tertiary block mb-0.5">Heading Weight: {config.heading_weight}</label>
                <input type="range" min={400} max={900} step={100} value={config.heading_weight}
                  onChange={(e) => set("heading_weight")(Number(e.target.value))}
                  className="w-full accent-brand-mint" />
              </div>
              <div>
                <label className="text-[10px] text-theme-tertiary block mb-0.5">Border Radius: {config.border_radius}px</label>
                <input type="range" min={0} max={16} value={config.border_radius}
                  onChange={(e) => set("border_radius")(Number(e.target.value))}
                  className="w-full accent-brand-mint" />
              </div>
            </div>
          </div>

          {/* Export */}
          <div className="space-y-2 pt-2 border-t border-theme">
            <div className="flex gap-2">
              <Button onClick={handleDownload} size="sm">Download YAML</Button>
              {saved && <span className="text-xs text-signal-positive self-center">Saved</span>}
            </div>
            <details className="text-xs">
              <summary className="cursor-pointer text-theme-tertiary hover:text-theme">Show YAML</summary>
              <pre className="mt-2 bg-nagarro-blue-900 text-nagarro-green-300 text-[10px] p-3 rounded font-mono overflow-x-auto max-h-48 overflow-y-auto">
                {generateYaml()}
              </pre>
            </details>
          </div>
        </div>
      </div>

      {/* Right: Live Preview */}
      <div className="flex-1 overflow-y-auto bg-theme-secondary">
        {/* Template tabs */}
        <div className="bg-theme border-b border-theme px-6 py-2 flex gap-0.5 shrink-0 sticky top-0 z-10">
          {(["T1", "T2", "T3", "T4"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setPreviewTab(t)}
              className={`px-3 py-1.5 text-xs rounded font-medium transition-colors cursor-pointer
                ${previewTab === t ? "bg-brand-mint/10 text-brand-mint" : "text-theme-tertiary hover:text-theme hover:bg-theme-tertiary"}`}
            >
              {t === "T1" ? "T1 Strategic" : t === "T2" ? "T2 Tactical" : t === "T3" ? "T3 Operational" : "T4 Prescriptive"}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-2">
            <span className="text-[10px] text-theme-tertiary">Mode:</span>
            <select value={config.mode} onChange={(e) => set("mode")(e.target.value as BrandConfig["mode"])}
              className="text-[10px] border border-theme rounded px-1.5 py-0.5 bg-theme-secondary text-theme focus:outline-none">
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="both">Both</option>
            </select>
          </div>
        </div>

        {/* Preview area */}
        <div className="p-6 max-w-3xl mx-auto space-y-6">
          {/* Typography preview */}
          <div className="bg-theme rounded-lg border border-theme p-4" style={{ fontFamily: config.font_family }}>
            <h3 className="text-[10px] text-theme-tertiary uppercase tracking-wider mb-2">Typography Sample</h3>
            <div className="space-y-1">
              <div style={{ fontFamily: config.font_heading, fontWeight: config.heading_weight, fontSize: config.base_size * 1.5, color: config.secondary_color }}>
                Heading ({config.font_heading}, {config.heading_weight})
              </div>
              <div style={{ fontSize: config.base_size, color: config.secondary_color }}>
                Body text at {config.base_size}px &mdash; The quick brown fox jumps over the lazy dog.
              </div>
              <div style={{ fontFamily: config.font_mono, fontSize: config.base_size * 0.85, color: config.neutral_color }}>
                Monospace: sales.net_sales.amount = SUM(Revenue) - SUM(Returns)
              </div>
            </div>
          </div>

          {/* Color swatches */}
          <div className="bg-theme rounded-lg border border-theme p-4">
            <h3 className="text-[10px] text-theme-tertiary uppercase tracking-wider mb-2">Color System</h3>
            <div className="flex gap-2 flex-wrap">
              {[
                { label: "Primary", color: config.primary_color },
                { label: "Secondary", color: config.secondary_color },
                { label: "Positive", color: config.positive_color },
                { label: "Negative", color: config.negative_color },
                { label: "Warning", color: config.warning_color },
                { label: "Neutral", color: config.neutral_color },
              ].map((s) => (
                <div key={s.label} className="text-center">
                  <div className="w-12 h-12 rounded border border-theme" style={{ backgroundColor: s.color, borderRadius: config.border_radius }} />
                  <div className="text-[9px] text-theme-tertiary mt-1">{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Template preview */}
          {previewTab === "T1" && <T1Preview config={config} bg={previewBg} />}
          {previewTab === "T2" && <T2Preview config={config} bg={previewBg} />}
          {previewTab === "T3" && <T3Preview config={config} bg={previewBg} />}
          {previewTab === "T4" && <T4Preview config={config} bg={previewBg} />}
        </div>
      </div>
    </div>
  );
}
