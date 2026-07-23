import { test, expect, type Page } from '@playwright/test';

test.describe('Visual regression (screenshots)', () => {
  async function loginDemo(page: Page) {
    await page.goto('/login');
    await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
    await page.getByText('Sign in with Demo').click();
    await page.waitForURL((url: URL) => !url.pathname.includes('/login'), { timeout: 15_000 });
  }

  test('overview looks stable', async ({ page }) => {
    await loginDemo(page);
    await page.goto('/overview');
    await expect(page.getByText('KPIs', { exact: true })).toBeVisible();

    // Snapshot compare (baseline stored under __screenshots__).
    await expect(page).toHaveScreenshot('overview.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.02,
    });
  });

  test('blueprint golden thread flow looks stable', async ({ page }) => {
    await loginDemo(page);
    await page.goto('/blueprint');

    await expect(page.getByText('Golden Thread Flow', { exact: true })).toBeVisible({ timeout: 30_000 });
    await expect(page).toHaveScreenshot('blueprint-flow.png', {
      fullPage: true,
      mask: [page.locator('h1')],
      maxDiffPixelRatio: 0.05,
    });
  });
});

