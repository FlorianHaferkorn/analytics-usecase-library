import { defineConfig } from '@playwright/test';
import base from './playwright.config';

// Real engine and mirrored price-canon core against a synthetic tenant written by the test.
// Never starts a server or resets a database: the running server must use a fresh
// STUDIO_PACKAGE_DATA_ROOT and PREIS_KANON_MANDANTEN_DIR (temporary directories).
export default defineConfig({ ...base, testMatch: 'commercial-impact.spec.ts', webServer: undefined, reporter: 'list' });
