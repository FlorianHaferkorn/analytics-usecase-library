import { test, expect } from '@playwright/test';

// Nav labels come from studio/src/lib/navigation.ts (FORGE_NAV / REGISTRY_NAV) —
// the declared single source of truth. These specs previously asserted the labels
// of components/shell/Sidebar.tsx ('Discovery' / 'Steering' / 'Registry'), which is
// dead code imported nowhere; the shell renders components/ui/studio-sidebar.tsx.
// Assert against the SSOT labels, so a real nav change breaks these instead of a
// rename in a component that no longer ships.

test.describe('Navigation', () => {
  test('landing page redirects to overview and shows module links', async ({ page }) => {
    await page.goto('/');

    // app/page.tsx is `redirect('/overview')` — '/' never renders content of its own,
    // so the old assertions here could only ever have described the target page.
    await expect(page).toHaveURL(/\/overview$/);
    await expect(page.getByRole('main').getByText('ALUCA Studio')).toBeVisible();

    // Workspace nav is the first <nav>; Tools (Library/Canvas) is the second.
    const workspaceNav = page.getByRole('navigation').first();
    await expect(workspaceNav.getByRole('link', { name: 'Overview', exact: true })).toBeVisible();
  });

  test('sidebar renders all module links', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
    await page.getByText('Sign in with Demo').click();
    await page.waitForTimeout(2000);

    const workspaceNav = page.getByRole('navigation').first();
    for (const label of ['Overview', 'Discover', 'Blueprint', 'Compose', 'Generate']) {
      await expect(workspaceNav.getByRole('link', { name: label, exact: true })).toBeVisible();
    }

    // Forge/Registry is the mode switcher and deliberately sits OUTSIDE <nav> —
    // scoping it to the navigation landmark is what made the old assertion fail.
    await expect(page.getByRole('link', { name: 'Forge', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Registry', exact: true })).toBeVisible();
  });
});
