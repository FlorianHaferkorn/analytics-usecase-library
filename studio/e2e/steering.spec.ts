import { test, expect } from '@playwright/test';

test.describe('Steering Hub', () => {
  test('renders flow canvas and editor area', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
    await page.getByText('Sign in with Demo').click();
    await page.waitForTimeout(2000);

    await page.goto('/steering');
    await page.waitForTimeout(1000);

    // Check for React Flow container
    const flow = page.locator('.react-flow');
    await expect(flow).toBeVisible({ timeout: 10000 });
  });
});
