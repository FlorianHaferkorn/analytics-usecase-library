import { test, expect, type Page } from '@playwright/test';

async function loginAsDemo(page: Page) {
  await page.goto('/login');
  await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
  await page.getByText('Sign in with Demo').click();
  // next-auth signIn can be async and sometimes logs authjs fetch errors while the cookie/redirect settles.
  // Mimic existing E2E specs by giving the client a short stabilization window.
  await page.waitForTimeout(2000);

  // Do not silently suppress login redirect failures.
  // If this times out, the test will later fail with a clearer "wrong operation" only if needed,
  // but we at least surface the root cause here.
  const loginRedirectError: unknown = await page
    .waitForURL((url: URL) => !url.pathname.includes('/login'), { timeout: 15_000 })
    .then(() => null)
    .catch((err) => err);

  if (loginRedirectError) {
    // eslint-disable-next-line no-console
    console.warn(
      `[design-system-optical] Login redirect wait did not complete. Current URL: ${page.url()}. Error: ${
        loginRedirectError instanceof Error ? loginRedirectError.message : String(loginRedirectError)
      }`,
    );
  }
}

type TokenMismatch = { token: string; actual: string; expected: string };

test.describe('Design System — optical Premium checks', () => {
  test.use({ viewport: { width: 1280, height: 720 } });

  // Snapshot update policy:
  // - Update baselines only intentionally via:
  //   `npx playwright test e2e/design-system-optical.spec.ts --update-snapshots`
  // - CI will fail on pixel diffs and on token mismatches (Block A).

  test('Block A: DS tokens (studio/dark/airy) are correctly applied', async ({ page }) => {
    await loginAsDemo(page);
    await page.goto('/overview');

    // Anchor that the app (and CSS variable layer) is ready.
    await expect(page.getByText('KPIs', { exact: true })).toBeVisible({ timeout: 10_000 });

    const mismatches = await page.evaluate(() => {
      const ds = {
        // Variant "studio", Theme "dark"
        bg: '#0b0b0c',
        bg2: '#101012',
        panel: '#131316',
        ink: '#f4f4f2',
        ink2: '#c9c9cd',
        ink3: '#8a8a90',
        ink4: '#5a5a60',
        line: 'rgba(255,255,255,0.08)',
        line2: 'rgba(255,255,255,0.04)',
        accent: 'oklch(0.78 0.10 215)',
        accentSoft: 'oklch(0.78 0.10 215 / 0.16)',
        accentInk: 'oklch(0.12 0.04 215)',

        // Structural tokens for density "airy"
        pad: '28px',
        gap: '28px',
        hRow: '48px',

        // Radius
        radius: '10px',
      } as const;

      const root = document.documentElement;
      const dataset = root.dataset;

      const mismatches: TokenMismatch[] = [];

      const colorToRgba = (cssValue: string) => {
        const el = document.createElement('div');
        el.style.backgroundColor = cssValue;
        document.body.appendChild(el);
        const computed = getComputedStyle(el).backgroundColor;

        // Convert ANY CSS color string (rgb/lab/oklch/hex/rgba) into a comparable RGBA tuple via canvas.
        const canvas = document.createElement('canvas');
        canvas.width = 1;
        canvas.height = 1;
        const ctx = canvas.getContext('2d');
        if (!ctx) throw new Error('2d canvas ctx missing');

        ctx.clearRect(0, 0, 1, 1);
        ctx.fillStyle = computed;
        ctx.fillRect(0, 0, 1, 1);
        const data = ctx.getImageData(0, 0, 1, 1).data;
        el.remove();
        const r = data[0];
        const g = data[1];
        const b = data[2];
        const a = data[3];
        return { r, g, b, a };
      };

      const normalizeLength = (
        cssValue: string,
        property: 'padding' | 'gap' | 'height' | 'borderRadius',
      ) => {
        const el = document.createElement('div');
        if (property === 'padding') el.style.padding = cssValue;
        if (property === 'height') el.style.height = cssValue;
        if (property === 'borderRadius') el.style.borderRadius = cssValue;
        if (property === 'gap') {
          el.style.display = 'flex';
          el.style.gap = cssValue;
          // Ensure at least two children so `gap` takes effect.
          const c1 = document.createElement('div');
          const c2 = document.createElement('div');
          el.appendChild(c1);
          el.appendChild(c2);
        }
        document.body.appendChild(el);
        const computed =
          property === 'padding'
            ? getComputedStyle(el).paddingTop
            : property === 'gap'
              ? getComputedStyle(el).gap
              : property === 'height'
                ? getComputedStyle(el).height
                : getComputedStyle(el).borderTopLeftRadius;
        el.remove();
        return computed;
      };

      const expectColorVar = (token: string, expectedCss: string) => {
        const actual = colorToRgba(`var(${token})`);
        const expected = colorToRgba(expectedCss);
        const actualStr = `rgba(${actual.r},${actual.g},${actual.b},${actual.a})`;
        const expectedStr = `rgba(${expected.r},${expected.g},${expected.b},${expected.a})`;
        if (actualStr !== expectedStr) {
          mismatches.push({ token, actual: actualStr, expected: expectedStr });
        }
      };

      const expectLengthVar = (
        token: string,
        expectedCss: string,
        property: 'padding' | 'gap' | 'borderRadius',
      ) => {
        const actual = normalizeLength(`var(${token})`, property);
        const expected = normalizeLength(expectedCss, property);
        if (actual !== expected) mismatches.push({ token, actual, expected });
      };

      // Dataset assertions (theme/density/fonts)
      if (dataset.theme !== 'dark') mismatches.push({ token: 'data-theme', actual: dataset.theme ?? '', expected: 'dark' });
      if (dataset.density !== 'airy') mismatches.push({ token: 'data-density', actual: dataset.density ?? '', expected: 'airy' });
      if (dataset.fonts !== 'inter') mismatches.push({ token: 'data-fonts', actual: dataset.fonts ?? '', expected: 'inter' });

      // Color token comparisons
      expectColorVar('--bg', ds.bg);
      expectColorVar('--bg-2', ds.bg2);
      expectColorVar('--panel', ds.panel);
      expectColorVar('--ink', ds.ink);
      expectColorVar('--ink-2', ds.ink2);
      expectColorVar('--ink-3', ds.ink3);
      expectColorVar('--ink-4', ds.ink4);
      expectColorVar('--line', ds.line);
      expectColorVar('--line-2', ds.line2);
      expectColorVar('--accent', ds.accent);
      expectColorVar('--accent-soft', ds.accentSoft);
      expectColorVar('--accent-ink', ds.accentInk);

      // Layout token comparisons
      expectLengthVar('--pad', ds.pad, 'padding');
      expectLengthVar('--gap', ds.gap, 'gap');
      // `--h-row` is a legacy row-height alias. Read it reliably by applying the
      // underlying variable to a dummy element and checking computed height.
      const actualRowHeightAiry = normalizeLength('var(--row-height-airy)', 'height');
      if (actualRowHeightAiry !== ds.hRow) {
        mismatches.push({
          token: '--h-row (via --row-height-airy)',
          actual: actualRowHeightAiry,
          expected: ds.hRow,
        });
      }

      // Radius comparison
      expectLengthVar('--radius', ds.radius, 'borderRadius');

      // Inner padding / spacing: verify that a representative inner container
      // actually uses `var(--pad)` with the panel background.
      // This connects "Padding" tokens to real rendered component chrome.
      const expectedPanelRgba = colorToRgba('var(--panel)');
      const expectedPanelStr = `rgba(${expectedPanelRgba.r},${expectedPanelRgba.g},${expectedPanelRgba.b},${expectedPanelRgba.a})`;
      const expectedPadStr = ds.pad;

      const kpiLabelEls = Array.from(document.querySelectorAll('*')).filter(
        (el) => el.textContent?.trim() === 'KPIs',
      ) as HTMLElement[];

      let foundInnerPad = false;
      for (const labelEl of kpiLabelEls.slice(0, 5)) {
        let cur: HTMLElement | null = labelEl;
        for (let depth = 0; depth < 7 && cur; depth++) {
          const cs = getComputedStyle(cur);
          if (cs.paddingTop === expectedPadStr) {
            const bg = colorToRgba(cs.backgroundColor);
            const bgStr = `rgba(${bg.r},${bg.g},${bg.b},${bg.a})`;
            if (bgStr === expectedPanelStr) {
              foundInnerPad = true;
              break;
            }
          }
          cur = cur.parentElement;
        }
        if (foundInnerPad) break;
      }

      if (!foundInnerPad) {
        mismatches.push({
          token: 'innerPadding(panel chrome)',
          actual: 'not found (no element with paddingTop=var(--pad) & var(--panel) bg)',
          expected: `panel container with paddingTop=${expectedPadStr}`,
        });
      }

      // Font sanity checks: ensure the app actually uses the expected font families.
      const computedBody = getComputedStyle(document.body).fontFamily;
      if (!/inter/i.test(computedBody)) {
        mismatches.push({ token: 'fontFamily(body)', actual: computedBody, expected: 'Inter (or Inter fallback stack)' });
      }

      const monoFamilyFromVar = (() => {
        const el = document.createElement('div');
        el.style.fontFamily = 'var(--font-mono)';
        document.body.appendChild(el);
        const computed = getComputedStyle(el).fontFamily;
        el.remove();
        return computed;
      })();

      if (!/jetbrains mono/i.test(monoFamilyFromVar)) {
        mismatches.push({ token: 'fontFamily(--font-mono)', actual: monoFamilyFromVar, expected: 'JetBrains Mono' });
      }

      // Typography tokens: ensure CSS variables resolve to the intended families.
      const fontDisplayFromVar = (() => {
        const el = document.createElement('div');
        el.style.fontFamily = 'var(--font-display)';
        document.body.appendChild(el);
        const computed = getComputedStyle(el).fontFamily;
        el.remove();
        return computed;
      })();

      if (!/inter/i.test(fontDisplayFromVar)) {
        mismatches.push({ token: 'fontFamily(--font-display)', actual: fontDisplayFromVar, expected: 'Inter (or fallback stack)' });
      }

      // Typography details (computed-style based, to avoid missing tokens like --display-track).
      // Validate the main heading uses the expected tracking: StudioPageHeader sets letterSpacing: '-0.02em'.
      const h1 = document.querySelector('h1') as HTMLElement | null;
      if (h1) {
        const cs = getComputedStyle(h1);
        const fontSizePx = parseFloat(cs.fontSize || '');
        const letterSpacingPx = parseFloat(cs.letterSpacing || '');
        // Some browsers return "normal" (-> NaN). Only validate when both parse to numbers.
        if (!Number.isNaN(fontSizePx) && !Number.isNaN(letterSpacingPx)) {
          const expectedLetterSpacingPx = fontSizePx * -0.02;
          if (Math.abs(letterSpacingPx - expectedLetterSpacingPx) > 0.5) {
            mismatches.push({
              token: 'h1 letterSpacing (-0.02em)',
              actual: `${letterSpacingPx}px`,
              expected: `${expectedLetterSpacingPx}px`,
            });
          }
        }
      }

      // Ensure mono font is used by at least one real element (not just var resolution).
      const anyMonoElementUsesJetBrains = Array.from(document.querySelectorAll('*')).some((el) => {
        const cs = getComputedStyle(el);
        return /jetbrains mono/i.test(cs.fontFamily || '');
      });
      if (!anyMonoElementUsesJetBrains) {
        mismatches.push({
          token: 'some element uses JetBrains Mono',
          actual: 'not found',
          expected: 'JetBrains Mono in computed font-family',
        });
      }

      return mismatches;
    });

    // If any token deviates, fail with a concise diff.
    expect(mismatches, `Token mismatches:\n${mismatches.map((m) => `${m.token}: ${m.actual} != ${m.expected}`).join('\n')}`).toEqual([]);
  });

  test('Block B: Screenshots for premium DS look-and-feel', async ({ page }) => {
    test.setTimeout(120_000);
    await loginAsDemo(page);

    // Overview
    await page.goto('/overview');
    await expect(page.getByText('KPIs', { exact: true })).toBeVisible({ timeout: 10_000 });
    await expect(page).toHaveScreenshot('ds-overview.png', {
      fullPage: true,
      // Mask greeting header to reduce time-of-day fluctuations.
      mask: [page.locator('h1')],
      maxDiffPixelRatio: 0.02,
    });

    // Generate (legacy /delivery alias)
    await page.goto('/delivery');
    await expect(page).toHaveURL('/generate');
    await expect(page.getByRole('button', { name: 'Microsoft Fabric / Power BI' })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/Export to/)).toBeVisible({ timeout: 10_000 });
    await page.waitForTimeout(750);
    await expect(page).toHaveScreenshot('ds-delivery.png', { fullPage: true, maxDiffPixelRatio: 0.04 });

    // Blueprint steering surface
    await page.goto('/blueprint');
    await expect(page.getByText('Golden Thread Flow', { exact: true })).toBeVisible({ timeout: 30_000 });
    await expect(page).toHaveScreenshot('ds-steering.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.05,
    });

    // Templates (Brand & UX Lab alias via /brand redirect)
    await page.goto('/brand');
    await expect(page).toHaveURL(/\/templates/);
    await expect(page.getByRole('heading', { name: 'Report Templates', level: 1 })).toBeVisible({ timeout: 15_000 });
    // Theme tweaks aside hydrates client-only — mask to keep optical gate stable.
    await expect(page).toHaveScreenshot('ds-templates.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.02,
      mask: [page.locator('aside'), page.locator('h1')],
    });
  });
});

