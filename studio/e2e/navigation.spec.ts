import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('landing page shows stats and module links', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('ALUCA Studio')).toBeVisible();
    await expect(page.getByText('KPIs', { exact: true })).toBeVisible();
  });

  test('sidebar renders all module links', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
    await page.getByText('Sign in with Demo').click();
    await page.waitForTimeout(2000);

    const sidebar = page.locator('nav').first();
    await expect(sidebar.getByText('Discover')).toBeVisible();
    await expect(sidebar.getByText('Blueprint')).toBeVisible();
    await expect(sidebar.getByText('Compose')).toBeVisible();
  });
});
