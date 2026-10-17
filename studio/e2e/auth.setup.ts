import { test as setup, expect } from '@playwright/test';
import { DEMO_STATE } from '../playwright.config';

// Signs in once as the demo user and stores the session for every other spec.
setup('demo sign-in', async ({ page }) => {
  await page.goto('/login');
  await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
  await page.getByText('Sign in with Demo').click();
  await page.waitForURL(/\/overview$/, { timeout: 30_000 });
  await expect(page.context().cookies()).resolves.toEqual(
    expect.arrayContaining([expect.objectContaining({ name: 'authjs.session-token' })]),
  );
  await page.context().storageState({ path: DEMO_STATE });
});
