import { expect, test, type Page } from '@playwright/test';

async function expectAllNodesInViewport(page: Page) {
  await expect.poll(async () => page.locator('.react-flow').evaluate(flow => {
    const viewport = flow.getBoundingClientRect();
    const nodes = [...flow.querySelectorAll('.react-flow__node')];
    return nodes.length > 0 && nodes.every(node => {
      const bounds = node.getBoundingClientRect();
      return bounds.left >= viewport.left - 2 && bounds.top >= viewport.top - 2
        && bounds.right <= viewport.right + 2 && bounds.bottom <= viewport.bottom + 2;
    });
  })).toBe(true);
}

test.describe('Golden thread behavior', () => {
  test.use({ viewport: { width: 1440, height: 900 } });
  test.beforeEach(async ({ page }) => {
    await page.goto('/blueprint');
    await expect(page.getByRole('button', { name: 'Fit', exact: true })).toBeVisible();
  });

  test('Fit uses graph bounds, filter metrics match, keyboard opens details and list keeps full text', async ({ page }) => {
    await page.getByRole('combobox', { name: 'Use case', exact: true }).selectOption('');
    await page.getByRole('button', { name: 'Fit', exact: true }).click();
    await expectAllNodesInViewport(page);
    await page.getByRole('combobox', { name: 'Use case', exact: true }).selectOption('COM-001');
    await expect(page.getByText('1 use case', { exact: true })).toBeVisible();
    await expect(page.getByText('7 drivers', { exact: true })).toBeVisible();
    await expect(page.locator('.react-flow__node')).toHaveCount(12);
    await expectAllNodesInViewport(page);
    await page.getByRole('button', { name: '100%', exact: true }).click();
    await page.getByRole('button', { name: 'Fit', exact: true }).click();
    await expectAllNodesInViewport(page);
    const node = page.getByRole('group', { name: 'KPI: Gross Margin %. Sales Performance vs Plan & LY', exact: true });
    await node.focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('complementary', { name: 'Selected element details' })).toBeVisible();
    await page.getByRole('button', { name: 'Close element details' }).click();
    await page.getByRole('button', { name: 'List · 12' }).click();
    await page.getByRole('textbox', { name: 'Find graph elements' }).fill('Recovery');
    await expect(page.getByRole('button', { name: /Sales Gap Recovery via Price & Pack Adjustment/ })).toBeVisible();
    await page.getByRole('button', { name: /Sales Gap Recovery via Price & Pack Adjustment/ }).click();
    await expect(page.getByRole('heading', { name: 'Sales Gap Recovery via Price & Pack Adjustment' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Open details' })).toHaveCount(0);
  });

  test('working graph dominates desktop and optional assumptions do not load until requested', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Value assumptions' })).toHaveCount(0);
    const bounds = await page.locator('.react-flow').boundingBox();
    expect(bounds!.height).toBeGreaterThan(450);
    expect(bounds!.y).toBeLessThan(330);
    await page.getByRole('button', { name: 'Value assumptions', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Value assumptions' })).toBeVisible();
  });

  test('narrow viewport retains usable controls, complete overview and readable list', async ({ page }) => {
    await page.setViewportSize({ width: 560, height: 920 });
    await page.getByRole('button', { name: 'Fit', exact: true }).click();
    await expectAllNodesInViewport(page);
    await page.getByRole('button', { name: /^List ·/ }).click();
    await expect(page.getByRole('textbox', { name: 'Find graph elements' })).toBeVisible();
    const firstRow = page.getByRole('button', { name: /Strategy anchor.*Profitable growth/ });
    expect(await firstRow.evaluate(button => {
      const bounds = button.getBoundingClientRect();
      return [...button.children].every(child => child.getBoundingClientRect().bottom <= bounds.bottom);
    })).toBe(true);
    expect(await page.locator('main').evaluate(main => main.scrollWidth <= main.clientWidth + 1)).toBe(true);
  });
});
