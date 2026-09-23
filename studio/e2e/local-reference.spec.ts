import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { unzipSync, strFromU8 } from 'fflate';

// Deliberately opts in: executes real local Python compilers, never a tenant.
test('real local reference: decision, architecture, evidence and same-version ZIP', async ({ page }) => {
  test.skip(process.env.STUDIO_LOCAL_REFERENCE_E2E !== '1', 'Opt in to real local compiler execution on an existing development server.');
  test.setTimeout(300_000);
  const unsafeRequests: string[] = [], customerContent: string[] = [], errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (/\/api\/projects\/.*\/(runner|deployment)/.test(request.url())) unsafeRequests.push(request.url());
    if (/\/api\/projects\/.*\/(view|architecture|automation)(\?|$)/.test(request.url())) customerContent.push(request.url());
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/login?callbackUrl=%2Fautomation%2Freference');
  await page.getByRole('button', { name: 'Sign in with Demo', exact: true }).click();
  await expect(page).toHaveURL(/\/automation\/reference$/, { timeout: 30_000 });
  await expect(page.getByRole('heading', { name: 'Local reference lab', exact: true })).toBeVisible();
  await expect.poll(() => page.evaluate(() => sessionStorage.getItem('studio.view.selection'))).not.toBeNull();
  const beforeSelection = await page.evaluate(() => sessionStorage.getItem('studio.view.selection'));
  const run = page.getByRole('button', { name: 'Run local reference', exact: true });
  await expect(run).toBeDisabled();
  await page.screenshot({ path: test.info().outputPath('reference-input-desktop.png'), fullPage: true });
  const revisions: string[] = [];
  for (const variant of ['dev_test_prod', 'dev_prod']) {
    if (variant === 'dev_prod') await page.locator('summary').filter({ hasText: 'Reference input' }).click();
    await page.getByRole('combobox', { name: 'Reference environment decision' }).selectOption(variant);
    await page.getByRole('checkbox').check();
    const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/local-reference') && response.request().method() === 'POST', { timeout: 190_000 });
    await run.click();
    const response = await responsePromise;
    expect(response.status(), await response.text()).toBe(200);
    const report = await response.json();
    expect(report).toMatchObject({ source_kind: 'synthetic', project_ref: 'local_reference', variant, tenant_actions_performed: false, live_apply_allowed: false });
    revisions.push(report.revision_hash);
    expect(report.checks.every((check: { evidence_kind: string }) => check.evidence_kind !== 'tenant_verified')).toBe(true);
    await expect(page.getByRole('button', { name: 'Download reference ZIP' })).toBeVisible();
    await page.getByRole('button', { name: 'Architecture', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Derived reference architecture' })).toBeVisible();
    await page.getByRole('button', { name: 'Fit', exact: true }).click();
    await page.locator('[aria-label="Graph viewport"]').scrollIntoViewIfNeeded();
    await page.screenshot({ path: test.info().outputPath(`reference-${variant}-architecture.png`), fullPage: true });
    await page.getByRole('button', { name: 'Checks & limitations' }).click();
    await page.getByText('Tenant verification', { exact: true }).click();
    await expect(page.getByText('No tenant is configured or called.', { exact: false })).toBeVisible();
    await page.getByRole('button', { name: 'Generated files' }).click();
    await expect(page.getByRole('combobox', { name: 'Generated reference file' })).toBeVisible();
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download reference ZIP' }).click();
    const download = await downloadPromise;
    const output = test.info().outputPath(download.suggestedFilename()); await download.saveAs(output);
    const files = unzipSync(await readFile(output));
    expect(Object.keys(files)).toHaveLength(report.files.length + 1);
    for (const file of report.files) {
      expect(strFromU8(files[file.path])).toBe(file.content);
      expect(createHash('sha256').update(files[file.path]).digest('hex')).toBe(file.sha256);
    }
    expect(JSON.parse(strFromU8(files['local-reference-report.json'])).revision_hash).toBe(report.revision_hash);
    await page.setViewportSize({ width: 768, height: 1000 });
    expect(await page.locator('main').evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`reference-${variant}-files-narrow.png`), fullPage: true });
    await page.setViewportSize({ width: 1440, height: 1000 });
  }
  expect(revisions[0]).not.toBe(revisions[1]);
  expect(await page.evaluate(() => sessionStorage.getItem('studio.view.selection'))).toBe(beforeSelection);
  expect(unsafeRequests).toEqual([]); expect(customerContent).toEqual([]); expect(errors).toEqual([]);
  await page.reload(); await expect(run).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Download reference ZIP' })).toHaveCount(0);
});
