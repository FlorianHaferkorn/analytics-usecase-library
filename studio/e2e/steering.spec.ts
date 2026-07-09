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

    await page.goto('/steering');
    await page.waitForTimeout(1000);

    // The Steering page is a stats/summary dashboard (Use Cases / Drivers /
    // Action gaps), not the flow canvas — that moved to /canvas. Was
    // previously asserted here incorrectly; see the 'canvas' test below.
    await expect(page.getByText('Use Cases', { exact: true })).toBeVisible();
    await expect(page.getByText('Drivers', { exact: true })).toBeVisible();
  });

  test('canvas renders the React Flow graph', async ({ page }) => {
    await loginDemo(page);

    await page.goto('/canvas');
    await page.waitForTimeout(1000);

    const flow = page.locator('.react-flow');
    await expect(flow).toBeVisible({ timeout: 10000 });
  });
});
