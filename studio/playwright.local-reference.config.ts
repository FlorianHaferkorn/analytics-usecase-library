import { defineConfig } from '@playwright/test';
import base from './playwright.config';

// This lab test must never start a server through the standard E2E DB reset hook.
// A running development server is an explicit prerequisite; absence fails safely.
export default defineConfig({ ...base, testMatch: 'local-reference.spec.ts', webServer: undefined });
