import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { defineConfig } from '@playwright/test';

/**
 * Chromium-Pfad fuer Umgebungen, die einen **vorinstallierten** Browser mitbringen,
 * dessen Build-Nummer nicht zum Playwright-Pin passt.
 *
 * Gemessen am 03.08.2026: Playwright 1.59.1 verlangt Build 1217, das Remote-Image
 * liefert 1194 unter `PLAYWRIGHT_BROWSERS_PATH` plus einen stabilen `chromium`-Symlink.
 * Ohne diesen Zweig scheitern **alle 28** Specs mit `Executable doesn't exist` — und
 * zwar bevor eine einzige Assertion laeuft. Genau das hat die frueher notierte Diagnose
 * „die Specs fallen an Assertions" erzeugt: das Bild sah nach Anwendungsdefekten aus,
 * war aber eine fehlende Binaerdatei. Mit dem Pfad bestehen alle 28.
 *
 * Reihenfolge: ein explizit gesetzter Pfad gewinnt immer. Sonst wird der Symlink nur
 * dann genommen, wenn er wirklich existiert. Die CI (`npx playwright install`) legt
 * ihn nicht an und laedt ihren passenden Build selbst — dieser Zweig feuert dort also
 * nicht, und `undefined` laesst Playwright wie bisher selbst aufloesen.
 */
function chromiumExecutable(): string | undefined {
  const explicit = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;
  if (explicit) return explicit;
  const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (!browsersPath) return undefined;
  const symlink = join(browsersPath, 'chromium');
  return existsSync(symlink) ? symlink : undefined;
}

const requestedPort = process.env.STUDIO_E2E_PORT || '3000';
if (!/^\d{4,5}$/.test(requestedPort) || Number(requestedPort) < 1024 || Number(requestedPort) > 65535) {
  throw new Error('STUDIO_E2E_PORT must be a valid non-privileged TCP port');
}

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',

  use: {
    baseURL: `http://localhost:${requestedPort}`,
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
    launchOptions: { executablePath: chromiumExecutable() },
  },

  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],

  webServer: {
    command: `node scripts/reset-studio-db.mjs && npm run dev -- -p ${requestedPort}`,
    url: `http://localhost:${requestedPort}`,
    env: {
      ...process.env,
      STUDIO_DB_PATH: join(process.cwd(), '.e2e', 'studio.db'),
    },
    // Keep tests deterministic: tenant isolation depends on a clean SQLite DB.
    reuseExistingServer: process.env.PLAYWRIGHT_REUSE_SERVER === '1',
    // 30_000 war zu knapp: der Turbopack-Kaltstart braucht auf langsamem Dateisystem
    // laenger (das Remote-Image meldet es selbst: "Slow filesystem detected"). Der
    // Timeout lief ab, bevor der Server antwortete — jeder Lauf endete mit
    // "Timed out waiting 30000ms", ohne dass ein Test lief. Ein Timeout ist eine
    // Obergrenze, keine Wartezeit: ein schneller Start wird davon nicht langsamer.
    timeout: 180_000,
  },
});
