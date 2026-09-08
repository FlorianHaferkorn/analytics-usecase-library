import { test, expect } from '@playwright/test';

async function loginDemo(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
  await page.getByText('Sign in with Demo').click();
  await page.waitForURL(/\/overview$/, { timeout: 15000 });
}

test.describe('Studio v3 shell', () => {
  test('overview shows rebuild sidebar nav', async ({ page }) => {
    await loginDemo(page);
    await page.goto('/overview');

    const sidebar = page.locator('aside');
    await expect(sidebar.getByRole('link', { name: 'Overview' })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Discover' })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Blueprint' })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Library' })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Data lineage' })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Brand & Templates' })).toBeVisible();
  });

  test('settings modal opens from topbar', async ({ page }) => {
    await loginDemo(page);
    await page.goto('/overview');
    await page.getByRole('button', { name: 'Settings' }).click();
    await expect(page.getByText('Theme')).toBeVisible({ timeout: 5000 });
  });

  test('library redirects from legacy catalog', async ({ page }) => {
    await loginDemo(page);
    await page.goto('/catalog', { waitUntil: 'domcontentloaded' });
    // Legacy catalog remains the management lens of the unified Library.
    await expect(page).toHaveURL(/\/library\?view=manage/, { timeout: 15_000 });
  });
});
