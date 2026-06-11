import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },

  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],

  webServer: {
    command: 'node scripts/reset-studio-db.mjs && npm run dev',
    url: 'http://localhost:3000',
    // Keep tests deterministic: tenant isolation depends on a clean SQLite DB.
    reuseExistingServer: false,
    timeout: 30000,
  },
});
