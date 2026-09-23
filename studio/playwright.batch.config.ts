import { defineConfig } from '@playwright/test';
import base from './playwright.config';
// Explicit existing server only; do not invoke the standard test DB reset hook.
export default defineConfig({ ...base, testMatch: 'batch-ingestion.spec.ts', webServer: undefined, reporter: 'list', expect: { timeout: 30_000 } });
