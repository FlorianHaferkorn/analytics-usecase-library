// Recharts render proof — a REAL React + Recharts headless render of every web_recharts golden.
//
// Python can't run Recharts (it's a React runtime), so this is the out-of-pytest proof that the
// JSX goldens actually render: each is bundled with esbuild, mounted in a headless Chromium via
// Playwright, and asserted to produce a populated <svg>. Result recorded in validation_matrix.json
// (web_recharts = "rendered", method "react-harness").
//
// Reproduce:
//   cd tooling/visual_library/acceptance
//   npm i react react-dom recharts esbuild playwright   # (or playwright-core + a browser)
//   node render_recharts.mjs
//
// The JSX snippets reference the data variables a host app supplies (data, waterfallData,
// sankeyData, varianceData, buildupData, bins, series, row) — this harness provides representative
// values for each, exactly as the "How to ship it" recipe instructs a consumer to.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import esbuild from "esbuild";
import { chromium } from "playwright";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const GOLDEN = path.resolve(HERE, "../../../core/templates/page_templates/visual_library/golden");

const COMPS = "BarChart,LineChart,AreaChart,ComposedChart,ScatterChart,PieChart,RadialBarChart,"
  + "Treemap,Sankey,Funnel,FunnelChart,Bar,Line,Area,Scatter,Pie,Cell,XAxis,YAxis,ZAxis,"
  + "CartesianGrid,Tooltip,Legend,ReferenceLine,ReferenceArea,ReferenceDot,LabelList,Label,"
  + "ResponsiveContainer,Rectangle,Dot,Sector";

function sampleRows(n) {
  const cat = {
    unit: "ABCDE", part: ["Fashion", "Home", "Electro", "Sport"],
    period: ["Jan", "Feb", "Mar", "Apr", "May"], region: ["DACH", "BeNe", "Nord", "CEE"],
    driver: ["PY", "Price", "Cost", "Mix", "Actual"], bin: ["0-10", "10-20", "20-30", "30-40"],
    month: ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05"],
  };
  const out = []; let cum = 0;
  for (let i = 0; i < n; i++) {
    const d = [8, -5, 6, -3, 9][i % 5]; const base = cum; cum += d;
    out.push({
      unit: cat.unit[i % 5], part: cat.part[i % 4], period: cat.period[i % 5], region: cat.region[i % 4],
      driver: cat.driver[i % 5], bin: cat.bin[i % 4], month: cat.month[i % 5],
      gm: 40 + i * 4, gm_vs_plan: [-0.018, 0.02, -0.01, 0.03, -0.02][i % 5], idx: 100 + i * 6,
      net_sales: 3 + i, price_real: 90 + i * 3, sales: 2 + i * 0.5, sla: 0.9 + i * 0.01, count: 4 + i * 2,
      base, delta: d, series1: 10 + i, series2: 14 - i, series3: 9 + i, part_val: 20 + i,
    });
  }
  return out;
}
const DATA = sampleRows(5);
const SANKEY = { nodes: [{ name: "Leads" }, { name: "MQL" }, { name: "Won" }], links: [{ source: 0, target: 1, value: 10 }, { source: 1, target: 2, value: 6 }] };

async function main() {
  const files = fs.readdirSync(GOLDEN).filter((f) => /\.web_recharts.*\.jsx$/.test(f)).sort();
  const browser = await chromium.launch();
  let ok = 0, bad = 0;
  for (const f of files) {
    const jsx = fs.readFileSync(path.join(GOLDEN, f), "utf8").trim();
    const entry = `
import React from 'react';
import { createRoot } from 'react-dom/client';
import * as RC from 'recharts';
const {${COMPS}} = RC;
const data=${JSON.stringify(DATA)}, bins=data, buildupData=data, varianceData=data, waterfallData=data,
  sankeyData=${JSON.stringify(SANKEY)}, row=data[0], series=["series1","series2","series3"];
function Chart(){ return ( ${jsx} ); }
createRoot(document.getElementById('root')).render(React.createElement(Chart));`;
    let bundle;
    try {
      const r = await esbuild.build({
        stdin: { contents: entry, resolveDir: HERE, loader: "jsx" }, bundle: true, write: false,
        format: "iife", jsxFactory: "React.createElement", jsxFragment: "React.Fragment",
        absWorkingDir: HERE, logLevel: "silent", define: { "process.env.NODE_ENV": '"development"' },
      });
      bundle = r.outputFiles[0].text;
    } catch (e) { bad++; console.log(`BUILDFAIL ${f}: ${String(e.message || e).split("\n")[0].slice(0, 80)}`); continue; }
    const ctx = await browser.newContext({ viewport: { width: 800, height: 500 } });
    const pg = await ctx.newPage();
    const errs = []; pg.on("pageerror", (e) => errs.push(String(e.message || e)));
    await pg.setContent('<div id="root"></div>');
    await pg.addScriptTag({ content: bundle });
    await pg.waitForTimeout(350);
    const info = await pg.evaluate(() => { const s = document.querySelector("#root svg"); return s ? s.querySelectorAll("*").length : 0; });
    await ctx.close();
    if (info > 2) { ok++; console.log(`OK   ${f.padEnd(42)} svg kids=${info}`); }
    else { bad++; console.log(`FAIL ${f.padEnd(42)} ${errs[0] ? "| " + errs[0].slice(0, 70) : "no svg"}`); }
  }
  await browser.close();
  console.log(`\n${ok} rendered, ${bad} failed`);
  process.exit(bad ? 1 : 0);
}
main().catch((e) => { console.error("ERR", e); process.exit(1); });
