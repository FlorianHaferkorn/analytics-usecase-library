import { test, expect } from '@playwright/test';

// Navigation groups and labels come from studio/src/lib/navigation.ts — the
// declared single source of truth. The sidebar presents one engagement workflow;
// technical Forge/Registry ownership must not leak into the primary navigation.

test.describe('Navigation', () => {
  test('landing page redirects to overview and shows module links', async ({ page }) => {
    await page.goto('/');

    // app/page.tsx is `redirect('/overview')` — '/' never renders content of its own,
    // so the old assertions here could only ever have described the target page.
    await expect(page).toHaveURL(/\/overview$/);
    await expect(page.getByRole('heading', { name: 'Choose the next useful step.' })).toBeVisible();

    // The sidebar exposes a single workflow navigation landmark.
    const workspaceNav = page.getByRole('navigation').first();
    await expect(workspaceNav.getByRole('link', { name: 'Overview', exact: true })).toBeVisible();
  });

  test('sidebar renders all module links', async ({ page }) => {
    test.setTimeout(90_000);
    await page.goto('/login');
    await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
    await page.getByText('Sign in with Demo').click();
    await page.waitForURL(/\/overview$/, { timeout: 60_000 });
    await expect(page.getByRole('navigation', { name: 'Studio workflow' })).toBeVisible();

    const workspaceNav = page.getByRole('navigation', { name: 'Studio workflow' });
    for (const label of ['Overview', 'Discover', 'Blueprint', 'Simulate', 'Generate']) {
      await expect(workspaceNav.getByRole('link', { name: label, exact: true })).toBeVisible();
    }

    const sidebar = page.locator('aside').first();
    for (const group of ['Project', 'Shape', 'Deliver', 'Assure', 'Assets', 'Administration']) {
      await expect(sidebar.getByText(group, { exact: true })).toBeVisible();
    }
    await expect(page.getByRole('link', { name: 'Forge', exact: true })).toHaveCount(0);
    await expect(page.getByRole('link', { name: 'Registry', exact: true })).toHaveCount(0);
  });
});
