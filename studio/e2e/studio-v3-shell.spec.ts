import { test, expect } from '@playwright/test';

async function loginDemo(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
  await page.getByText('Sign in with Demo').click();
  await page.waitForURL(/\/(overview|login)/, { timeout: 15000 });
}

test.describe('Studio v3 shell', () => {
  test('overview shows rebuild sidebar nav', async ({ page }) => {
    await loginDemo(page);
    await page.goto('/overview');
    await expect(page.getByRole('link', { name: 'Overview' })).toBeVisible();
    // "Canvas" appears both in the top links and in the sidebar; use exact match.
    await expect(page.getByRole('link', { name: 'Canvas', exact: true })).toBeVisible();
    // "Library" appears both in the top links and in the sidebar; use exact match.
    await expect(page.getByRole('link', { name: 'Library', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Report Templates' })).toBeVisible();
  });

  test('settings modal opens from topbar', async ({ page }) => {
    await loginDemo(page);
    await page.goto('/overview');
    await page.getByRole('button', { name: 'Settings' }).click();
    await expect(page.getByText('Theme')).toBeVisible({ timeout: 5000 });
  });

  test('library redirects from legacy catalog', async ({ page }) => {
    await loginDemo(page);
    await page.goto('/catalog');
    // Redirect compatibility was removed; `/catalog` is now the canonical route.
    await expect(page).toHaveURL(/\/catalog/);
  });
});
