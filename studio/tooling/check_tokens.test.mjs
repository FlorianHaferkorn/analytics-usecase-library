import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { auditCss, auditTsx, applyExceptions, createBaseline, compareBaseline, run } from './check_tokens.mjs';

test('rejects self-referential tokens, including @theme', () => {
  assert.equal(auditCss('@theme { --radius-lg: var(--radius-lg); }')[0].rule, 'circular-token');
  assert.equal(auditCss(':root { --radius: var(--radius-card); }').length, 0);
});
test('requires tokens for governed type, radius and spacing', () => {
  assert.equal(auditCss('.x { font-size: 13px; padding: 8px; border-radius: 12px; }', true).length, 3);
  assert.equal(auditCss('.x { font-size: var(--text-sm); padding: 0 var(--space-2, 8px); margin: 0 auto; }', true).length, 0);
});
test('does not mistake documentation comments for CSS violations', () => {
  assert.equal(auditCss('/* --x: var(--x); #ffffff */ .x { color: var(--ink); }', true).length, 0);
});
test('detects JSX literal colors even with quotes and colon-space', () => {
  assert.equal(auditTsx("<div style={{ color: '#ffffff' }} />", true)[0].rule, 'literal-color');
  assert.equal(auditTsx("<div style={{ color: 'var(--ink)' }} />", true).length, 0);
});
test('inventories legacy small text without claiming compliance', () => {
  assert.equal(auditTsx('<div style={{ fontSize: 10 }} />')[0].rule, 'small-text');
  assert.equal(auditCss('.x { font-size: 0.6875rem; }')[0].rule, 'small-text');
});

const existing = { file: 'src/components/old.tsx', line: 10, rule: 'small-text', value: 'fontSize: 11px' };
test('legacy ratchet allows existing debt and reductions, but rejects new values and duplicates', () => {
  const baseline = createBaseline([existing]);
  assert.equal(compareBaseline([existing], baseline).added.length, 0);
  assert.equal(compareBaseline([], baseline).removed, 1);
  assert.equal(compareBaseline([existing, { ...existing, line: 20 }], baseline).added.length, 1);
  assert.equal(compareBaseline([{ ...existing, value: 'fontSize: 10px' }], baseline).added.length, 1);
  assert.equal(compareBaseline([{ ...existing, file: 'src/components/new.tsx' }], baseline).added.length, 1);
});
test('legacy ratchet survives line shifts and harmless whitespace, not moves between files', () => {
  const baseline = createBaseline([existing]);
  assert.equal(compareBaseline([{ ...existing, line: 999, value: 'fontSize:   11px' }], baseline).added.length, 0);
});
test('exceptions only exempt the exact rule/value/file and allowed count', () => {
  const exceptions = [{ ...existing, count: 1, reason: 'Test only' }];
  assert.equal(applyExceptions([existing], exceptions).debt.length, 0);
  assert.equal(applyExceptions([existing, existing], exceptions).debt.length, 1);
  assert.equal(applyExceptions([{ ...existing, value: 'fontSize: 9px' }], exceptions).debt.length, 1);
});

test('actual gate returns failure for new debt outside the governed manifest', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'studio-token-ratchet-'));
  t.mock.method(console, 'log', () => {});
  t.mock.method(console, 'error', () => {});
  try {
    await mkdir(join(root, 'src/components/shell'), { recursive: true });
    await mkdir(join(root, 'tooling'));
    await writeFile(join(root, 'src/components/shell/StudioAppShell.module.css'), '.shell { display: flex; }');
    const component = join(root, existing.file);
    await writeFile(component, '<div style={{ fontSize: "11px" }} />');
    await writeFile(join(root, 'tooling/design-token-debt.json'), JSON.stringify(createBaseline([existing])));
    assert.equal(await run(root), 0);
    await writeFile(component, '<div style={{ fontSize: "11px" }} /><div style={{ fontSize: "9px" }} />');
    assert.equal(await run(root), 1);
    await writeFile(component, '<div style={{ fontSize: "var(--text-xs)" }} />');
    assert.equal(await run(root), 0);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
