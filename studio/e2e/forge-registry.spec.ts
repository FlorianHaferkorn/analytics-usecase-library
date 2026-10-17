/**
 * Forge/Registry route group E2E tests (Week 6 exit gate).
 *
 * Covers:
 *  - Forge path: compose → generate
 *  - Registry path: catalog → drift → approvals (the catalog is now the
 *    management lens of the unified Library, /library?view=manage)
 *
 * Auth: uses the demo credentials that already exist in other e2e specs.
 */
import { test, expect, type Page } from '@playwright/test';

async function loginAsDemo(page: Page) {
  await page.goto('/login');
  await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
  await page.getByText('Sign in with Demo').click();
  // Wait for redirect away from /login
  await page.waitForURL((url: URL) => !url.pathname.includes('/login'), { timeout: 10_000 });
}

test.describe('Forge path', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemo(page);
  });

  test('sidebar links the governed library from /discover', async ({ page }) => {
    await page.goto('/discover');
    // The Forge/Registry mode switcher no longer exists: since b1a2fee15 (23.09.2026)
    // one workflow sidebar carries both, and the governed definitions formerly under
    // "Registry" live in the Reference library (navigation.spec.ts asserts that no
    // 'Registry'/'Forge' link leaks back). Assert the hub heading and that entry.
    await expect(page.getByRole('heading', { name: 'Discovery', level: 1 })).toBeVisible();
    const workflow = page.getByRole('navigation', { name: 'Studio workflow' });
    await expect(workflow.getByRole('link', { name: 'Reference library', exact: true })).toHaveAttribute('href', '/library');
    await expect(page.getByRole('link', { name: 'Registry', exact: true })).toHaveCount(0);
  });

  test('/compose renders Simulator', async ({ page }) => {
    await page.goto('/compose');
    await expect(page).toHaveURL('/compose');
    // Simulator has formula / what-if content
    await expect(page.locator('main')).toBeVisible();
  });

  test('/generate renders Delivery', async ({ page }) => {
    await page.goto('/generate');
    await expect(page).toHaveURL('/generate');
    await expect(page.locator('main')).toBeVisible();
  });

  test('old /delivery redirects to /generate', async ({ page }) => {
    await page.goto('/delivery');
    await expect(page).toHaveURL('/generate');
  });

  test('old /simulator redirects to /compose', async ({ page }) => {
    await page.goto('/simulator');
    await expect(page).toHaveURL('/compose');
  });
});

test.describe('Registry path', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemo(page);
  });

  test('sidebar marks the library management lens active when on /catalog', async ({ page }) => {
    await page.goto('/catalog');
    // Since 0ac7775b1 (08.09.2026) /catalog redirects to the management lens of the
    // unified Library (/library?view=manage). The former "Catalog" link is the
    // 'Manage definitions' tool of that page, the former "Registry" entry is the
    // sidebar's 'Reference library'. Both must mark themselves as the current page.
    await expect(page).toHaveURL(/\/library\?view=manage$/);
    const workflow = page.getByRole('navigation', { name: 'Studio workflow' });
    await expect(workflow.getByRole('link', { name: 'Reference library', exact: true })).toHaveAttribute('aria-current', 'page');
    const tools = page.getByRole('navigation', { name: 'Library tools' });
    await expect(tools.getByRole('link', { name: 'Manage definitions', exact: true })).toHaveAttribute('aria-current', 'page');
    await expect(tools.getByRole('link', { name: 'Browse assets', exact: true })).not.toHaveAttribute('aria-current', 'page');
  });

  test('/catalog renders KPI catalog table', async ({ page }) => {
    await page.goto('/catalog');
    // Legacy route: redirects to the Library management lens (0ac7775b1).
    await expect(page).toHaveURL(/\/library\?view=manage$/);
    const main = page.locator('main');
    await expect(main.getByRole('heading', { name: 'Library', level: 1 })).toBeVisible();
    const table = main.getByRole('table').first();
    await expect(table.getByRole('columnheader', { name: 'Name', exact: true })).toBeVisible();
    await expect(table.getByRole('columnheader', { name: 'Ref', exact: true })).toBeVisible();
    expect(await table.locator('tbody tr').count()).toBeGreaterThan(0);
  });

  test('/drift renders drift report page', async ({ page }) => {
    await page.goto('/drift');
    await expect(page).toHaveURL('/drift');
    await expect(page.getByText('Catalog ↔ TMDL Drift')).toBeVisible();
  });

  test('/approvals renders bracket approval queue', async ({ page }) => {
    await page.goto('/approvals');
    await expect(page).toHaveURL('/approvals');
    await expect(page.getByText('Governance Approvals')).toBeVisible();
  });

  test('old /registry redirects to the library management lens', async ({ page }) => {
    // /registry -> /catalog -> /library?view=manage (0ac7775b1).
    await page.goto('/registry');
    await expect(page).toHaveURL(/\/library\?view=manage$/);
  });

  test('sidebar navigates from /discover to the library management lens', async ({ page }) => {
    // Replaces the removed Registry mode switcher: the governed catalog is reached
    // through the Reference library and its 'Manage definitions' tool.
    await page.goto('/discover');
    await page.getByRole('navigation', { name: 'Studio workflow' }).getByRole('link', { name: 'Reference library', exact: true }).click();
    await expect(page).toHaveURL(/\/library$/);
    await page.getByRole('navigation', { name: 'Library tools' }).getByRole('link', { name: 'Manage definitions', exact: true }).click();
    await expect(page).toHaveURL(/\/library\?view=manage$/);
    await expect(page.locator('main').getByRole('heading', { name: 'Library', level: 1 })).toBeVisible();
  });
});
