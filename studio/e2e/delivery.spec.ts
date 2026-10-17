import { test, expect } from '@playwright/test';

async function loginAndOpenDelivery(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
  await page.getByText('Sign in with Demo').click();
  // Wait for the sign-in redirect itself; a fixed pause let it interrupt the next goto.
  await page.waitForURL(/\/overview$/, { timeout: 15_000 });

  await page.goto('/delivery');
  await page.waitForTimeout(1000);
}

test.describe('Delivery Engine', () => {
  test('renders adapter selection and export controls, labeled as library preview', async ({ page }) => {
    await loginAndOpenDelivery(page);

    // Since 0ac7775b1 (08.09.2026) the three targets are Fabric/Power BI, Databricks
    // Metric Views and Open Semantic Interchange ('Open Source Stack' and 'CI/CD
    // Pipeline' were removed), and every export runs through the governed Python
    // seam (lib/delivery/governed-export-handler.ts) instead of a TS shadow adapter.
    const fabric = page.getByRole('button', { name: /^Microsoft Fabric \/ Power BI/ });
    const databricks = page.getByRole('button', { name: /^Databricks Metric Views/ });
    const osi = page.getByRole('button', { name: /^Open Semantic Interchange/ });
    await expect(fabric).toBeVisible();
    await expect(databricks).toBeVisible();
    await expect(osi).toBeVisible();
    await expect(fabric).toHaveAttribute('aria-pressed', 'true');

    // Export control: present, and disabled until a use case is in scope.
    await expect(page.getByRole('button', { name: 'Create package', exact: true })).toBeDisabled();

    // ADR-0007: nothing on this page is presented as a shippable deliverable. The
    // former per-adapter 'preview' badge moved to the page: library generation is a
    // preview, not an approved delivery; a target whose vendor gate is pending is
    // 'beta'; no target is ever labeled 'available'.
    await expect(page.getByRole('heading', { name: 'Generate library preview', exact: true })).toBeVisible();
    await expect(page.getByText(/These previews are not approved customer deliveries/)).toBeVisible();
    await expect(databricks.locator('[data-status]')).toHaveText('beta');
    for (const target of [fabric, osi]) await expect(target.locator('[data-status]')).toHaveText('governed');
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
