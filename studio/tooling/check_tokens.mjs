#!/usr/bin/env node
/**
 * Token-compliance lint — checks for hardcoded hex colors in component files.
 * Run from the studio directory: node tooling/check_tokens.mjs
 *
 * Fails if new hardcoded hex values appear outside the allowlist.
 * The allowlist covers hex values that exist legitimately in non-component files
 * (token definitions, theme presets, etc.).
 */

import { readdir, readFile } from 'node:fs/promises';
import { join, extname } from 'node:path';

// Hex values allowed everywhere (canonical design tokens defined in globals.css / tokens.ts)
const ALLOWED_HEX = new Set([
  '#0d0e10', '#131416', '#1a1b1f',   // bg / bg-2 / panel
  '#eaebee', '#b0b0b8', '#6e6e78', '#42424c',  // ink scale
  '#00D4AA', '#00d4aa',              // accent
  '#FFB800', '#ffb800',              // gold
  '#3B82F6',                         // fact node blue
  '#60A5FA',                         // driver node blue
  '#475569', '#334155', '#1E293B',   // legacy slate (canvas/lineage — being migrated)
  '#020617', '#CBD5E1', '#64748B',   // canvas legend / inspector (legacy)
  '#RRGGBB',                         // BrandSpec schema placeholder string
]);

// Directories to scan (relative to studio/)
const SCAN_DIRS = ['src/components', 'src/app', 'src/hooks', 'src/lib/theme'];

// Files to skip entirely (token definitions, data-viz palettes, export helpers)
const SKIP_PATTERNS = [
  /globals\.css$/,
  /tokens\.ts$/,
  /brand-spec/,
  /color-picker/,
  /contrast-checker/,
  /export-css\.ts$/,
  /export-json\.ts$/,
  /export-tailwind\.ts$/,
  /golden-thread-flow/,  // data-viz domain palette — semantic, not UI chrome
  /node_modules/,
  /\.next/,
];

const HEX_RE = /#([0-9a-fA-F]{3,8})\b/g;

async function* walk(dir) {
  let entries;
  try { entries = await readdir(dir, { withFileTypes: true }); }
  catch { return; }
  for (const e of entries) {
    const full = join(dir, e.name);
    if (e.isDirectory()) yield* walk(full);
    else if (e.isFile() && (extname(e.name) === '.ts' || extname(e.name) === '.tsx' || extname(e.name) === '.css')) {
      yield full;
    }
  }
}

let violations = 0;
let filesScanned = 0;

for (const scanDir of SCAN_DIRS) {
  const base = join(process.cwd(), scanDir);
  for await (const filePath of walk(base)) {
    if (SKIP_PATTERNS.some(p => p.test(filePath))) continue;
    filesScanned++;
    const src = await readFile(filePath, 'utf-8');
    const lines = src.split('\n');
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      // Skip comment lines and strings that look like schema/docs
      if (line.trimStart().startsWith('//') || line.trimStart().startsWith('*')) continue;
      let m;
      HEX_RE.lastIndex = 0;
      while ((m = HEX_RE.exec(line)) !== null) {
        const hex = m[0].toLowerCase().replace(/^#/, '');
        const full = '#' + hex;
        const fullUpper = m[0];
        if (ALLOWED_HEX.has(full) || ALLOWED_HEX.has(fullUpper)) continue;
        // Allow in strings that look like user-facing theme preset values
        const context = line.slice(Math.max(0, m.index - 20), m.index + 20);
        if (context.includes("'") && context.includes(': ')) continue; // YAML-style
        console.log(`  ${filePath.replace(process.cwd() + '/', '')}:${i + 1}  →  ${fullUpper}`);
        violations++;
      }
    }
  }
}

console.log(`\nScanned ${filesScanned} files.`);
if (violations === 0) {
  console.log('✓ No hardcoded hex violations found.');
  process.exit(0);
} else {
  console.log(`✗ ${violations} hardcoded hex violation(s). Replace with CSS tokens (var(--accent), var(--ink-3), etc.)`);
  process.exit(1);
}
