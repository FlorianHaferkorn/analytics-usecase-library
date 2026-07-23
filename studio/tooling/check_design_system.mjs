#!/usr/bin/env node
/**
 * Design system guard — undefined CSS vars and spacing token presence.
 * Run: node tooling/check_design_system.mjs
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const ROOT = join(import.meta.dirname, '..');
const TOKENS_PATH = join(ROOT, 'src/styles/tokens.css');
const SRC = join(ROOT, 'src');

const REQUIRED_TOKENS = [
  '--sp-1', '--sp-2', '--sp-3', '--sp-4', '--sp-5', '--sp-6', '--sp-7', '--sp-8',
  '--shell-header', '--shell-sidebar', '--pad', '--gap', '--accent',
  '--success', '--warning', '--danger', '--info',
];

const tokensCss = readFileSync(TOKENS_PATH, 'utf-8');
const defined = new Set([...tokensCss.matchAll(/(--[a-z0-9-]+)\s*:/gi)].map((m) => m[1]));

const errors = [];
for (const token of REQUIRED_TOKENS) {
  if (!defined.has(token)) errors.push(`Missing token in tokens.css: ${token}`);
}

/** Collect var(--foo) references in src (excluding tokens.css). */
function walk(dir, files = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) {
      if (name === 'node_modules' || name === '.next') continue;
      walk(p, files);
    } else if (/\.(tsx?|css)$/.test(name)) {
      files.push(p);
    }
  }
  return files;
}

const suspicious = new Set(['--sp-9', '--slate-900', '--mint-dark']);
for (const file of walk(SRC)) {
  if (file.endsWith('tokens.css')) continue;
  const rel = relative(ROOT, file);
  const text = readFileSync(file, 'utf-8');
  for (const m of text.matchAll(/var\((--[a-z0-9-]+)\)/gi)) {
    const name = m[1];
    if (suspicious.has(name) || (name.startsWith('--sp-') && !defined.has(name))) {
      errors.push(`Suspicious/undefined var() in ${rel}: ${name}`);
    }
  }
}

if (errors.length) {
  console.error('Design system check FAILED:\n');
  for (const e of errors) console.error(`  • ${e}`);
  process.exit(1);
}

console.log('Design system check passed.');
