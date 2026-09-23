import { test, expect } from '@playwright/test';

const hash = 'a'.repeat(64), updated = 'b'.repeat(64), preview = 'c'.repeat(64);

test('reviewed decision updates the pinned architecture and clears release confirmation', async ({ page }) => {
  await page.route('**/api/project/list', route => route.fulfill({ json: { projects: [] } }));
  await page.route('**/api/projects/*/view*', route => {
    const url = new URL(route.request().url()), id = url.pathname.split('/')[3];
    const revision = url.searchParams.get('revision') || hash;
    return route.fulfill({ json: { projectId: id, revision: { revision_hash: revision, package_id: 'fixture', project_ref: id, revision: revision === hash ? 1 : 2, parent_revision_hash: revision === hash ? null : hash }, state: revision === hash ? 'approved' : 'working', modules: [] } });
  });
  await page.route(/\/api\/projects\/[^/]+\/architecture(?:\?|$)/, route => {
    const url = new URL(route.request().url()), id = url.pathname.split('/')[3], revision = url.searchParams.get('revision');
    return route.fulfill({ json: {
      project_ref: id, revision_hash: revision, architecture: {}, use_cases: [],
      graph: { nodes: [{ id: 'workspace:bronze', kind: 'workspace', label: revision === hash ? 'bronze-old' : 'bronze-new', layer: 'dev', details: {} }], edges: [] },
      readiness: { release_ready: revision === hash, blockers: revision === hash ? [] : ['input_release_required'], apply_ready: false },
      outputs: [{ id: 'architecture_bundle', label: 'Architecture bundle', status: 'ready', reason: 'Recorded architecture' }],
    } });
  });
  await page.route('**/api/projects/*/architecture/decisions*', route => {
    const id = new URL(route.request().url()).pathname.split('/')[3];
    if (route.request().method() === 'POST') return route.fulfill({ json: { project_ref: id, revision_hash: updated, parent_revision_hash: hash, state: 'working', release_required: true, audit_ref: 'architecture/derivations/fixture.json' } });
    return route.fulfill({ json: { project_ref: id, revision_hash: hash, preview_sha256: preview, can_apply: true, blockers: [],
      changes: [{ rule_id: 'workspace_name', decision_ref: 'approved_naming', target: { collection: 'physical_workspaces', entity_id: 'bronze', field: 'name' }, before: 'bronze-old', after: 'bronze-new', rationale: 'Apply the approved snake-case workspace name.' }],
      rules: [{ id: 'workspace_name', status: 'ready', reason: 'Explicit approved mapping.' }],
    } });
  });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/architecture');
  await expect(page.locator('.react-flow__node').filter({ hasText: 'bronze-old' })).toBeVisible();
  await page.getByRole('button', { name: 'Build outputs', exact: true }).click();
  await page.getByRole('checkbox').check();
  await expect(page.getByRole('button', { name: 'Generate architecture bundle' })).toBeEnabled();
  await page.getByRole('button', { name: 'Decision effects', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Proposed architecture changes' })).toBeVisible();
  await expect(page.getByText('bronze-old', { exact: true })).toBeVisible();
  await expect(page.getByText('bronze-new', { exact: true })).toBeVisible();
  const submit = page.getByRole('button', { name: 'Update architecture draft', exact: true });
  await expect(submit).toBeDisabled();
  await page.getByRole('textbox', { name: 'Review rationale' }).fill('Reviewed the explicit approved naming against the workspace contract.');
  await page.getByRole('checkbox').check();
  await expect(submit).toBeEnabled();
  await page.screenshot({ path: test.info().outputPath('decision-review-desktop.png'), fullPage: true });
  await page.setViewportSize({ width: 768, height: 900 });
  await expect(submit).toBeVisible();
  expect(await page.locator('main').evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('decision-review-narrow.png'), fullPage: true });
  const request = page.waitForRequest(r => r.url().includes('/architecture/decisions') && r.method() === 'POST');
  await submit.click();
  expect((await request).postDataJSON()).toEqual({ revisionHash: hash, previewHash: preview, rationale: 'Reviewed the explicit approved naming against the workspace contract.', confirmed: true });
  await expect(page.locator('.react-flow__node').filter({ hasText: 'bronze-new' })).toBeVisible();
  await expect(page.getByRole('status')).toContainText('new Working version');
  await page.getByRole('button', { name: 'Build outputs', exact: true }).click();
  await expect(page.getByRole('checkbox')).not.toBeChecked();
  await page.getByRole('checkbox').check();
  await expect(page.getByRole('button', { name: 'Generate architecture bundle' })).toBeDisabled();
});
