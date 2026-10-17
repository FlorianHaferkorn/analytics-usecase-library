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

    // Since b1a2fee15 (23.09.2026) the sidebar follows the data scope: without a
    // pinned project it shows reusable content only ('Library' became 'Reference
    // library', 'Brand & Templates' became 'Output standards'). The delivery flow
    // (Delivery cockpit, Discover, …, Domain scope) appears only in project scope —
    // asserted in navigation.spec.ts. Blueprint and Simulate are deliberately kept
    // out of the primary sidebar (tests/lib/navigation-hierarchy.test.ts).
    const sidebar = page.locator('aside');
    await expect(sidebar.getByRole('link', { name: 'Reference library', exact: true })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Output standards', exact: true })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Plugins', exact: true })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Organizations', exact: true })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Delivery cockpit', exact: true })).toHaveCount(0);
    await expect(sidebar.getByRole('link', { name: 'Blueprint', exact: true })).toHaveCount(0);
    await expect(sidebar.getByRole('link', { name: 'Simulate', exact: true })).toHaveCount(0);
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
