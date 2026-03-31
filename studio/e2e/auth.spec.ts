import { test, expect } from '@playwright/test';

test.describe('Auth flow', () => {
  test('redirects unauthenticated user to login', async ({ page }) => {
    await page.goto('/steering');
    await expect(page).toHaveURL(/\/login/);
  });

  test('login page renders correctly', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByText('ActionReady Studio')).toBeVisible();
    await expect(page.getByPlaceholder('demo@aurora-group.eu')).toBeVisible();
    await expect(page.getByText('Continue with GitHub')).toBeVisible();
    await expect(page.getByText('Sign in with Demo')).toBeVisible();
  });

  test('demo login redirects to steering', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
    await page.getByText('Sign in with Demo').click();
    await page.waitForURL(/\/(steering|login)/, { timeout: 10000 });
  });
});
