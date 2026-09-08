import { expect, test, type Page } from '@playwright/test';

async function loginAsDemo(page: Page) {
  await page.goto('/login');
  await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
  await page.getByText('Sign in with Demo').click();
  await page.waitForTimeout(2_000);
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 15_000 });
}

async function assertQualityBaseline(page: Page, path: string) {
  const consoleErrors: string[] = [];
  const failedResponses: string[] = [];

  await loginAsDemo(page);

  page.on('console', (message) => {
    if (message.type() !== 'error') return;
    const value = message.text();
    // Auth.js can abort its in-flight session request when the test immediately
    // leaves the post-login redirect. The authenticated cookie is already set;
    // target-page HTTP failures remain a hard failure below.
    if (value.includes('ClientFetchError: Failed to fetch') && value.includes('errors.authjs.dev')) return;
    consoleErrors.push(value);
  });
  page.on('response', (response) => {
    if (response.status() >= 400) failedResponses.push(`${response.status()} ${response.url()}`);
  });

  await page.goto(path);
  await expect(page.locator('main').first()).toBeVisible();
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(750);

  const layout = await page.evaluate(() => {
    const main = document.querySelector('main');
    const smallText = Array.from(main?.querySelectorAll('*') ?? []).filter((element) => {
      if (element.closest('[data-quality-preview]')) return false;
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && element.textContent?.trim() && Number.parseFloat(style.fontSize) < 11;
    }).slice(0, 12).map((element) => `${element.tagName.toLowerCase()}: ${element.textContent?.trim().slice(0, 60)} (${getComputedStyle(element).fontSize})`);
    return {
      bodyOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      mainOverflow: main ? main.scrollWidth - main.clientWidth : 0,
      smallText,
    };
  });

  const expectedPermissionResponses = failedResponses.filter((entry) =>
    (path === '/approvals' && /^403 .*\/api\/governance\/review(?:\?|$)/.test(entry))
    || (path === '/package' && /^403 .*\/api\/projects\/default\/package(?:\?|$)/.test(entry))
    || (path === '/discover' && /^403 .*\/api\/projects\/default\/discovery(?:\?|$)/.test(entry)),
  );
  const unexpectedResponses = failedResponses.filter((entry) => !expectedPermissionResponses.includes(entry));
  const relevantConsoleErrors = consoleErrors.filter((entry) =>
    !(expectedPermissionResponses.length > 0 && entry.includes('status of 403 (Forbidden)')),
  );

  expect(unexpectedResponses, `${path} loaded failed resources`).toEqual([]);
  expect(relevantConsoleErrors, `${path} emitted console errors`).toEqual([]);
  expect(layout.bodyOverflow, `${path} overflows the viewport`).toBeLessThanOrEqual(1);
  expect(layout.mainOverflow, `${path} overflows its main content area`).toBeLessThanOrEqual(1);
  expect(layout.smallText, `${path} contains unreadable text below 11px:\n${layout.smallText.join('\n')}`).toEqual([]);
  if (path === '/package' && expectedPermissionResponses.length > 0) {
    await expect(page.getByText(/^(Project access required|Sign in required|Project Package unavailable)$/)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Try again', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Save changes', exact: true })).toBeDisabled();
  }
  if (path === '/discover' && expectedPermissionResponses.length > 0) {
    await expect(page.getByText(/Project access required/)).toBeVisible();
    await expect(page.getByRole('button', {name: 'Send', exact:true})).toHaveCount(0);
  }
}

const primaryPages = [
  { name: 'overview', path: '/overview' },
  { name: 'discovery', path: '/discover' },
  { name: 'blueprint', path: '/blueprint' },
  { name: 'compose', path: '/compose' },
  { name: 'project package', path: '/package' },
  { name: 'generate', path: '/generate' },
  { name: 'approvals', path: '/approvals' },
  { name: 'lineage', path: '/lineage' },
  { name: 'drift', path: '/drift' },
  { name: 'health', path: '/health' },
  { name: 'library', path: '/library' },
  { name: 'catalog', path: '/catalog' },
  { name: 'canvas', path: '/canvas' },
  { name: 'templates', path: '/templates' },
  { name: 'plugins', path: '/plugins' },
  { name: 'organizations', path: '/organizations' },
] as const;

test.describe('Studio quality baseline', () => {
  test.setTimeout(60_000);

  for (const viewport of [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'compact', width: 1024, height: 768 },
    { name: 'narrow', width: 768, height: 900 },
  ]) {
    test.describe(viewport.name, () => {
      test.use({ viewport: { width: viewport.width, height: viewport.height } });

      for (const studioPage of primaryPages) {
        test(`${studioPage.name} is clean and responsive`, async ({ page }) => {
          await assertQualityBaseline(page, studioPage.path);
        });
      }
    });
  }

  test('Blueprint loads requested illustrative value assumptions without a hidden 404', async ({ page }) => {
    const failures: string[] = [];
    page.on('response', (response) => {
      if (response.status() >= 400) failures.push(`${response.status()} ${response.url()}`);
    });
    await loginAsDemo(page);
    await page.goto('/blueprint');
    await expect(page.locator('h3:visible').filter({ hasText: 'Golden Thread Flow' }).first()).toBeVisible({ timeout: 20_000 });
    await page.getByRole('button', { name: 'Value assumptions', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Value assumptions', exact: true })).toBeVisible();
    await expect(page.getByText('Baseline', { exact: true })).toBeVisible();
    await expect(page.getByText('Target', { exact: true })).toBeVisible();
    await page.waitForTimeout(750);
    expect(failures).toEqual([]);
  });
});
