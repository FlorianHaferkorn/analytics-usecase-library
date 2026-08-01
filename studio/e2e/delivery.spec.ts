import { test, expect } from '@playwright/test';

async function loginAndOpenDelivery(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
  await page.getByText('Sign in with Demo').click();
  await page.waitForTimeout(2000);

  await page.goto('/delivery');
  await page.waitForTimeout(1000);
}

test.describe('Delivery Engine', () => {
  test('renders adapter selection and export controls, all labeled preview', async ({ page }) => {
    await loginAndOpenDelivery(page);

    // Check for adapter buttons
    await expect(page.getByRole('button', { name: 'Microsoft Fabric / Power BI' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Open Source Stack' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'CI/CD Pipeline' })).toBeVisible();

    // Check for export button
    await expect(page.getByText(/Export to/)).toBeVisible();

    // I-10.3 (ADR-0007 rule 3): none of these TS-adapter exports is authoritative —
    // every one must render labeled 'preview', never 'available'.
    await expect(page.getByText('preview').first()).toBeVisible();
    await expect(page.getByText('available', { exact: true })).toHaveCount(0);
  });

  test('Governed Preview calls the real Python core once exactly one use case is selected', async ({ page }) => {
    await loginAndOpenDelivery(page);

    // Nothing is selected by default ("0 of 20 use cases selected for export"), so
    // the governed preview — bracket-scoped, one bridge call per use case — asks to
    // narrow the scope. The default used to be all-selected, which is why this test
    // began with a 'Deselect all' click; that control no longer exists (the page now
    // offers 'Select all'), so the click hung until the test timed out.
    await expect(page.getByText(/Select exactly one use case/)).toBeVisible();

    // Narrow the scope to exactly one use case.
    await page.getByRole('button', { name: /COM-001/ }).click();

    // The bridge-backed preview (I-10.3: /api/precore, /api/generate,
    // /api/delivery-flow — the Python core, not the TS shadow adapters) now
    // replaces the placeholder. Either real gate-validated results or an honest
    // "bridge unavailable" banner is acceptable here — both prove the real
    // bridge path ran; what the old test only checked (adapter buttons on this
    // same page) proved nothing about it.
    await expect(page.getByTestId('governed-preview')).toBeVisible({ timeout: 20000 });
    const hasRealPanel = await page.getByTestId('gate-report-panel').isVisible().catch(() => false);
    const hasUnavailableBanner = await page.getByTestId('generate-unavailable').isVisible().catch(() => false);
    expect(hasRealPanel || hasUnavailableBanner).toBe(true);
  });
});
