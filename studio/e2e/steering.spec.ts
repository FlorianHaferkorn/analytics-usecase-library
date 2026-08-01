import { test, expect } from '@playwright/test';

async function loginDemo(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
  await page.getByText('Sign in with Demo').click();
  await page.waitForTimeout(2000);
}

test.describe('Steering Hub', () => {
  test('steering renders the decision-spine dashboard', async ({ page }) => {
    await loginDemo(page);

    // /steering is now `redirect('/blueprint')` — the Steering Hub was folded into
    // Blueprint as a tab (blueprint-client.tsx embeds SteeringHubClient), so landing
    // here shows Blueprint's default tab, not the old standalone dashboard.
    await page.goto('/steering');
    await expect(page).toHaveURL(/\/blueprint$/);

    const steeringTab = page.getByRole('button', { name: 'Steering', exact: true });
    await steeringTab.click();

    // The Steering view is a stats/summary dashboard (use cases / drivers /
    // action gaps), not the flow canvas — that moved to /canvas. See the
    // 'canvas' test below.
    //
    // Embedded in Blueprint, SteeringHubClient renders the compact summary bar
    // ("20 use cases · 107 drivers · 50 action gaps") rather than the StudioMetric
    // cards labelled 'Use Cases'/'Drivers' of the old standalone page — hence
    // toContainText on <main> instead of exact-text lookups, which also keeps the
    // counts themselves out of the assertion (they track repo content).
    const main = page.getByRole('main');
    await expect(main).toContainText('use cases');
    await expect(main).toContainText('drivers');
    await expect(main).toContainText('action gaps');
  });

  test('canvas renders the React Flow graph', async ({ page }) => {
    await loginDemo(page);

    await page.goto('/canvas');
    await page.waitForTimeout(1000);

    const flow = page.locator('.react-flow');
    await expect(flow).toBeVisible({ timeout: 10000 });
  });
});
