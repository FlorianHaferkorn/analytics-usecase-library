import { test, expect, type Page } from '@playwright/test';

async function loginAsDemo(page: Page) {
  await page.goto('/login');
  await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
  await page.getByText('Sign in with Demo').click();
  await page.waitForURL((url: URL) => !url.pathname.includes('/login'), { timeout: 15_000 });
}

test.describe('Forge walkthrough (DoD checklist)', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemo(page);
  });

  test('Discover showcase handoff opens Blueprint with draft query', async ({ page }) => {
    await page.goto('/discover');
    await expect(page.getByRole('heading', { name: 'Discover', level: 1 })).toBeVisible();
    await page.getByRole('button', { name: 'Open showcase in Blueprint' }).click();
    await expect(page).toHaveURL(/\/blueprint\?draftId=DRAFT-COM-002/);
    await expect(page.getByText('Draft scaffold loaded')).toBeVisible({ timeout: 10_000 });
  });

  test('Blueprint COM-002 syncs ROI preset to margin.gm.pct', async ({ page }) => {
    await page.goto('/blueprint');
    await page.getByRole('combobox').first().selectOption('COM-002');
    await expect(page.locator('#roi-kpi-select')).toHaveValue('margin.gm.pct', { timeout: 10_000 });

    const roiPanel = page.locator('section').filter({ has: page.locator('#roi-kpi-select') });
    await expect(roiPanel.getByText('Gross Margin %', { exact: true })).toBeVisible({ timeout: 10_000 });
    await expect(roiPanel.getByText('Baseline', { exact: true })).toBeVisible({ timeout: 10_000 });
  });

  test('Compose shows Aurora showcase banner', async ({ page }) => {
    await page.goto('/compose');
    await expect(page.getByRole('heading', { name: 'Aurora Showcase Simulation', level: 3 })).toBeVisible();
    await expect(page.getByRole('link', { name: /Continue to Generate/ })).toBeVisible();
  });

  test('Generate starts with zero selected use cases', async ({ page }) => {
    await page.goto('/generate');
    await expect(page.getByText('0 of 20 use cases selected')).toBeVisible();
    await expect(page.getByRole('link', { name: /Continue to Brand/ })).toBeVisible();
  });
});
