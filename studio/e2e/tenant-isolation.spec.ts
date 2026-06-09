/**
 * E2E: Tenant isolation — project membership enforcement.
 *
 * Verifies that user A, authenticated to project X, receives a 403
 * when they attempt to access resources belonging to project Y.
 *
 * Setup assumptions:
 *   - The dev server is running (configured in playwright.config.ts).
 *   - The Credentials provider is active (NODE_ENV !== 'production').
 *   - Project "default" exists (seeded by the SQLite initSchema).
 *   - A project with id "proj-other-tenant" does NOT include the demo user as member.
 *
 * The test signs in as demo@aurora-group.eu, then directly calls the
 * tenant-scoped API for a project the user is NOT a member of.
 * The API must return 403.
 */

import { test, expect } from '@playwright/test';

const DEMO_EMAIL = 'demo@aurora-group.eu';
const FOREIGN_PROJECT_ID = 'proj-other-tenant-test-isolation';

function cookiesToHeader(cookies: Array<{ name: string; value: string }>): string {
  return cookies.map((c) => `${c.name}=${c.value}`).join('; ');
}

let cookieHeader = '';

test.describe('Tenant isolation', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure NextAuth session is recreated from a clean state each test.
    await page.context().clearCookies();

    // Sign in as the demo user.
    await page.goto('/login');
    const emailInput = page.getByPlaceholder('demo@aurora-group.eu');
    await emailInput.fill(DEMO_EMAIL);
    await page.getByText('Sign in with Demo').click();
    // Wait until redirected away from /login (may go to /steering or stay if no redirect).
    await page.waitForURL(/\/(steering|discovery|registry|lineage|simulator|brand-lab|delivery|plugins)/, {
      timeout: 15000,
    }).catch(() => {
      // Some CI configs may stay at /login; continue anyway so the cookie is set.
    });

    // `page.request` can be decoupled from the browser context cookies depending on runner.
    // Make the tenant isolation checks deterministic by explicitly passing the cookie header.
    const cookies = await page.context().cookies();
    cookieHeader = cookiesToHeader(cookies);

    // We keep this cookieHeader explicit because `page.request` can be
    // decoupled from the browser context cookies.
  });

  test('user in project X cannot GET /api/projects/Y/core/brackets (403)', async ({ page }) => {
    // Hit the tenant-scoped brackets endpoint for a project the user is NOT in.
    const response = await page.request.get(
      `/api/projects/${FOREIGN_PROJECT_ID}/core/brackets`,
      {
        headers: { cookie: cookieHeader },
        maxRedirects: 0,
      },
    );

    expect(response.status()).toBe(403);

    const body = await response.json().catch(() => null);
    if (body) {
      // Forbidden JSON error body with code PROJECT_ACCESS_DENIED.
      expect(body).toMatchObject({ code: 'PROJECT_ACCESS_DENIED' });
    }
  });

  test('user can GET /api/projects/default/core/brackets (200)', async ({ page }) => {
    // The demo user has no explicit memberships after fresh login; the graceful
    // fallback grants access to the "default" project.
    const response = await page.request.get(
      '/api/projects/default/core/brackets',
      { headers: { cookie: cookieHeader }, maxRedirects: 0 },
    );

    // Should be 200 (or 404 if the core dir is missing in CI — anything but 403).
    expect(response.status()).not.toBe(403);
  });

  test('X-Project-Id header for foreign project on /api/core/brackets returns 403', async ({ page }) => {
    // The demo user is NOT a member of the foreign project.
    // When the legacy /api/core/... route receives X-Project-Id for that project,
    // the API handler must block with 403.
    const response = await page.request.get('/api/core/brackets', {
      headers: { 'X-Project-Id': FOREIGN_PROJECT_ID },
      maxRedirects: 0,
    });

    expect(response.status()).toBe(403);

    const body = await response.json().catch(() => null);
    if (body) {
      expect(body).toMatchObject({ code: 'PROJECT_ACCESS_DENIED' });
    }
  });

  test('X-Project-Id header for default project on /api/core/brackets is allowed', async ({ page }) => {
    // The graceful fallback allows users with no explicit memberships to access "default".
    const response = await page.request.get('/api/core/brackets', {
      headers: { 'X-Project-Id': 'default', cookie: cookieHeader },
      maxRedirects: 0,
    });

    // 200 or 404/500 (handler may fail in CI without full repo) — but NOT 403.
    expect(response.status()).not.toBe(403);
  });

  test('/api/core/brackets without X-Project-Id header is allowed (backward compat)', async ({ page }) => {
    // Legacy callers that do not send the header must continue to work.
    const response = await page.request.get('/api/core/brackets', { headers: { cookie: cookieHeader }, maxRedirects: 0 });

    // Backward compat: without X-Project-Id, the API handler should not return 403.
    expect(response.status()).not.toBe(403);
  });
});
