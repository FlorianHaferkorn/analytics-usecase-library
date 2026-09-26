import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';

// Opt-in: real Studio routes, real Python engine, synthetic reference package. Never a tenant.
test('real engine: compare the DEV / PROD alternative against the released DEV / TEST / PROD baseline', async ({ page, context, baseURL }) => {
  test.skip(process.env.STUDIO_ALTERNATIVE_IMPACT_E2E !== '1', 'Opt in on a development server started with STUDIO_PACKAGE_DATA_ROOT.');
  test.setTimeout(240_000);
  const dataRoot = process.env.STUDIO_PACKAGE_DATA_ROOT;
  expect(dataRoot, 'STUDIO_PACKAGE_DATA_ROOT must match the running server').toBeTruthy();
  const root = isAbsolute(dataRoot!) ? dataRoot! : resolve(process.cwd(), dataRoot!);
  const writes: string[] = [], unsafe: string[] = [], errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (/\/api\/projects\/.*\/(runner|deployment)/.test(request.url())) unsafe.push(request.url());
    if (request.method() !== 'GET' && /\/api\/projects\//.test(request.url())) writes.push(`${request.method()} ${request.url()}`);
  });

  await page.goto('/login?callbackUrl=%2Farchitecture');
  await page.getByRole('button', { name: 'Sign in with Demo', exact: true }).click();
  await expect(page).toHaveURL(/\/architecture/, { timeout: 60_000 });

  const created = await page.request.post('/api/project', { data: { name: 'Synthetic alternative reference' } });
  expect(created.status(), await created.text()).toBe(201);
  const body = await created.json();
  const projectId: string = (body.project ?? body.data?.project).id;
  expect(projectId).toMatch(/^proj_[a-f0-9]{32}$/);

  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const built = JSON.parse(execFileSync(python, [
    ...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.alternative_impact', '--schemas', join('tooling', 'generator', 'schemas'),
    '--build-reference', join(root, 'repositories', projectId), '--project-ref', projectId,
  ], { cwd: resolve(process.cwd(), '..'), encoding: 'utf-8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }));
  expect(built.ok).toBe(true);
  const revision: string = built.value.revision_hash;

  await context.addCookies([{ name: 'studio.project', value: projectId, url: baseURL! }]);
  await page.addInitScript(([id, hash]) => {
    sessionStorage.setItem('studio.view.selection', JSON.stringify({ projectId: id, scope: 'project', hash }));
  }, [projectId, revision]);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/architecture');
  await page.getByRole('button', { name: 'Decision effects', exact: true }).click();

  const compare = page.getByRole('button', { name: 'decision environment model → dev prod', exact: true });
  await expect(compare).toBeVisible({ timeout: 60_000 });
  const responsePromise = page.waitForResponse(response => response.url().includes('/architecture/alternatives?'), { timeout: 120_000 });
  await compare.click();
  const response = await responsePromise;
  expect(response.status(), await response.text()).toBe(200);
  const impact = await response.json();
  expect(impact).toMatchObject({ project_ref: projectId, baseline_revision_hash: revision, status: 'impact_ready',
    baseline_option_ref: 'dev_test_prod', alternative_option_ref: 'dev_prod', baseline_unchanged: true,
    approval_granted: false, release_granted: false, tenant_actions_performed: false });

  await expect(page.getByText('− TEST', { exact: true })).toBeVisible();
  await expect(page.getByText('− test lead', { exact: true })).toBeVisible();
  await expect(page.getByText('6 person-days → 4 person-days', { exact: true })).toBeVisible();
  for (const id of ['ws_sales_test', 'ws_finance_test', 'pl_sales_test', 'nb_finance_test']) {
    await expect(page.getByRole('cell', { name: id, exact: true })).toBeVisible();
  }
  await expect(page.getByText('retire topology · domain_sales/test', { exact: true })).toBeVisible();
  await page.screenshot({ path: test.info().outputPath('alternative-impact-desktop.png'), fullPage: true });

  await page.setViewportSize({ width: 768, height: 1000 });
  await expect(compare).toBeVisible();
  expect(await page.locator('main').evaluate(element => element.scrollWidth <= element.clientWidth + 1)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('alternative-impact-narrow.png'), fullPage: true });

  expect(writes).toEqual([]);
  expect(unsafe).toEqual([]);
  expect(errors).toEqual([]);
});
