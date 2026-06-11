import { test, expect } from '@playwright/test';

test.describe('Delivery Engine', () => {
  test('renders adapter selection and export controls', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
    await page.getByText('Sign in with Demo').click();
    await page.waitForTimeout(2000);

    await page.goto('/delivery');
    await page.waitForTimeout(1000);

    // Check for adapter buttons
    await expect(page.getByRole('button', { name: 'Microsoft Fabric / Power BI' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Open Source Stack' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'CI/CD Pipeline' })).toBeVisible();

    // Check for export button
    await expect(page.getByText(/Export to/)).toBeVisible();
  });
});
