import { expect, test, type Page } from '@playwright/test';

// A fresh e2e database has no Project Package, so the loaded view (file list next to
// the editor) is served from a fixture here. The spec checks layout only.
const text = (value: string) => Buffer.from(value, 'utf-8').toString('base64');
const files = [
  { path: 'project.yaml', content: 'project_ref: default\nname: Aurora demo\n' },
  { path: 'modules/discovery/objectives.yaml', content: 'objectives:\n  - id: obj_margin\n    title: Protect gross margin\n' },
  { path: 'modules/plan/work_packages.yaml', content: 'work_packages: []\n' },
  { path: 'README.md', content: '# Aurora demo package\n' },
].map(({ path, content }) => ({ path, contentBase64: text(content), size: content.length, sha256: 'a'.repeat(64) }));

async function serveFixturePackage(page: Page) {
  await page.route(/\/api\/projects\/default\/package(?:\?.*)?$/, (route) => (
    route.request().method() === 'GET'
      ? route.fulfill({ json: { revision: { revision_hash: 'b'.repeat(64), package_id: 'fixture', project_ref: 'default', revision: 3, parent_revision_hash: null }, files } })
      : route.continue()
  ));
}

async function layoutOf(page: Page) {
  await page.goto('/package');
  const list = page.getByRole('button', { name: /project\.yaml/ }).first();
  const editor = page.getByRole('textbox', { name: /^Edit / });
  await expect(list).toBeVisible({ timeout: 20_000 });
  await expect(editor).toBeVisible();
  const box = async (locator: typeof list) => (await locator.boundingBox())!;
  const [listBox, editorBox] = [await box(list), await box(editor)];
  const overflow = await page.evaluate(() => {
    const main = document.querySelector('main')!;
    return { body: document.documentElement.scrollWidth - document.documentElement.clientWidth, main: main.scrollWidth - main.clientWidth };
  });
  return { listBox, editorBox, overflow };
}

test.describe('Project Package with a saved revision', () => {
  test.beforeEach(async ({ page }) => { await serveFixturePackage(page); });

  test.describe('desktop', () => {
    test.use({ viewport: { width: 1280, height: 900 } });
    test('file list sits next to the editor', async ({ page }) => {
      const { listBox, editorBox, overflow } = await layoutOf(page);
      expect(listBox.x + listBox.width).toBeLessThanOrEqual(editorBox.x + 1);
      expect(overflow.main, 'main scrolls sideways').toBeLessThanOrEqual(1);
    });
  });

  test.describe('mobile', () => {
    test.use({ viewport: { width: 360, height: 780 } });
    test('file list stacks above the editor without sideways scrolling', async ({ page }) => {
      const { listBox, editorBox, overflow } = await layoutOf(page);
      expect(overflow.body, 'page scrolls sideways').toBeLessThanOrEqual(1);
      expect(overflow.main, 'main scrolls sideways').toBeLessThanOrEqual(1);
      expect(editorBox.y).toBeGreaterThanOrEqual(listBox.y + listBox.height - 1);
    });
  });
});

test.describe('Project Package save conflicts', () => {
  const failSave = (page: Page, error: { code: string; message: string }) => page.route(/\/api\/projects\/default\/package$/, (route) => (
    route.request().method() === 'POST' ? route.fulfill({ status: 409, json: { error } }) : route.fallback()
  ));

  async function editAndSave(page: Page) {
    await page.goto('/package');
    const editor = page.getByRole('textbox', { name: /^Edit / });
    await expect(editor).toBeVisible({ timeout: 20_000 });
    await editor.fill('project_ref: default\nname: Aurora demo (edited)\n');
    await page.getByRole('button', { name: 'Save 1 change', exact: true }).click();
  }

  test('a stale revision asks to reload before applying the edits again', async ({ page }) => {
    await serveFixturePackage(page);
    await failSave(page, { code: 'STALE_REVISION', message: 'expected HEAD does not match current HEAD' });
    await editAndSave(page);
    await expect(page.getByText(/A newer version has been saved/)).toBeVisible();
  });

  test('another conflict shows the server message instead of the stale-version hint', async ({ page }) => {
    await serveFixturePackage(page);
    await failSave(page, { code: 'CONFLICT', message: 'Package path already exists in this revision.' });
    await editAndSave(page);
    await expect(page.getByText('Package path already exists in this revision.')).toBeVisible();
    await expect(page.getByText(/A newer version has been saved/)).toHaveCount(0);
  });
});
