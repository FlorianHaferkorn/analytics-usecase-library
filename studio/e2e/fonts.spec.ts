import { expect, test } from '@playwright/test';

// The app ships Inter and JetBrains Mono (next/font/local). If the bundle breaks,
// the stack silently falls back to Segoe UI or DejaVu, and every layout and
// overflow measurement in this suite then depends on the machine. This test
// makes that fallback visible.
test('body and mono text render in the bundled faces', async ({ page }) => {
  await page.goto('/overview');
  await expect(page.locator('main').first()).toBeVisible();

  const fonts = await page.evaluate(async () => {
    await document.fonts.ready;
    const root = getComputedStyle(document.documentElement);
    const inter = root.getPropertyValue('--font-inter-face').trim();
    const mono = root.getPropertyValue('--font-jetbrains-mono-face').trim();
    const first = (stack: string) => stack.split(',')[0].trim().replace(/["']/g, '');
    // load() resolves to the faces it found; an unknown family yields []. (check() would
    // return true for an unknown family, so it proves nothing here.)
    const facesFor = async (stack: string) => (stack === '' ? [] : document.fonts.load(`12px "${first(stack)}"`));
    const interFaces = await facesFor(inter);
    const monoFaces = await facesFor(mono);
    return {
      inter,
      mono,
      bodyFamily: getComputedStyle(document.body).fontFamily,
      bodyUsesInter: inter !== '' && first(getComputedStyle(document.body).fontFamily) === first(inter),
      interLoaded: interFaces.some((face) => face.status === 'loaded'),
      monoReady: monoFaces.some((face) => face.status === 'loaded'),
    };
  });

  expect(fonts.inter, 'next/font did not set --font-inter-face').not.toBe('');
  expect(fonts.mono, 'next/font did not set --font-jetbrains-mono-face').not.toBe('');
  expect(fonts.bodyUsesInter, `body uses ${fonts.bodyFamily}`).toBe(true);
  expect(fonts.interLoaded, 'bundled Inter was not loaded').toBe(true);
  expect(fonts.monoReady, 'bundled JetBrains Mono is not available').toBe(true);
});
