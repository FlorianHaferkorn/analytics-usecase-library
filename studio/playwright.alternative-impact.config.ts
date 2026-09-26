import { defineConfig } from '@playwright/test';
import base from './playwright.config';

// Real engine run against a synthetic reference. Never starts a server or resets a database:
// a development server started with STUDIO_PACKAGE_DATA_ROOT (a fresh temporary directory)
// and STUDIO_DB_PATH under .e2e is an explicit prerequisite.
export default defineConfig({ ...base, testMatch: 'alternative-impact.spec.ts', webServer: undefined, reporter: 'list' });
