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
    await expect(page.getByText('Forge')).toBeVisible();
    await expect(page.getByText('Registry')).toBeVisible();
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

  test('sidebar shows Registry nav when on /catalog', async ({ page }) => {
    await page.goto('/catalog');
    const nav = page.locator('nav');
    await expect(nav.getByText('Catalog')).toBeVisible();
    await expect(nav.getByText('Drift')).toBeVisible();
    await expect(nav.getByText('Approvals')).toBeVisible();
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
    await page.goto('/registry');
    await expect(page).toHaveURL('/catalog');
  });

  test('Registry mode switcher navigates to /catalog', async ({ page }) => {
    await page.goto('/discover');
    await page.getByText('Registry').first().click();
    await expect(page).toHaveURL('/catalog');
  });
});
