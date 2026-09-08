import { test, expect } from '@playwright/test';

test.describe('Auth flow', () => {
  test('protects project package data without a session', async ({ request }) => {
    const response = await request.get('/api/projects/default/package');
    expect(response.status()).toBe(401);
  });

  test('login page renders correctly', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByText('ALUCA Studio')).toBeVisible();
    await expect(page.getByPlaceholder('demo@aurora-group.eu')).toBeVisible();
    await expect(page.getByText('Continue with GitHub')).toBeVisible();
    await expect(page.getByText('Sign in with Demo')).toBeVisible();
  });

  test('demo login redirects to overview', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
    await page.getByText('Sign in with Demo').click();
    await page.waitForURL(/\/overview$/, { timeout: 15000 });
  });
});
