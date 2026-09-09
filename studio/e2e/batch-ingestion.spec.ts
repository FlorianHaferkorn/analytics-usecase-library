import { test, expect } from '@playwright/test';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { unzipSync, strFromU8 } from 'fflate';

// Real Python repository/processor behind a browser transport harness. Authentication
// and API guards have separate unit coverage; this is not an HTTP deployment test.
test('guided batch contract, actual local processing and released ZIP', async ({ page, context }) => {
  test.skip(process.env.STUDIO_BATCH_E2E !== '1', 'Explicit local-only test opt-in required.');
  test.setTimeout(300_000);
  const root = resolve('..'), scratch = await mkdtemp(join(tmpdir(), 'studio-batch-e2e-'));
  const python = process.platform === 'win32' ? 'py' : 'python3', prefix = process.platform === 'win32' ? ['-3'] : [];
  const seed = JSON.parse(execFileSync(python, [...prefix, '-c', 'import json,sys; from pathlib import Path; from tooling.tests.test_project_automation import make_repository; r,v=make_repository(Path(sys.argv[1]),approved=False); print(json.dumps({"revision":v.revision_hash}))', scratch], { cwd: root, encoding: 'utf8', windowsHide: true }));
  let head: string = seed.revision;
  const repository = join(scratch, 'repositories', 'project_demo');
  const modes: string[] = [], errors: string[] = [], forbidden: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', r => { if (/\/api\/projects\/.*\/(runner|deployment)/.test(r.url())) forbidden.push(r.url()); });
  await context.addCookies([{ name: 'studio.project', value: 'project_demo', url: 'http://localhost:3000' }]);
  await page.route('**/api/project/list', r => r.fulfill({ json: { projects: [{ id: 'project_demo', name: 'Synthetic batch acceptance', strategy_anchor: '', updated_at: '' }] } }));
  await page.route('**/api/projects/*/view*', r => {
    const u = new URL(r.request().url()), id = u.pathname.split('/')[3];
    return r.fulfill({ json: { projectId: id, revision: { revision_hash: u.searchParams.get('revision') || head }, state: 'working', modules: [] } });
  });
  await page.route('**/api/projects/*/ingestion*', r => {
    const request = r.request(), url = new URL(request.url()), body = request.method() === 'POST' ? request.postDataJSON() : {};
    const mode = body.mode || 'inspect'; modes.push(mode);
    const payload = { project_ref: 'project_demo', revision_hash: body.revisionHash || url.searchParams.get('revision'),
      ...(body.contract ? { contract: body.contract } : {}),
      ...(mode === 'save' ? { actor: 'browser-fixture@example.test', preview_hash: body.previewHash, rationale: body.rationale, confirmed: body.confirmed } : {}),
      ...(mode === 'test' ? { batches: body.batches } : {}) };
    const result = spawnSync(python, [...prefix, '-m', 'tooling.superversion.project_package.batch_workbench', '--repository', repository, '--schemas', join(root, 'tooling/generator/schemas'), '--mode', mode], { cwd: root, input: JSON.stringify(payload), encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, windowsHide: true, timeout: 90_000, maxBuffer: 16*1024*1024 });
    const output = JSON.parse(result.stdout);
    if (mode === 'save' && output.ok) head = output.value.revision_hash;
    return r.fulfill({ status: output.ok ? 200 : output.status || 422, json: output.ok ? output.value : { error: output.error } });
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/login?callbackUrl=%2Fautomation%2Fingestion');
  await page.getByRole('button', { name: 'Sign in with Demo', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Batch ingestion', exact: true })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Capability ID', exact: true })).toBeEnabled();
  expect(modes.every(mode => mode === 'inspect')).toBe(true);
  await page.screenshot({ path: test.info().outputPath('batch-inputs-desktop.png'), fullPage: true });
  await page.getByRole('button', { name: 'Review impact', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Derived names and consequences' })).toBeVisible();
  await page.getByRole('button', { name: 'Fit', exact: true }).click();
  await page.screenshot({ path: test.info().outputPath('batch-review-desktop.png'), fullPage: true });
  await page.locator('.react-flow').scrollIntoViewIfNeeded();
  await page.locator('.react-flow').screenshot({ path: test.info().outputPath('batch-architecture-desktop.png') });
  await page.setViewportSize({ width: 768, height: 1000 });
  expect(await page.locator('main').evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('batch-review-narrow.png'), fullPage: true });
  await page.getByRole('button', { name: 'Fit', exact: true }).click();
  await page.locator('.react-flow').scrollIntoViewIfNeeded();
  await page.locator('.react-flow').screenshot({ path: test.info().outputPath('batch-architecture-narrow.png') });
  const save = page.getByRole('button', { name: 'Save Working version', exact: true });
  await expect(save).toBeDisabled();
  await page.getByRole('textbox', { name: 'Review rationale' }).fill('Reviewed only synthetic schema, names and local incremental semantics.');
  await page.getByRole('checkbox', { name: /I reviewed these changes/ }).check(); await save.click();
  await expect(page.getByText(/Working version .* saved/)).toBeVisible();
  await page.getByRole('button', { name: '3 · Local test', exact: true }).click();
  await page.getByRole('button', { name: 'Use synthetic orders example' }).click();
  await page.getByRole('checkbox', { name: /Run only these local test rows/ }).check();
  await page.getByRole('button', { name: 'Run local batches', exact: true }).click();
  await expect(page.getByText('Batch 2', { exact: true })).toBeVisible();
  await expect(page.getByRole('status').filter({ hasText: 'Python data logic only' })).toContainText('"updated": 1');
  await page.screenshot({ path: test.info().outputPath('batch-local-result.png'), fullPage: true });
  await page.getByRole('button', { name: '4 · Outputs', exact: true }).click();
  await page.getByRole('checkbox', { name: /Generate this version's local batch/ }).check();
  await page.getByRole('button', { name: 'Download released batch ZIP' }).click();
  await expect(page.locator('main').getByRole('alert')).toContainText('approval/release');
  // Fixture-only explicit approval: no project DB or customer package is involved.
  const approved = JSON.parse(execFileSync(python, [...prefix, '-c', 'import json,sys; from pathlib import Path; from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository; from tooling.tests.test_project_batch_workbench import approve,SCHEMAS; r=ProjectPackageRevisionRepository(Path(sys.argv[1]),SCHEMAS); v=approve(r,r.head(),Path(sys.argv[2])); print(json.dumps({"revision":v.revision_hash}))', repository, scratch], { cwd: root, encoding: 'utf8', windowsHide: true }));
  head = approved.revision;
  await page.getByRole('button', { name: 'Load latest version', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Capability ID', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: '4 · Outputs', exact: true }).click();
  await page.getByRole('checkbox', { name: /Generate this version's local batch/ }).check();
  const downloaded = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download released batch ZIP' }).click();
  const download = await downloaded, path = test.info().outputPath(download.suggestedFilename()); await download.saveAs(path);
  const files = unzipSync(await readFile(path));
  expect(JSON.parse(strFromU8(files['output-manifest.json'])).revision_hash).toBe(head);
  expect(Object.keys(files)).toContain('delivery-work-plan.json');
  expect(errors).toEqual([]); expect(forbidden).toEqual([]);
});
