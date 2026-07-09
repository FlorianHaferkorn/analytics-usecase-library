import { defineConfig } from '@playwright/test';
import base from './playwright.config';

// CI-only override of playwright.config.ts. Excludes the two visual-
// regression suites (visual-regression.spec.ts, design-system-optical.spec.ts)
// -- their baseline PNGs were captured on Windows (filenames end -win32) and
// would fail on every run on a Linux CI runner from font/anti-aliasing
// differences alone, not real regressions. They remain real, valid coverage
// run locally on Windows; this file only scopes what runs in CI.
export default defineConfig({
  ...base,
  testIgnore: ['**/visual-regression.spec.ts', '**/design-system-optical.spec.ts'],
});
