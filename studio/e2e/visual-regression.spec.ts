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
    await expect(page).toHaveScreenshot('overview.png', { fullPage: true });
  });

  test('steering flow canvas looks stable', async ({ page }) => {
    await loginDemo(page);
    await page.goto('/steering');

    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 10_000 });
    await expect(page).toHaveScreenshot('steering.png', { fullPage: true });
  });
});

