import { test, expect, type Page } from '@playwright/test';

// Navigation groups and labels come from studio/src/lib/navigation.ts — the
// declared single source of truth. The sidebar presents one engagement workflow;
// technical Forge/Registry ownership must not leak into the primary navigation.
//
// Since b1a2fee15 (23.09.2026) the sidebar is scope-dependent (studio-sidebar.tsx):
// in the default library scope it shows only reusable content ('Reference &
// standards', 'Administration'); once a project is pinned it shows the delivery
// flow plus the project workspace and hides 'Administration'. Both states are
// asserted, including what must be absent, so a scope leak in either direction fails.

type Groups = Record<string, readonly string[]>;

const LIBRARY_GROUPS: Groups = {
  'Reference & standards': ['Reference library', 'Output standards'],
  Administration: ['Plugins', 'Organizations'],
};

const PROJECT_GROUPS: Groups = {
  'Delivery flow': ['Delivery cockpit', 'Discover', 'Decide & plan', 'Design', 'Build & release', 'Verify & operate'],
  'Project workspace': ['Project record', 'Approvals', 'Domain scope'],
  'Reference & standards': ['Reference library', 'Output standards'],
};

async function expectSidebar(page: Page, visible: Groups, other: Groups) {
  const workspaceNav = page.getByRole('navigation', { name: 'Studio workflow' });
  const visibleLabels = new Set(Object.values(visible).flat());
  for (const [group, labels] of Object.entries(visible)) {
    await expect(workspaceNav.getByText(group, { exact: true })).toBeVisible();
    for (const label of labels) {
      await expect(workspaceNav.getByRole('link', { name: label, exact: true })).toBeVisible();
    }
  }
  for (const [group, labels] of Object.entries(other)) {
    if (!(group in visible)) await expect(workspaceNav.getByText(group, { exact: true })).toHaveCount(0);
    for (const label of labels) {
      if (!visibleLabels.has(label)) await expect(workspaceNav.getByRole('link', { name: label, exact: true })).toHaveCount(0);
    }
  }
}

test.describe('Navigation', () => {
  test('landing page redirects to overview and shows module links', async ({ page }) => {
    await page.goto('/');

    // app/page.tsx is `redirect('/overview')` — '/' never renders content of its own,
    // so the old assertions here could only ever have described the target page.
    await expect(page).toHaveURL(/\/overview$/);
    await expect(page.getByRole('heading', { name: 'Choose the next useful step.' })).toBeVisible();

    // The sidebar exposes a single workflow navigation landmark. Without a pinned
    // project it offers the reusable library modules.
    const workspaceNav = page.getByRole('navigation').first();
    await expect(workspaceNav).toHaveAccessibleName('Studio workflow');
    await expect(workspaceNav.getByRole('link', { name: 'Reference library', exact: true })).toBeVisible();
    await expect(workspaceNav.getByRole('link', { name: 'Output standards', exact: true })).toBeVisible();
  });

  test('sidebar renders all module links', async ({ page }) => {
    test.setTimeout(90_000);
    await page.route('**/api/project/list', route => route.fulfill({
      json: { projects: [{ id: 'nav_fixture', name: 'Navigation fixture', strategy_anchor: '', updated_at: '' }] },
    }));
    await page.goto('/login');
    await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
    await page.getByText('Sign in with Demo').click();
    await page.waitForURL(/\/overview$/, { timeout: 60_000 });
    await expect(page.getByRole('navigation', { name: 'Studio workflow' })).toBeVisible();

    // Library scope (default after sign-in): reusable content only.
    await expectSidebar(page, LIBRARY_GROUPS, PROJECT_GROUPS);

    // Project scope: the delivery workflow replaces administration.
    await page.getByRole('button', { name: /Switch project/ }).click();
    await page.getByRole('button', { name: /Navigation fixture/ }).click();
    await expectSidebar(page, PROJECT_GROUPS, LIBRARY_GROUPS);

    await expect(page.getByRole('link', { name: 'Forge', exact: true })).toHaveCount(0);
    await expect(page.getByRole('link', { name: 'Registry', exact: true })).toHaveCount(0);
  });
});
