#!/usr/bin/env node
/**
 * Scoped design-system gate. Shared page primitives and the shell are enforced;
 * older components use a checked-in non-regression baseline, NOT a compliance claim.
 * Expand GOVERNED_FILES when a component has actually been migrated and tested.
 */
import { readdir, readFile } from 'node:fs/promises';
import { extname, join, relative, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import postcss from 'postcss';
import ts from 'typescript';

export const GOVERNED_FILES = new Set([
  'src/components/project/project-automation.tsx',
  'src/components/project/project-deployment.tsx',
  'src/components/project/project-automation.module.css',
  'src/components/project/project-estimation.tsx',
  'src/components/project/project-estimation.module.css',
  'src/components/project/project-architecture.tsx',
  'src/components/project/project-architecture.module.css',
  'src/components/project/delivery-workspace.tsx',
  'src/components/project/delivery-workspace.module.css',
  'src/components/project/project-scope.module.css',
  'src/components/project/project-revision-view.tsx',
  'src/components/project/project-scope-boundary.tsx',
  'src/components/ui/studio-page.tsx',
  'src/components/ui/studio-page.module.css',
  'src/components/shell/StudioAppShell.module.css',
  'src/components/canvas/custom-canvas.tsx',
  'src/components/canvas/custom-canvas.module.css',
  'src/components/discovery/source-panel.tsx',
  'src/components/discovery/extraction-panel.tsx',
  'src/components/discovery/discovery-chat.tsx',
  'src/components/discovery/tool-result-card.tsx',
  'src/components/ui/studio-dialog.tsx',
  'src/components/ui/studio-dialog.module.css',
  'src/components/ui/studio-data.tsx',
  'src/components/ui/badges.tsx',
  'src/components/ui/role-chip.tsx',
  'src/components/ui/collapsible-panel.tsx',
  'src/components/ui/kbd-shortcut.tsx',
  'src/components/notifications/notification-bell.tsx',
]);
const HEX = /#[\da-f]{3,8}\b/i;
const removeVariables = (value) => value.replace(/var\([^)]*\)/g, '');
const rawDimension = /(?:^|\s)-?(?:\d*\.)?\d+(?:px|rem|em)\b/;
const BASELINE_PATH = 'tooling/design-token-debt.json';

// Exact, bounded theme-data exceptions. These values describe the customer's
// editable/exported theme, not Studio chrome. No directory-wide preview bypass.
export const EXCEPTIONS = [
  ...['#1A1A2E', '#1E293B', '#1A2332', '#292524'].map((color) => ({
    file: 'src/app/(studio)/brand-lab/brand-lab-client.tsx', rule: 'literal-color',
    value: `background: ${color}`, count: 1, reason: 'Editable customer-theme preset data',
  })),
  ...['#0d0e10', '#0e0f1a', '#13151f'].map((color) => ({
    file: 'src/components/brand/tweaks-tab.tsx', rule: 'literal-color',
    value: `background: ${color}`, count: 1, reason: 'Editable customer-theme preset data',
  })),
  { file: 'src/lib/store/project-store.ts', rule: 'literal-color', value: 'background: #F5F5F5', count: 1,
    reason: 'Default exported customer-theme value, not a Studio surface' },
];
const issueKey = (issue) => JSON.stringify([issue.file, issue.rule, issue.value.replace(/\s+/g, ' ').trim()]);

export function applyExceptions(issues, exceptions = EXCEPTIONS) {
  const remaining = new Map(exceptions.map((item) => [issueKey(item), item.count]));
  const debt = [];
  const excluded = [];
  for (const issue of issues) {
    const key = issueKey(issue);
    if ((remaining.get(key) ?? 0) > 0) {
      remaining.set(key, remaining.get(key) - 1);
      excluded.push(issue);
    } else debt.push(issue);
  }
  return { debt, excluded };
}

export function createBaseline(issues) {
  const entries = new Map();
  for (const issue of issues) {
    const key = issueKey(issue);
    const existing = entries.get(key);
    if (existing) existing.count++;
    else entries.set(key, { file: issue.file, rule: issue.rule, value: issue.value.replace(/\s+/g, ' ').trim(), count: 1 });
  }
  return { version: 1, description: 'Existing design debt. Do not increase counts to make CI green; migrate to tokens. Reductions are allowed and should be recorded during review.',
    findings: [...entries.values()].sort((a, b) => issueKey(a).localeCompare(issueKey(b))) };
}

export function compareBaseline(issues, baseline) {
  if (baseline.version !== 1 || !Array.isArray(baseline.findings)) throw new Error('Unsupported design debt baseline');
  const remaining = new Map(baseline.findings.map((item) => [issueKey(item), item.count]));
  const added = [];
  for (const issue of issues) {
    const key = issueKey(issue);
    if ((remaining.get(key) ?? 0) > 0) remaining.set(key, remaining.get(key) - 1);
    else added.push(issue);
  }
  return { added, removed: [...remaining.values()].reduce((total, count) => total + count, 0) };
}

export function auditCss(source, strict = false) {
  const issues = [];
  postcss.parse(source).walkDecls((decl) => {
    const { prop, value } = decl;
    const report = (rule) => issues.push({ line: decl.source.start.line, rule, value: `${prop}: ${value}` });
    if (prop.startsWith('--')) {
      if (new RegExp(`var\\(\\s*${prop}\\s*[,)]`).test(value)) report('circular-token');
      return;
    }
    if (HEX.test(value)) report('literal-color');
    if (strict && /^(font-size|border-radius|padding(?:-.+)?|margin(?:-.+)?|(?:column-|row-)?gap)$/.test(prop)
      && rawDimension.test(removeVariables(value))) report('literal-design-value');
    if (!strict && prop === 'font-size') {
      const match = value.match(/^(\d*\.?\d+)(px|rem)$/);
      if (match && Number(match[1]) * (match[2] === 'rem' ? 16 : 1) < 12) report('small-text');
    }
  });
  return issues;
}

export function auditTsx(source, strict = false) {
  const issues = [];
  const file = ts.createSourceFile('component.tsx', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  function visit(node) {
    if (ts.isPropertyAssignment(node)) {
      const name = node.name.getText(file).replace(/['"]/g, '');
      const value = ts.isStringLiteralLike(node.initializer) ? node.initializer.text : node.initializer.getText(file);
      const report = (rule) => issues.push({ line: file.getLineAndCharacterOfPosition(node.getStart(file)).line + 1, rule, value: `${name}: ${value}` });
      if (/^(color|background|backgroundColor|borderColor|border|stroke|fill|boxShadow)$/.test(name) && HEX.test(value)) report('literal-color');
      if (name === 'fontSize' && !value.includes('var(')) {
        const size = value.match(/^(\d*\.?\d+)(px|rem)?$/);
        if (strict) report('literal-design-value');
        else if (size && Number(size[1]) * (size[2] === 'rem' ? 16 : 1) < 12) report('small-text');
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(file);
  return issues;
}

async function* walk(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(path);
    else if (['.ts', '.tsx', '.css'].includes(extname(path))) yield path;
  }
}

export async function collect(root = process.cwd()) {
  const failures = [];
  const legacy = [];
  let scanned = 0;
  for await (const path of walk(join(root, 'src'))) {
    const file = relative(root, path).replaceAll('\\', '/');
    const strict = GOVERNED_FILES.has(file);
    const src = await readFile(path, 'utf8');
    const issues = file.endsWith('.css') ? auditCss(src, strict) : auditTsx(src, strict);
    scanned++;
    for (const issue of issues) {
      const item = { file, ...issue };
      if (strict || issue.rule === 'circular-token') failures.push(item);
      else legacy.push(item);
    }
  }
  const shellFile = 'src/components/shell/StudioAppShell.module.css';
  const shell = await readFile(join(root, shellFile), 'utf8');
  postcss.parse(shell).walkDecls((decl) => {
    if (/^--(?:pad|gap|row|h-row|studio-panel-pad-[xy]|studio-header-height|studio-section-gap)$/.test(decl.prop)) {
      failures.push({ file: shellFile, line: decl.source.start.line, rule: 'shadowed-token-authority', value: decl.toString() });
    }
  });
  return { failures, legacy, scanned };
}

export async function run(root = process.cwd()) {
  const { failures, legacy, scanned } = await collect(root);
  const { debt, excluded } = applyExceptions(legacy);
  const baseline = JSON.parse(await readFile(join(root, BASELINE_PATH), 'utf8'));
  const delta = compareBaseline(debt, baseline);
  failures.push(...delta.added.map((issue) => ({ ...issue, rule: `new-legacy-${issue.rule}` })));
  console.log(`Design-system gate: ${GOVERNED_FILES.size} governed files; ${scanned} source files inventoried.`);
  for (const issue of failures) console.error(`${issue.file}:${issue.line} [${issue.rule}] ${issue.value}`);
  const counts = debt.reduce((result, issue) => ({ ...result, [issue.rule]: (result[issue.rule] ?? 0) + 1 }), {});
  console.log(`Existing debt: ${Object.entries(counts).map(([key, count]) => `${count} ${key}`).join(', ') || 'none'}.`);
  console.log(`Legacy ratchet: ${delta.added.length} additions, ${delta.removed} reductions; ${excluded.length} exact theme-data exceptions.`);
  if (process.argv.includes('--inventory')) for (const issue of debt) console.log(`${issue.file}:${issue.line} [${issue.rule}] ${issue.value}`);
  console.log(failures.length ? `FAIL: ${failures.length} design-rule violations.` : 'PASS: governed rules and no new tracked legacy debt; not whole-product design or accessibility certification.');
  return failures.length ? 1 : 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) process.exitCode = await run();
