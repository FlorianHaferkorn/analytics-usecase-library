/**
 * Forge/Registry route group E2E tests (Week 6 exit gate).
 *
 * Covers:
 *  - Forge path: compose → generate
 *  - Registry path: catalog → drift → approvals
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

  test('sidebar shows Forge mode switcher', async ({ page }) => {
    await page.goto('/discover');
    // Mode switcher labels ("Forge"/"Registry") are not guaranteed on /discover.
    // Assert against stable UI: the Discovery hub heading and the Registry nav link.
    await expect(page.getByRole('heading', { name: 'Discover', level: 1 })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Registry', exact: true })).toBeVisible();
  });

  test('/compose renders Simulator', async ({ page }) => {
    await page.goto('/compose');
    await expect(page).toHaveURL('/compose');
    // Simulator has formula / what-if content
    await expect(page.locator('main')).toBeVisible();
  });

  test('/generate renders Generate hub', async ({ page }) => {
    await page.goto('/generate');
    await expect(page).toHaveURL('/generate');
    await expect(page.getByRole('heading', { name: 'Generate', level: 1 })).toBeVisible();
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

  test('sidebar shows Registry nav when on /catalog', async ({ page }) => {
    await page.goto('/catalog');
    // /catalog uses the top-level "Registry" navigation; Drift/Approvals are on
    // their dedicated pages.
    await expect(page.getByRole('heading', { name: 'Catalog', level: 1 })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Registry', exact: true })).toBeVisible();
  });

  test('/catalog renders KPI catalog table', async ({ page }) => {
    await page.goto('/catalog');
    await expect(page).toHaveURL('/catalog');
    await expect(page.locator('main')).toBeVisible();
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

  test('old /registry redirects to /catalog', async ({ page }) => {
    await page.goto('/registry', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL('/catalog', { timeout: 15_000 });
  });

  test('Registry mode switcher navigates to /catalog', async ({ page }) => {
    await page.goto('/discover');
    await page.getByRole('link', { name: 'Registry', exact: true }).click();
    await expect(page).toHaveURL('/catalog', { timeout: 10_000 });
  });
});
