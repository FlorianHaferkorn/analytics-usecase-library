import { expect, test } from '@playwright/test';

test('review saved evidence, preview objective and transfer exact pinned selection', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1600, height: 1000 });
  const revision = 'a'.repeat(64);
  const head = 'b'.repeat(64);
  let captured: Record<string, unknown> | undefined;
  await page.route(/\/api\/projects\/[^/]+\/discovery$/, async (route) => {
    const projectId = new URL(route.request().url()).pathname.split('/')[3];
    await route.fulfill({ json: { projectId, canEdit: true, revision, updatedAt: null, document: { schemaVersion: 1, sources: [{ id: 's1', type: 'text', name: 'Workshop', content: 'Reduce manual reconciliation.', addedAt: '2026-09-07T12:00:00Z' }], messages: [], lastResponse: '', candidates: [{ type: 'anchor', id: 'objective_1', name: 'Reduce manual reconciliation', details: 'Proposed objective', source: 'Workshop', sourceId: 's1', sourceContext: 'Reduce manual reconciliation.', evidenceStatus: 'quote-verified', status: 'draft' }] } } });
  });
  await page.route(/\/api\/projects\/[^/]+\/discovery\/transfer$/, async (route) => {
    const projectId = new URL(route.request().url()).pathname.split('/')[3];
    if (route.request().method() === 'GET') await route.fulfill({ json: { projectId, head: { revision_hash: head }, objectives: ['Understand reporting needs'], scopeStatus: 'proposed' } });
    else { captured = route.request().postDataJSON(); await route.fulfill({ json: { projectId, revision: { revision_hash: 'c'.repeat(64), project_ref: projectId }, status: 'proposed' } }); }
  });
  await page.goto('/discover');
  await page.getByRole('button', { name: 'Review for Project Package' }).click();
  await expect(page.getByText(`Reviewing Package`).first()).toBeVisible();
  await page.getByLabel('Preserve Reduce manual reconciliation').check();
  await page.getByLabel('Add as draft project objective').check();
  await expect(page.getByRole('region', { name: 'Objective change preview' })).toContainText('Understand reporting needs');
  await expect(page.getByRole('button', { name: 'Transfer reviewed selection' })).toBeDisabled();
  await page.getByRole('textbox', { name: 'Review rationale' }).fill('Reviewed the source quote and this draft objective with the workshop notes.');
  await page.getByLabel('I reviewed the sources and changes.', { exact: false }).check();
  await page.screenshot({ path: testInfo.outputPath('discovery-objective-review.png'), fullPage: true });
  await page.getByRole('button', { name: 'Transfer reviewed selection' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Transferred to a new Working revision.' })).toBeVisible();
  expect(captured).toMatchObject({ discoveryRevision: revision, expectedHeadRevisionHash: head, candidateKeys: ['anchor:objective_1'], objectiveKeys: ['anchor:objective_1'], confirmed: true });
  expect(captured).not.toHaveProperty('document');
  expect(captured).not.toHaveProperty('actor');
});
