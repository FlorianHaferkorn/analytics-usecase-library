import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { isAbsolute, join, resolve } from 'node:path';

// Invented tenant values, written at test time into the server's tenant directory. The
// distinctive rates and prices are asserted to be absent from the page and the response.
const STATUS = { status: 'ANNAHME, ungeprueft', herkunft: 'Testwert' };
const TENANT = { mandanten: { nagarro: {
  name: 'Testmandant', waehrung: 'EUR', rundung_eur: 50,
  marge_m: { wert: 0.25, ...STATUS }, risikozuschlag_r: { festpreis: 0.1, tm: 0, ...STATUS },
  rollen: ['architekt', 'engineer', 'tester'], standorte: ['onshore', 'nearshore'],
  satzklassen: {
    architekt_onshore: { rolle: 'architekt', standort: 'onshore', kostenband: 'B', kostensatz_eur_h: 123.45, ...STATUS },
    engineer_nearshore: { rolle: 'engineer', standort: 'nearshore', kostenband: 'C', kostensatz_eur_h: 67.89, ...STATUS },
    tester_nearshore: { rolle: 'tester', standort: 'nearshore', kostenband: 'C', kostensatz_eur_h: 54.32, ...STATUS },
  },
  verfuegbarkeit: Object.fromEntries(['architekt', 'engineer', 'tester'].map(role => [role, { koepfe: 1, fakturierbare_stunden_je_tag: 8, fakturierbare_tage_je_woche: 4, arbeitstage_je_woche: 5, arbeitswochen_je_jahr: 44 }])),
  pakete: {
    REF_LANES: { name: 'Umgebungsstrecken', sales_code: 'REF_LANES', dod_paket: null, tier: 2,
      kalkulation: { ...STATUS, mengentreiber: { umgebungen: { menge_default: 1, einheit: 'Umgebung' }, domaenen: { menge_default: 1, einheit: 'Domaene' } },
        beteiligung: { architekt: 20, engineer: 50, tester: 30 },
        aufgaben: [{ name: 'Zuschnitt', klasse: 'architekt_onshore', stunden: 8 }, { name: 'Strecke', klasse: 'engineer_nearshore', stunden_je: 4, treiber: 'umgebungen' }, { name: 'Abnahme', klasse: 'tester_nearshore', stunden_je: 3, treiber: 'umgebungen' }] },
      festpreis: { grund_eur: 4321 }, lieferzeit: { band_at: [3, 5], je_einheit_at: { umgebungen: 1 }, status: 'ANNAHME, ungeprueft' } },
    REF_SOURCES: { name: 'Quellvertraege', sales_code: 'REF_SOURCES', dod_paket: null, tier: 2,
      kalkulation: { ...STATUS, mengentreiber: { quellobjekte: { menge_default: 1, einheit: 'Objekt' } }, beteiligung: { engineer: 100 },
        aufgaben: [{ name: 'Vertrag je Objekt', klasse: 'engineer_nearshore', stunden_je: 2, treiber: 'quellobjekte' }] },
      festpreis: { grund_eur: 8765 }, lieferzeit: { band_at: [4, 6], status: 'ANNAHME, ungeprueft' } },
  },
} } };

// Opt-in: real routes, real Python engine and mirrored core, synthetic tenant. Never a tenant cloud.
test('real engine: rate-free commercial impact of the DEV / PROD alternative', async ({ page, context, baseURL }) => {
  test.skip(process.env.STUDIO_COMMERCIAL_IMPACT_E2E !== '1', 'Opt in on a development server started with STUDIO_PACKAGE_DATA_ROOT and PREIS_KANON_MANDANTEN_DIR.');
  test.setTimeout(240_000);
  const dataRoot = process.env.STUDIO_PACKAGE_DATA_ROOT, tenantDir = process.env.PREIS_KANON_MANDANTEN_DIR;
  expect(dataRoot && tenantDir, 'STUDIO_PACKAGE_DATA_ROOT and PREIS_KANON_MANDANTEN_DIR must match the running server').toBeTruthy();
  const root = isAbsolute(dataRoot!) ? dataRoot! : resolve(process.cwd(), dataRoot!);
  mkdirSync(tenantDir!, { recursive: true });
  writeFileSync(join(tenantDir!, 'preis_kanon.yaml'), JSON.stringify(TENANT, null, 2), 'utf-8');
  const errors: string[] = [], writes: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => { if (request.method() !== 'GET' && /\/api\/projects\//.test(request.url())) writes.push(request.url()); });

  await page.goto('/login?callbackUrl=%2Farchitecture');
  await page.getByRole('button', { name: 'Sign in with Demo', exact: true }).click();
  await expect(page).toHaveURL(/\/architecture/, { timeout: 60_000 });
  const created = await page.request.post('/api/project', { data: { name: 'Synthetic commercial reference' } });
  expect(created.status(), await created.text()).toBe(201);
  const body = await created.json();
  const projectId: string = (body.project ?? body.data?.project).id;
  const python = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const built = JSON.parse(execFileSync(python, [
    ...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),
    '-m', 'tooling.superversion.project_package.alternative_impact', '--schemas', join('tooling', 'generator', 'schemas'),
    '--build-reference', join(root, 'repositories', projectId), '--project-ref', projectId, '--canon',
  ], { cwd: resolve(process.cwd(), '..'), encoding: 'utf-8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }));
  const revision: string = built.value.revision_hash;

  await context.addCookies([{ name: 'studio.project', value: projectId, url: baseURL! }]);
  await page.addInitScript(([id, hash]) => { sessionStorage.setItem('studio.view.selection', JSON.stringify({ projectId: id, scope: 'project', hash })); }, [projectId, revision]);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/architecture');
  await page.getByRole('button', { name: 'Decision effects', exact: true }).click();
  await page.getByRole('button', { name: 'decision environment model → dev prod', exact: true }).click({ timeout: 60_000 });
  await expect(page.getByText('− TEST', { exact: true })).toBeVisible({ timeout: 120_000 });

  const responsePromise = page.waitForResponse(response => response.url().includes('/architecture/commercial?'), { timeout: 120_000 });
  await page.getByRole('button', { name: 'Evaluate against price canon', exact: true }).click();
  const response = await responsePromise;
  expect(response.status(), await response.text()).toBe(200);
  const raw = await response.text();
  const result = JSON.parse(raw);
  expect(result).toMatchObject({ status: 'evaluated', price_values_embedded: false, project_ref: projectId, alternative_option_ref: 'dev_prod' });
  expect(result.baseline.hours_by_canon_role).toEqual({ architekt: 8, engineer: 30, tester: 9 });
  expect(result.alternative.hours_by_canon_role).toEqual({ architekt: 8, engineer: 26, tester: 6 });

  const table = page.getByRole('table').filter({ hasText: 'Hours per canon role' });
  await expect(table.getByRole('row', { name: /tester 9 h 6 h/ })).toBeVisible();
  await expect(page.getByText('8 → 7 workdays', { exact: true })).toBeVisible();
  await expect(page.getByText(/New · canon role without plan demand/)).toBeVisible();
  await page.getByText('Proposal assumptions (rate-free)').click();
  await expect(page.getByText(/Quantity umgebungen: 2 \(derived: selected_stage_count\)/)).toBeVisible();
  await page.screenshot({ path: test.info().outputPath('commercial-impact-desktop.png'), fullPage: true });

  const pageText = await page.locator('main').innerText();
  for (const value of ['123.45', '67.89', '54.32', '4321', '8765', 'kostensatz', 'festpreis']) {
    expect(raw).not.toContain(value);
    expect(pageText).not.toContain(value);
  }
  await page.setViewportSize({ width: 768, height: 1000 });
  expect(await page.locator('main').evaluate(element => element.scrollWidth <= element.clientWidth + 1)).toBe(true);
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
