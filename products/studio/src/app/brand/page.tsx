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
}

const DEFAULT: BrandConfig = {
  brand_name: "Aurora Group",
  primary_color: "#2B5EB4",
  secondary_color: "#1A3A6E",
  positive_color: "#16A34A",
  negative_color: "#DC2626",
  warning_color: "#D97706",
};

function ColorField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-3">
      <input
        type="color"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-10 h-10 rounded border border-slate-200 cursor-pointer p-0.5"
      />
      <div className="flex-1">
        <label className="block text-xs font-medium text-slate-600">{label}</label>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="text-xs font-mono border border-slate-200 rounded px-2 py-1 mt-0.5 w-28 focus:outline-none focus:ring-1 focus:ring-brand-primary"
        />
      </div>
      <div
        className="w-16 h-8 rounded border border-slate-200"
        style={{ backgroundColor: value }}
      />
    </div>
  );
}

export default function BrandPage() {
  const [config, setConfig] = useState<BrandConfig>(DEFAULT);
  const [saved, setSaved] = useState(false);

  function set(key: keyof BrandConfig) {
    return (v: string) => {
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
    positive: { color: "${config.positive_color}", icon: "▲" }
    negative: { color: "${config.negative_color}", icon: "▼" }
    warning:  { color: "${config.warning_color}", icon: "◆" }
    neutral:  { color: "#6B7280", icon: "●" }
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

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-2xl mx-auto p-8">
        <h1 className="text-xl font-bold text-slate-900 mb-1">Brand Designer</h1>
        <p className="text-sm text-slate-500 mb-8">
          Configure your brand tokens. Export as BrandSpec YAML and use with the derivation
          pipeline to generate Power BI themes and CSS variables.
        </p>

        <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-6">
          {/* Identity */}
          <div>
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Identity
            </h2>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Brand name</label>
              <input
                type="text"
                value={config.brand_name}
                onChange={(e) => set("brand_name")(e.target.value)}
                className="border border-slate-200 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary w-full max-w-xs"
              />
            </div>
          </div>

          {/* Colors */}
          <div>
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Color System
            </h2>
            <div className="space-y-3">
              <ColorField label="Primary" value={config.primary_color} onChange={set("primary_color")} />
              <ColorField label="Secondary" value={config.secondary_color} onChange={set("secondary_color")} />
              <ColorField label="Positive" value={config.positive_color} onChange={set("positive_color")} />
              <ColorField label="Negative" value={config.negative_color} onChange={set("negative_color")} />
              <ColorField label="Warning" value={config.warning_color} onChange={set("warning_color")} />
            </div>
          </div>

          {/* Live preview */}
          <div>
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Preview
            </h2>
            <div
              className="rounded border border-slate-200 p-4"
              style={
                {
                  "--preview-primary": config.primary_color,
                  "--preview-positive": config.positive_color,
                  "--preview-negative": config.negative_color,
                  "--preview-warning": config.warning_color,
                } as React.CSSProperties
              }
            >
              <div className="flex gap-3 flex-wrap items-center">
                <div
                  className="px-4 py-2 rounded text-white text-sm font-medium"
                  style={{ backgroundColor: config.primary_color }}
                >
                  Primary button
                </div>
                <div className="text-sm font-mono" style={{ color: config.positive_color }}>
                  ▲ +12.4%
                </div>
                <div className="text-sm font-mono" style={{ color: config.negative_color }}>
                  ▼ -3.1%
                </div>
                <div className="text-sm font-mono" style={{ color: config.warning_color }}>
                  ◆ 48 days
                </div>
              </div>
            </div>
          </div>

          {/* YAML preview */}
          <div>
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              BrandSpec YAML
            </h2>
            <pre className="bg-slate-950 text-green-300 text-xs p-4 rounded font-mono overflow-x-auto">
              {generateYaml()}
            </pre>
          </div>

          <div className="flex gap-3 items-center">
            <Button onClick={handleDownload}>Download BrandSpec YAML</Button>
            {saved && <span className="text-xs text-green-600">✓ Downloaded</span>}
          </div>

          <div className="text-xs text-slate-400 bg-slate-50 rounded p-3">
            <strong>Next step:</strong> Save the YAML to{" "}
            <code>showcases/&lt;name&gt;/brand/brand_spec.yaml</code> then run:{" "}
            <code>python tooling/brand/derive_brand_artifacts.py</code> to generate Power BI theme
            and CSS variables.
          </div>
        </div>
      </div>
    </div>
  );
}
