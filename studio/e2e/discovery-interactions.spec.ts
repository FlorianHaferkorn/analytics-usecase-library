import { expect, test } from '@playwright/test';
import { emptyDiscovery, type DiscoveryDocument } from '../src/lib/discovery/document';

test.beforeEach(async ({ page }) => {
  let saved: DiscoveryDocument = emptyDiscovery();
  let revision: string | null = null;
  await page.route(/\/api\/projects\/[^/]+\/discovery$/, async (route) => {
    const projectId = decodeURIComponent(new URL(route.request().url()).pathname.split('/')[3]);
    if (route.request().method() === 'PUT') { saved = route.request().postDataJSON().document; revision = 'a'.repeat(64); }
    await route.fulfill({ json: { projectId, canEdit: true, document: saved, revision, updatedAt: null } });
  });
  await page.goto('/discover');
  await expect(page.getByRole('button', { name: 'Paste notes', exact: true })).toBeVisible();
});

test('notes dialog traps focus, closes with Escape and restores its trigger', async ({ page }) => {
  const trigger = page.getByRole('button', { name: 'Paste notes', exact: true });
  await trigger.click();
  const dialog = page.getByRole('dialog', { name: 'Paste notes', exact: true });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('textbox', { name: 'Source text' })).toBeFocused();
  for (let index = 0; index < 7; index += 1) {
    await page.keyboard.press('Tab');
    expect(await dialog.evaluate((node) => node.contains(document.activeElement))).toBe(true);
  }
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
  await expect(trigger).toBeFocused();
  await trigger.click();
  await dialog.getByRole('textbox', { name: 'Source text' }).fill('Customer discovery evidence');
  await dialog.getByRole('button', { name: 'Add Source', exact: true }).click();
  await expect(dialog).not.toBeVisible();
  await expect(page.getByText('Pasted text (Customer discovery evidence...)')).toBeVisible();
});

test('file drop accepts YAML, rejects unsupported and empty files, and allows removing a source', async ({ page }) => {
  const files = await page.evaluateHandle(() => {
    const transfer = new DataTransfer();
    transfer.items.add(new File(['project: discovery'], 'context.yaml', { type: 'application/yaml' }));
    transfer.items.add(new File(['binary'], 'slides.pdf', { type: 'application/pdf' }));
    transfer.items.add(new File([''], 'empty.txt', { type: 'text/plain' }));
    return transfer;
  });
  await page.getByTestId('source-drop-zone').dispatchEvent('drop', { dataTransfer: files });
  await expect(page.getByText('context.yaml', { exact: true })).toBeVisible();
  await expect(page.getByTestId('source-drop-zone').getByRole('alert')).toContainText('slides.pdf: unsupported format');
  await expect(page.getByTestId('source-drop-zone').getByRole('alert')).toContainText('empty.txt: the file is empty');
  await page.getByRole('button', { name: 'Remove context.yaml' }).click();
  await expect(page.getByText('No sources loaded', { exact: true })).toBeVisible();
});

test('use-case picker reports load errors and adds the returned definition only after success', async ({ page }) => {
  let fail = true;
  await page.route('**/api/core/brackets', async (route) => {
    if (fail) {
      fail = false;
      await route.fulfill({ status: 503, json: { error: { message: 'Unavailable' } } });
    } else await route.fulfill({ json: { brackets: [{ id: 'COM-001', title: 'Sales performance', domain: 'Commercial' }] } });
  });
  await page.route('**/api/core/brackets/COM-001', (route) => route.fulfill({ json: { id: 'COM-001', yaml: 'id: COM-001\ntitle: Sales performance' } }));
  const trigger = page.getByRole('button', { name: 'Load existing use case', exact: true });
  await trigger.click();
  const dialog = page.getByRole('dialog', { name: 'Load existing use case' });
  await expect(dialog.getByRole('alert')).toHaveText('Use cases could not be loaded. Try again.');
  await dialog.getByRole('button', { name: 'Retry' }).click();
  await dialog.getByRole('button', { name: /Sales performance/ }).click();
  await expect(dialog).not.toBeVisible();
  await expect(page.getByText('Use case: COM-001 - Sales performance')).toBeVisible();
  await expect(trigger).toBeFocused();
});

test('Discovery panels align and loaded conversation uses readable type without live AI', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1600, height: 900 });
  const sizes = await page.evaluate(() => {
    const headings = Array.from(document.querySelectorAll('h3'));
    const sources = headings.find((node) => node.textContent === 'Sources')?.closest('section');
    const extracted = headings.find((node) => node.textContent === 'Extracted Elements')?.closest('section');
    const chat = document.querySelector('[data-testid="discovery-chat"]');
    return [sources, chat, extracted].map((node) => {
      const rect = node?.getBoundingClientRect();
      return rect ? { y: rect.y, height: rect.height } : null;
    });
  });
  expect(sizes.every(Boolean)).toBe(true);
  expect(Math.max(...sizes.map((item) => item!.height)) - Math.min(...sizes.map((item) => item!.height))).toBeLessThanOrEqual(1);
  expect(Math.max(...sizes.map((item) => item!.y)) - Math.min(...sizes.map((item) => item!.y))).toBeLessThanOrEqual(1);
  expect(Math.max(...sizes.map((item) => item!.y + item!.height))).toBeLessThanOrEqual(900);
  expect(Math.min(...sizes.map((item) => item!.height))).toBeGreaterThanOrEqual(540);
  await page.route('**/discovery/chat', (route) => route.fulfill({
    contentType: 'text/plain',
    body: 'Review the candidate against the registry before approving it. A governed KPI reference is required.',
  }));
  await page.route('**/api/core/discovery/review', (route) => route.fulfill({ json: { results: [] } }));
  await page.getByRole('textbox', { name: 'Discovery question' }).fill('Review my discovery candidate');
  await page.getByRole('button', { name: 'Send', exact: true }).click();
  await expect(page.getByText('Review the candidate against the registry before approving it. A governed KPI reference is required.')).toBeVisible();
  await expect(page.locator('[aria-current="step"]')).toContainText('Extract');
  await expect(page.locator('[aria-current="step"]')).not.toContainText('Govern');
  await expect(page.getByText('No candidates yet; refine your question')).toBeVisible();
  const smallText = await page.getByTestId('discovery-chat').evaluate((chat) => Array.from(chat.querySelectorAll('*'))
    .filter((node) => node.getClientRects().length && node.textContent?.trim() && parseFloat(getComputedStyle(node).fontSize) < 12)
    .map((node) => node.textContent));
  expect(smallText).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath('discovery-loaded.png'), fullPage: true });

  await page.route('**/discovery/chat', (route) => route.fulfill({
    contentType: 'text/plain', body: 'kpi_id: sales.net_sales.amount\nname: Net sales',
  }));
  await page.getByRole('textbox', { name: 'Discovery question' }).fill('Give me a structured candidate');
  await page.getByRole('button', { name: 'Send', exact: true }).click();
  await expect(page.getByText('1 draft candidate', { exact: true })).toBeVisible();
  await expect(page.locator('[aria-current="step"]')).toContainText('Govern');
});

test('saved project sources and chat candidates survive a browser reload', async ({ page }) => {
  await page.getByRole('button', { name: 'Paste notes', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Paste notes', exact: true });
  await dialog.getByRole('textbox', { name: 'Source text' }).fill('Net sales requires a governed reference.');
  await dialog.getByRole('button', { name: 'Add Source', exact: true }).click();
  await page.route('**/discovery/chat', async (route) => {
    const sourceId = route.request().postDataJSON().sources[0].id;
    await route.fulfill({ contentType: 'text/plain', body: `Source: ${sourceId}\nQuote: Net sales requires a governed reference.\nkpi_id: sales.net_sales.amount\nname: Net sales` });
  });
  await page.getByRole('textbox', { name: 'Discovery question' }).fill('Extract candidate');
  await page.getByRole('button', { name: 'Send', exact: true }).click();
  await expect(page.getByText('1 draft candidate', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Save draft', exact: true }).click();
  await expect(page.getByText('Draft saved in this project', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText('Net sales · Draft', { exact: true })).toBeVisible();
  await page.getByText('Net sales · Draft', { exact: true }).click();
  await expect(page.getByText('Exact quote found in the linked source; business meaning still needs review.')).toBeVisible();
  await expect(page.getByRole('log', { name: 'Discovery conversation' })).toContainText('Extract candidate');
  await expect(page.getByRole('button', { name: 'Save draft', exact: true })).toBeDisabled();
  const downloaded = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download draft evidence' }).click();
  const artifact = await downloaded;
  expect(artifact.suggestedFilename()).toMatch(/^discovery_.+_draft.json$/);
});
