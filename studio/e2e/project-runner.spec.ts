import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const revision = 'a'.repeat(64), approvalId = 'b'.repeat(64), planHash = 'c'.repeat(64);
const tenant = '11111111-1111-4111-8111-111111111111', principal = '22222222-2222-4222-8222-222222222222';

test('workspace plan approval, uncertain execution and reload recovery stay separate', async ({ page }) => {
  let executed = false, executeCount = 0, readinessBlocked = true;
  await page.route('**/api/project/list', route => route.fulfill({ json: { projects: [] } }));
  await page.route('**/api/projects/*/view*', route => {
    const id = new URL(route.request().url()).pathname.split('/')[3];
    return route.fulfill({ json: { projectId: id, revision: { revision_hash: revision, package_id: 'fixture', project_ref: id, revision: 1, parent_revision_hash: null }, state: 'approved', modules: [] } });
  });
  await page.route(/\/api\/projects\/[^/]+\/automation(?:\?|$)/, route => {
    const id = new URL(route.request().url()).pathname.split('/')[3];
    return route.fulfill({ json: { project_ref: id, revision_hash: revision, generation_allowed: true, stages: [], targets: [], latest_run: null, automation_gaps: [] } });
  });
  await page.route('**/api/projects/*/deployment', route => {
    const id = new URL(route.request().url()).pathname.split('/')[3];
    return route.fulfill({ json: { project_ref: id, revision_hash: revision, tenant_id: tenant, principal_id: principal, environment: 'dev', plan_sha256: planHash,
      workspace_apply_ready: true, whole_project_apply_ready: false,
      operations: [{ id: 'bronze', action: 'create', desired: { name: 'fixture_bronze_dev' }, reason: 'Absent from complete fixture inventory' }], capabilities: [],
    } });
  });
  await page.route('**/api/projects/*/runner*', route => {
    const url = new URL(route.request().url()), id = url.pathname.split('/')[3];
    const receipt = { project_ref: id, revision_hash: revision, approval_id: approvalId, plan_sha256: planHash, expires_at: new Date(Date.now() + 900_000).toISOString(), status: 'approved_not_executed' };
    if (route.request().method() === 'POST') {
      if (route.request().postDataJSON().mode === 'approve') return route.fulfill({ json: receipt });
      executed = true; executeCount += 1;
      return route.fulfill({ status: 503, json: { error: 'Execution outcome is uncertain. Retrieve the saved outcome; do not retry.' } });
    }
    if (url.searchParams.has('approval')) return route.fulfill({ json: { status: executed ? 'consumed_requires_reconciliation' : 'approved_not_executed', receipt } });
    return route.fulfill({ json: { project_ref: id, enabled: true, can_approve: !readinessBlocked, can_execute: !readinessBlocked, identity_broker_available: true, environments: ['dev'], limitations: ['Enabled fixture only. No tenant is contacted by this test.'],
      checked_at: new Date().toISOString(), readiness_scope: 'configuration_only', tenant_actions_performed: false,
      checks: [{ id: 'fabric_cli', title: 'Fabric CLI', state: readinessBlocked ? 'missing' : 'configured', detail: readinessBlocked ? 'Executable was not found.' : 'Executable discovery succeeded; no command was executed.', action: 'Make the trusted fab installation available on the host PATH.' },
        { id: 'tenant_acceptance', title: 'Tenant acceptance', state: 'not_verified', detail: 'No live test was performed.', action: 'Follow the authorized non-production acceptance procedure.' }] } });
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/automation');
  await page.getByRole('button', { name: 'Deployment preflight', exact: true }).click();
  await expect(page.getByText('1 configuration prerequisite needs attention.', { exact: true })).toBeVisible();
  await page.getByText('Fabric CLI', { exact: true }).click();
  await expect(page.getByText('Make the trusted fab installation available on the host PATH.', { exact: false })).toBeVisible();
  const readiness = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Runner readiness', exact: true }) });
  await readiness.screenshot({ path: test.info().outputPath('readiness-desktop.png') });
  await page.setViewportSize({ width: 768, height: 1000 });
  expect(await page.locator('main').evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
  await readiness.screenshot({ path: test.info().outputPath('readiness-narrow.png') });
  readinessBlocked = false; // Represents an external host correction, not a browser configuration write.
  await page.getByRole('button', { name: 'Recheck readiness' }).click();
  await expect(page.getByText('Reported configuration checks are satisfied. Live acceptance is still required.', { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole('textbox', { name: 'Target tenant ID' }).fill(tenant);
  await page.getByRole('textbox', { name: 'Environment', exact: true }).fill('dev');
  await page.getByLabel('Workspace observation JSON').setInputFiles({ name: 'fixture-observation.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify({ tenant_id: tenant, observed_at: new Date().toISOString() })) });
  await page.getByRole('button', { name: 'Build workspace plan' }).click();
  await expect(page.getByText('fixture_bronze_dev', { exact: true })).toBeVisible();
  const tenantInput = page.getByRole('textbox', { name: 'Target tenant ID' });
  await tenantInput.focus();
  await tenantInput.press('End'); await tenantInput.press('x');
  await expect(tenantInput).toBeFocused();
  await tenantInput.press('Backspace');
  await expect(tenantInput).toHaveValue(tenant);
  await page.getByRole('button', { name: 'Build workspace plan' }).click();
  await expect(page.getByText('fixture_bronze_dev', { exact: true })).toBeVisible();
  const downloaded = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download acceptance protocol' }).click();
  const download = await downloaded;
  const protocol = JSON.parse(await readFile((await download.path())!, 'utf8'));
  expect(protocol.acceptance_status).toBe('not_accepted');
  expect(protocol.authoritative).toBe(false);
  expect(protocol.tenant_actions_performed_by_protocol).toBe(false);
  expect(protocol.scope.plan_sha256).toBe(planHash);
  expect(protocol.cases).toHaveLength(6);
  await page.getByText('Open the workspace acceptance procedure', { exact: true }).click();
  await page.getByText('1. Authorize the non-production test', { exact: true }).click();
  await expect(page.getByText(/The first create test contains exactly one create operation/)).toBeVisible();
  const acceptance = page.locator('section').filter({ has: page.getByRole('heading', { name: 'First workspace acceptance', exact: true }) });
  await acceptance.screenshot({ path: test.info().outputPath('acceptance-desktop.png') });
  await page.setViewportSize({ width: 768, height: 1000 });
  expect(await page.locator('main').evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
  await acceptance.screenshot({ path: test.info().outputPath('acceptance-narrow.png') });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect(page.getByRole('button', { name: 'Save workspace approval' })).toBeDisabled();
  await page.getByRole('textbox', { name: 'Workspace approval rationale' }).fill('Reviewed the exact fixture target and workspace contract.');
  await page.getByRole('checkbox', { name: /I approve the exact workspace/ }).check();
  await page.getByRole('button', { name: 'Save workspace approval' }).click();
  await expect(page).toHaveURL(/runner_approval=/);
  const execute = page.getByRole('button', { name: 'Execute approved workspace plan' });
  await expect(execute).toBeDisabled();
  await page.getByRole('checkbox', { name: /Create the listed workspaces/ }).check();
  await expect(execute).toBeEnabled();
  await execute.scrollIntoViewIfNeeded();
  await page.screenshot({ path: test.info().outputPath('runner-desktop.png'), fullPage: true });
  await page.setViewportSize({ width: 768, height: 1000 });
  await execute.scrollIntoViewIfNeeded();
  expect(await page.locator('main').evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('runner-narrow.png'), fullPage: true });
  await execute.click();
  await expect(page.getByRole('alert').filter({ hasText: 'Execution outcome is uncertain' })).toBeVisible();
  await expect(execute).toHaveCount(0);
  expect(executeCount).toBe(1);
  await page.reload();
  await page.getByRole('button', { name: 'Deployment preflight', exact: true }).click();
  await page.getByText('Retrieve an existing approval or execution outcome', { exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Saved approval ID' })).toHaveValue(approvalId);
  await page.getByRole('button', { name: 'Retrieve saved outcome' }).click();
  await expect(page.getByText('Saved attempt state: consumed requires reconciliation', { exact: true })).toBeVisible();
  await expect(execute).toHaveCount(0);
  expect(executeCount).toBe(1);
});
